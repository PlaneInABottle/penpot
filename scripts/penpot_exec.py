#!/usr/bin/env python3
"""Run a JavaScript snippet in the Penpot plugin context over the MCP server.

The browser tab with the target file must have the Penpot MCP plugin connected;
every call fails otherwise with "No Penpot instance connected for user token."

Usage:
    penpot_exec.py --file snippet.js            # run a file (writer by default)
    penpot_exec.py --code 'return 1 + 1;'       # run inline
    cat snippet.js | penpot_exec.py             # run stdin
    penpot_exec.py --file snippet.js --raw      # print the raw JSON-RPC result
    penpot_exec.py --expect-page Üyelik --file 13.js   # refuse a drifted page
    penpot_exec.py --read --code 'return JSON.stringify(storage.H.version);'

The MCP URL (with the user token) is read from ~/.config/opencode/.penpot-mcp-url.
The token is never printed. One call waits up to 240 s (PENPOT_HTTP_TIMEOUT
overrides it); on a timeout it does NOT retry — a second call would race a task
that may still be running — and exits 2 with instructions to query live state.

One plugin, one writer. The server accepts a single plugin connection per user
token, `penpot.currentPage` is global to it, and it does not serialise tasks, so
every MCP call takes a `flock` keyed by host and a short hash of the token
(~/.cache/penpot-mcp/plugin-<host>-<hash8>.lock). A writing script also holds a
session lock (<...>.session.lock) for its whole run: other writers wait for it
(PENPOT_SESSION_WAIT, 900 s), read-only callers announce "build in progress" and
pass (PENPOT_WAIT_BUILD=1 makes them wait). Two files because flock is per open
file description: a second level on the same file would deadlock its own holder.
Waiting is bounded (PENPOT_LOCK_WAIT, 300 s); on expiry the call exits 2 with
"plugin busy: held by pid=… t=…". `--expect-page` guards the page inside the
task and verifies it again after it.

`--read` is the caller's declaration that the snippet only reads: it takes the
per-call lock but passes a running build session instead of waiting up to 900 s.
The CLI itself never probes or injects helpers, so a snippet that needs
`storage.H` fails on its own. Read-only library callers use
`ensure_helpers(..., write=False)`, which probes and then refuses to inject on a
missing/mismatched version. This is intent, not sandbox enforcement: the CLI
cannot prove a snippet does not write.

Exit codes: 0 success, 2 environment, transport or plugin failure (one line on
stderr, no traceback).
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import pathlib
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

URL_FILE = pathlib.Path.home() / ".config/opencode/.penpot-mcp-url"
MCP_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}
HELPERS_PROBE = "return JSON.stringify({ version: (storage.H && storage.H.version) || null });"
HELPERS_VERSION = re.compile(r"""version:\s*["']([^"']+)["']""")
DEFAULT_TIMEOUT_S = 240.0
LOCK_DIR = pathlib.Path.home() / ".cache" / "penpot-mcp"
LOCK_WAIT_S = 300.0      # past PENPOT_HTTP_TIMEOUT: a waiter outlasts one running call
SESSION_WAIT_S = 900.0   # a writer waits out a whole build, then gives up
LOCK_POLL_S = 0.05
PAGE_GUARD = """
{
  const want = __PAGE__;
  const now = penpot.currentPage && penpot.currentPage.name;
  if (now !== want) throw new Error("page-affinity: currentPage is " + now + ", expected " + want);
}
"""
PAGE_READ = "return JSON.stringify({ page: (penpot.currentPage && penpot.currentPage.name) || null });"


class McpError(Exception):
    """Environment, transport or plugin failure — never a finding."""


class TaskTimeout(McpError):
    """The HTTP call timed out; the plugin task may still be running.

    Never retried automatically: a second call would race the first one and can
    duplicate a write. Query the live state instead (build.py does that).
    """


class PluginBusy(McpError):
    """Another process owns the plugin (or its build session) past the wait bound.

    Also raised when `--expect-page` finds `currentPage` on a different page
    after its task, because such a write cannot be attributed any more.
    """


def _wait_env(name: str, default: float) -> float:
    raw = os.environ.get(name, "")
    if not raw.strip():
        return default
    try:
        value = float(raw)
    except ValueError:
        raise McpError(f"{name} must be seconds, got {raw!r}") from None
    if value < 0:
        raise McpError(f"{name} must not be negative, got {raw!r}")
    return value


def lock_wait() -> float:
    return _wait_env("PENPOT_LOCK_WAIT", LOCK_WAIT_S)


def session_wait() -> float:
    return _wait_env("PENPOT_SESSION_WAIT", SESSION_WAIT_S)


def token_tag(url: str) -> str:
    """A short, non-reversible tag for the endpoint's user token.

    The token is part of the URL; hashing the whole URL keys one lock per token
    without ever writing the token to a path, a log or a message.
    """
    return hashlib.sha256(url.encode()).hexdigest()[:8]


def lock_paths(url: str) -> tuple[pathlib.Path, pathlib.Path]:
    """(per-call lock, writer-session lock) for this endpoint's token."""
    host = (urllib.parse.urlparse(url).hostname or "local").replace(":", "_")
    base = pathlib.Path(os.environ.get("PENPOT_LOCK_DIR") or LOCK_DIR) / f"plugin-{host}-{token_tag(url)}"
    return base.with_suffix(".lock"), base.with_suffix(".session.lock")


# (lock path, thread) -> [fd, depth]; re-entrant per thread, never across threads.
_HELD: dict[tuple[str, int], list[int]] = {}


def _holder_text(path: pathlib.Path) -> str:
    """The holder's own line as `pid=123 t=17s`; a lock file never carries the token."""
    try:
        raw = path.read_text().strip()
    except OSError:
        return "pid=? t=?"
    pid, _, stamp = raw.partition(" ")
    if not stamp.startswith("since="):
        return f"{pid or 'pid=?'} t=?"
    try:
        age = time.time() - float(stamp[6:])
    except ValueError:
        return f"{pid or 'pid=?'} t=?"
    return f"{pid or 'pid=?'} t={age:.0f}s"


def _write_holder(fd: int) -> None:
    os.ftruncate(fd, 0)
    os.pwrite(fd, f"pid={os.getpid()} since={time.time():.0f}\n".encode(), 0)


def _acquire(path: pathlib.Path, wait: float, what: str) -> None:
    """Take an exclusive flock, or raise PluginBusy after `wait` seconds."""
    key = (str(path), threading.get_ident())
    state = _HELD.get(key)
    if state is not None:  # re-entrant inside one thread: the fd is already locked
        state[1] += 1
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    deadline = time.monotonic() + wait
    announced = False
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                holder = _holder_text(path)
                os.close(fd)
                raise PluginBusy(
                    f"plugin busy: held by {holder} — {what} lock {path.name} not free "
                    f"after {wait:g}s (PENPOT_LOCK_WAIT / PENPOT_SESSION_WAIT, seconds)")
            if not announced:
                print(f"waiting: plugin busy: held by {_holder_text(path)} ({what})",
                      file=sys.stderr)
                announced = True
            time.sleep(LOCK_POLL_S)
    _write_holder(fd)
    _HELD[key] = [fd, 1]


def _release(path: pathlib.Path) -> None:
    key = (str(path), threading.get_ident())
    state = _HELD.get(key)
    if state is None:
        return
    state[1] -= 1
    if state[1] > 0:
        return
    del _HELD[key]
    fd = state[0]
    try:
        os.ftruncate(fd, 0)
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _held_elsewhere(path: pathlib.Path) -> bool:
    """True when another process (or another thread here) holds `path`."""
    if any(key[0] == str(path) for key in _HELD):
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDONLY, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return True
    else:
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    finally:
        os.close(fd)


def plugin_session_blocker(url: str) -> str:
    """The writer session's holder as `pid=… t=…`, or '' when the plugin is free."""
    _, session_lock = lock_paths(url)
    return _holder_text(session_lock) if _held_elsewhere(session_lock) else ""


def acquire_session(url: str, wait: float | None = None) -> None:
    """Hold the writer session: other writers wait, read-only callers pass."""
    _, session_lock = lock_paths(url)
    _acquire(session_lock, session_wait() if wait is None else wait, "build session")


def release_session(url: str) -> None:
    _, session_lock = lock_paths(url)
    _release(session_lock)


@contextlib.contextmanager
def plugin_lock(url: str, *, write: bool = True, wait: float | None = None):
    """One MCP exchange at a time on the one plugin connection.

    A writer also waits for (and then holds) the session lock, so a second
    writer cannot move `currentPage` between two of its calls. A reader keeps
    its call under the per-call lock but passes a running session with a
    warning: it addresses a page by name and never moves `currentPage`, so a
    build cannot corrupt the geometry it reads. PENPOT_WAIT_BUILD=1 makes the
    reader wait instead.
    """
    call_lock, session_lock = lock_paths(url)
    call_wait = lock_wait() if wait is None else wait
    if not write and os.environ.get("PENPOT_WAIT_BUILD", "").strip().lower() in ("1", "true", "yes"):
        write = True
    # A child writer (build.py -> media.py) inherits the session its parent holds;
    # asking for it again would wait for the parent that is waiting for the child.
    inherited = os.environ.get("PENPOT_SESSION_HELD", "").strip().lower() in ("1", "true", "yes")
    session_held = False
    if not inherited:
        if write:
            _acquire(session_lock, session_wait() if wait is None else wait, "build session")
            session_held = True
        elif _held_elsewhere(session_lock):
            print(f"build in progress: held by {_holder_text(session_lock)} — reading by page "
                  "name; PENPOT_WAIT_BUILD=1 waits for it", file=sys.stderr)
    try:
        _acquire(call_lock, call_wait, "plugin")
        try:
            yield
        finally:
            _release(call_lock)
    finally:
        if session_held:
            _release(session_lock)


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


def _execute(url: str, code: str) -> dict:
    """One execute_code exchange; the caller holds the plugin lock."""
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


def current_page(url: str) -> str | None:
    """The plugin's `currentPage` name — the one global write target."""
    with plugin_lock(url, write=False):
        state = payload(_execute(url, PAGE_READ))
    return state.get("page") if isinstance(state, dict) else None


def call_execute_code(url: str, code: str, *, write: bool = True,
                      expect_page: str | None = None) -> dict:
    """Run `code` under the plugin lock, optionally pinned to `expect_page`.

    `expect_page` guards inside the task (a page that is already wrong never
    runs the snippet) and is verified again afterwards: if another session moved
    `currentPage` while the task ran, the write cannot be attributed to the
    page, so this raises instead of returning a result nobody can trust.
    """
    if expect_page:
        code = PAGE_GUARD.replace("__PAGE__", json.dumps(expect_page)) + code
    with plugin_lock(url, write=write):
        result = _execute(url, code)
    if expect_page:
        found = current_page(url)
        if found != expect_page:
            raise PluginBusy(
                f"another session changed the page: currentPage is {found!r}, "
                f"expected {expect_page!r} — the task above cannot be attributed to a page")
    return result


def ensure_helpers(url: str, helpers: pathlib.Path | None = None, *, write: bool = True) -> str:
    """Load storage.H and keep it in step with the helpers.js on disk.

    Compares the `version` declared in helpers.js with `storage.H.version` and
    re-injects on mismatch, so an edited helper does not need a plugin restart.
    Probe and injection share one lock hold: a writer must not move the page
    between them, and the pair is fast. Returns the loaded version.
    """
    path = pathlib.Path(helpers) if helpers else pathlib.Path(__file__).resolve().parent / "helpers.js"
    source = path.read_text()
    match = HELPERS_VERSION.search(source)
    if not match:
        raise McpError(f"{path} declares no version")
    wanted = match.group(1)

    with plugin_lock(url, write=write):
        probe = payload(call_execute_code(url, HELPERS_PROBE, write=write))
        loaded = probe.get("version") if isinstance(probe, dict) else None
        if loaded == wanted:
            return loaded
        if not write:
            raise McpError(
                f"helpers.js v{wanted} required but the plugin holds {loaded!r}; "
                "refusing to inject during a read — run a writer once "
                "(penpot_exec.py without --read, tokens_sync.py or build.py)")

        returned = payload(call_execute_code(url, source, write=write))
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
    ap.add_argument("--read", action="store_true",
                    help="caller intent: read-only. Passes a running build session instead of "
                         "waiting (PENPOT_WAIT_BUILD=1 waits) and never injects helpers. "
                         "Not a sandbox: the snippet is not inspected")
    ap.add_argument("--expect-page", metavar="NAME",
                    help="refuse to run, or to trust the result, when penpot.currentPage "
                         "is not NAME (exit 2: another session changed the page)")
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

        result = call_execute_code(load_url(), code, write=not args.read,
                                   expect_page=args.expect_page)
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
