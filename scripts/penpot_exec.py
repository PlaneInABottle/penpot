#!/usr/bin/env python3
"""Run a JavaScript snippet in the Penpot plugin context over the MCP server.

The browser tab with the target file must have the Penpot MCP plugin connected;
every call fails otherwise with "No Penpot instance connected for user token."

Usage:
    penpot_exec.py --file snippet.js            # run a file
    penpot_exec.py --code 'return 1 + 1;'       # run inline
    cat snippet.js | penpot_exec.py             # run stdin
    penpot_exec.py --file snippet.js --raw      # print the raw JSON-RPC result

The MCP URL (with the user token) is read from ~/.config/opencode/.penpot-mcp-url.
The token is never printed. One call waits up to 240 s (PENPOT_HTTP_TIMEOUT
overrides it); on a timeout it does NOT retry — a second call would race a task
that may still be running — and exits 2 with instructions to query live state.

Exit codes: 0 success, 2 environment, transport or plugin failure (one line on
stderr, no traceback).
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

URL_FILE = pathlib.Path.home() / ".config/opencode/.penpot-mcp-url"
MCP_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}
HELPERS_PROBE = "return JSON.stringify({ version: (storage.H && storage.H.version) || null });"
HELPERS_VERSION = re.compile(r"""version:\s*["']([^"']+)["']""")
DEFAULT_TIMEOUT_S = 240.0


class McpError(Exception):
    """Environment, transport or plugin failure — never a finding."""


class TaskTimeout(McpError):
    """The HTTP call timed out; the plugin task may still be running.

    Never retried automatically: a second call would race the first one and can
    duplicate a write. Query the live state instead (build.py does that).
    """


def http_timeout() -> float:
    """Seconds to wait for one MCP call; PENPOT_HTTP_TIMEOUT overrides the default."""
    raw = os.environ.get("PENPOT_HTTP_TIMEOUT", "")
    if not raw.strip():
        return DEFAULT_TIMEOUT_S
    try:
        value = float(raw)
    except ValueError:
        raise McpError(f"PENPOT_HTTP_TIMEOUT must be seconds, got {raw!r}") from None
    if value <= 0:
        raise McpError(f"PENPOT_HTTP_TIMEOUT must be positive, got {raw!r}")
    return value


def fail(msg: str, code: int = 2) -> None:
    """Print one line to stderr and exit with `code` (2 = environment problem)."""
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def load_url() -> str:
    if not URL_FILE.is_file():
        fail(f"missing {URL_FILE} (MCP endpoint with user token)")
    url = URL_FILE.read_text().strip()
    if not url.startswith("http"):
        fail(f"{URL_FILE} does not contain an http URL")
    return url


def post(url: str, payload: dict, session_id: str | None = None,
         timeout: float | None = None) -> tuple[int, dict, str]:
    headers = dict(MCP_HEADERS)
    if session_id:
        headers["mcp-session-id"] = session_id
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    limit = http_timeout() if timeout is None else timeout
    try:
        with urllib.request.urlopen(req, timeout=limit) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return resp.status, dict(resp.headers), raw
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers or {}), exc.read().decode("utf-8", "replace")
    except (TimeoutError, OSError) as exc:
        # urllib wraps a socket timeout in URLError on some platforms.
        if isinstance(exc, TimeoutError) or isinstance(getattr(exc, "reason", None), TimeoutError):
            raise TaskTimeout(
                f"MCP call timed out after {limit:g}s — task may still be running: "
                "wait and query the live state (no retry; PENPOT_HTTP_TIMEOUT overrides)"
            ) from exc
        raise


def parse_sse(raw: str, request_id: int | None = None) -> dict:
    """Return the JSON-RPC payload a request asks for.

    Handles a plain JSON body, `data:` with or without a space, multi-line data
    fields, notification events (no `id`) and responses for a different id.
    """
    body = raw.strip()
    if not body:
        raise McpError("empty response from the MCP server")
    if body.startswith("{"):
        return json.loads(body)

    events: list[dict] = []
    data: list[str] = []
    for line in body.splitlines() + [""]:
        if not line:
            if data:
                chunk = "\n".join(data)
                data = []
                try:
                    events.append(json.loads(chunk))
                except json.JSONDecodeError:
                    continue
            continue
        field, _, value = line.partition(":")
        if field == "data":
            data.append(value[1:] if value.startswith(" ") else value)

    responses = [e for e in events if isinstance(e, dict) and "id" in e]
    if request_id is not None:
        for response in responses:
            if response.get("id") == request_id:
                return response
        raise McpError(f"no JSON-RPC response for id {request_id}")
    if responses:
        return responses[-1]
    if events:
        return events[-1]
    raise McpError(f"no JSON payload in response: {body[:200]}")


def _content_text(result: dict) -> str:
    content = (result.get("result") or {}).get("content") or []
    if isinstance(content, dict):
        content = [content]
    parts = [
        item["text"]
        for item in (content if isinstance(content, list) else [])
        if isinstance(item, dict) and item.get("type", "text") == "text" and isinstance(item.get("text"), str)
    ]
    return "\n".join(parts)


def _raise_for_error(result: dict) -> None:
    if "error" in result:
        raise McpError(f"MCP error: {json.dumps(result['error'])[:300]}")
    res = result.get("result") or {}
    text = _content_text(result)
    if res.get("isError") or "Tool execution failed" in text:
        raise McpError(f"plugin error: {text.strip()[:400] or 'tool execution failed'}")


def payload(result: dict):
    """Unwrap a tools/call result: object, JSON string, or double-encoded JSON.

    Tolerant: empty content returns None and non-JSON text is returned as that
    text, so callers never see a raw IndexError or JSONDecodeError. JSON-RPC
    errors and plugin failures raise McpError instead.
    """
    if not isinstance(result, dict):
        raise McpError(f"unexpected result type {type(result).__name__}")
    _raise_for_error(result)
    text = _content_text(result).strip()
    if not text:
        return None
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return text

    for _ in range(3):  # the plugin wraps a returned string once more
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return value
        elif isinstance(value, dict) and "result" in value and set(value) <= {"result", "log"}:
            value = value["result"]
        else:
            return value
    return value


def call_execute_code(url: str, code: str) -> dict:
    status, headers, raw = post(
        url,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "penpot-exec", "version": "1.1.0"},
            },
        },
    )
    if status != 200:
        raise McpError(f"initialize failed: HTTP {status}: {raw[:300]}")
    session = headers.get("mcp-session-id") or headers.get("Mcp-Session-Id")
    if not session:
        raise McpError("initialize returned no mcp-session-id")

    post(
        url,
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        session_id=session,
    )
    status, _, raw = post(
        url,
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "execute_code", "arguments": {"code": code}},
        },
        session_id=session,
    )
    if status != 200:
        raise McpError(f"tools/call failed: HTTP {status}: {raw[:300]}")
    result = parse_sse(raw, 2)
    _raise_for_error(result)
    return result


def ensure_helpers(url: str, helpers: pathlib.Path | None = None) -> str:
    """Load storage.H and keep it in step with the helpers.js on disk.

    Compares the `version` declared in helpers.js with `storage.H.version` and
    re-injects on mismatch, so an edited helper does not need a plugin restart.
    Returns the loaded version.
    """
    path = pathlib.Path(helpers) if helpers else pathlib.Path(__file__).resolve().parent / "helpers.js"
    source = path.read_text()
    match = HELPERS_VERSION.search(source)
    if not match:
        raise McpError(f"{path} declares no version")
    wanted = match.group(1)

    probe = payload(call_execute_code(url, HELPERS_PROBE))
    loaded = probe.get("version") if isinstance(probe, dict) else None
    if loaded == wanted:
        return loaded

    returned = payload(call_execute_code(url, source))
    loaded = returned.get("loaded") if isinstance(returned, dict) else None
    if loaded != wanted:
        raise McpError(f"helpers.js loaded version {loaded!r}, expected {wanted!r}")
    print(f"re-injected helpers.js v{loaded}", file=sys.stderr)
    return loaded


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--file", type=pathlib.Path)
    src.add_argument("--code")
    ap.add_argument("--raw", action="store_true", help="print the raw JSON-RPC result")
    args = ap.parse_args(argv)

    try:
        if args.file is not None:
            code = args.file.read_text()
        elif args.code is not None:
            code = args.code
        elif not sys.stdin.isatty():
            code = sys.stdin.read()
        else:
            ap.error("provide --file, --code or stdin")
        if not code.strip():
            ap.error("empty snippet: --file, --code and stdin must contain code")

        result = call_execute_code(load_url(), code)
    except McpError as exc:
        fail(str(exc))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        fail(f"{type(exc).__name__}: {exc}")

    if args.raw:
        print(json.dumps(result, indent=2))
    else:
        text = _content_text(result)
        if text:
            print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
