#!/usr/bin/env python3
"""Export a Penpot board to a local image for visual review.

    export_board.py --board 01-home --page <page>
    export_board.py --board "01 - Tokens" --format svg --out /tmp/shots

`export_shape` returns image data to the MCP client and writes no file, so this script
is the only way to look at a render. The board is resolved by name on `--page`
(default: the page currently open in the plugin).

Exit codes: 0 exported, 1 board not found, 2 environment, transport or plugin failure.
"""

from __future__ import annotations

import argparse
import base64
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from penpot_exec import McpError, call_execute_code, fail, load_url, parse_sse, payload, post  # noqa: E402

FIND_BOARD = """
const page = {page};
if (!page) throw new Error("page not found");
const shape = page.root.children.find(s => s.name === {name});
if (!shape) throw new Error("board not found");
return JSON.stringify({{ id: shape.id, name: shape.name, width: shape.width, height: shape.height }});
"""


def call_tool(url: str, name: str, arguments: dict) -> dict:
    status, headers, raw = post(
        url,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "export-board", "version": "1.0.0"},
            },
        },
    )
    if status != 200:
        raise McpError(f"initialize failed: HTTP {status}: {raw[:300]}")
    session = headers.get("mcp-session-id") or headers.get("Mcp-Session-Id")
    if not session:
        raise McpError("initialize returned no mcp-session-id")
    post(url, {"jsonrpc": "2.0", "method": "notifications/initialized"}, session_id=session)
    status, _, raw = post(
        url,
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": name, "arguments": arguments}},
        session_id=session,
    )
    if status != 200:
        raise McpError(f"tools/call failed: HTTP {status}: {raw[:300]}")
    return parse_sse(raw, 2)


def image_bytes(result: dict) -> bytes:
    content = (result.get("result") or {}).get("content") or []
    for item in content:
        if item.get("type") == "image" and item.get("data"):
            return base64.b64decode(item["data"])
        if item.get("type") == "text" and item.get("text", "").startswith("<svg"):
            return item["text"].encode()
    text = json.dumps(result)[:300]
    raise McpError(f"export returned no image data: {text}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--board", required=True, help="board name exactly as it appears in the file")
    parser.add_argument("--page", help="page that holds the board (default: the open page)")
    parser.add_argument("--format", default="png", choices=("png", "svg"))
    parser.add_argument("--out", default="design/shots", type=pathlib.Path)
    arguments = parser.parse_args()

    page = "penpot.currentPage" if arguments.page is None else (
        f"penpot.currentFile.pages.find(p => p.name === {json.dumps(arguments.page)})"
    )
    code = FIND_BOARD.format(page=page, name=json.dumps(arguments.board))

    try:
        url = load_url()
        info = payload(call_execute_code(url, code))
        result = call_tool(url, "export_shape", {"shapeId": info["id"], "format": arguments.format, "mode": "shape"})
        data = image_bytes(result)
    except McpError as exc:
        message = str(exc)
        if "board not found" in message or "page not found" in message:
            fail(message, 1)
        fail(message)
    except Exception as exc:  # noqa: BLE001 - transport errors become exit 2
        fail(f"{type(exc).__name__}: {exc}")

    arguments.out.mkdir(parents=True, exist_ok=True)
    target = arguments.out / f"{arguments.board}.{arguments.format}"
    target.write_bytes(data)
    print(f"{target}  {len(data)} bytes  ({info['width']}x{info['height']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
