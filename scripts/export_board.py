#!/usr/bin/env python3
"""Export a Penpot board to a local image for visual review.

    export_board.py --board 01-home --page <page>
    export_board.py --board "01 - Tokens" --format svg --out /tmp/shots

`export_shape` returns image data to the MCP client and writes no file, so this script
is the only way to look at a render. The board is resolved by name on `--page`
(default: the page currently open in the plugin).

A PNG comes from whichever path finishes first: the bridge, or the exporter's own
render on disk. The bridge is abandoned by the MCP server after 120 s on tall boards
while the exporter has already rendered in ~3 s, so a task timeout is not a failure —
the tool keeps polling the exporter's temp dir for up to `--wait` seconds (300 s,
past the task limit) and accepts only a PNG of exactly the board's width x height.
Nothing is written unless the dimensions match: every board is 1440 wide, so a
neighbour's render is the failure mode worth checking.

Exit codes: 0 exported, 1 board not found, 2 environment, transport or plugin failure.
"""

from __future__ import annotations

import argparse
import base64
import json
import pathlib
import struct
import subprocess
import sys
import threading
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from penpot_exec import McpError, call_execute_code, fail, load_url, parse_sse, payload, post  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
SERVICE = "penpot-exporter"
TMP = "/tmp/penpot"
WAIT_S = 300.0   # longer than the MCP task limit (120 s): the render lands in ~3 s
POLL_S = 5.0

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


def compose(*args: str) -> str:
    """One `docker compose` call in the project root; empty output when it cannot run."""
    try:
        result = subprocess.run(["docker", "compose", *args], cwd=ROOT, capture_output=True, text=True)
    except OSError:
        return ""
    return (result.stdout or "") + (result.stderr or "")


def exporter_renders() -> list[str]:
    """The exporter's finished renders, newest first.

    Its temp names carry the extension mid-name (`penpot.resource.png.<uuid>`),
    and the `.tmp.bitmap` intermediates are not the shape's own render.
    """
    out = compose("exec", "-T", SERVICE, "sh", "-c", f"ls -t {TMP} 2>/dev/null")
    return [line.strip() for line in out.splitlines()
            if ".png" in line and ".tmp." not in line]


def png_size(path: pathlib.Path) -> tuple[int, int]:
    """(width, height) from the PNG header — no image library needed."""
    head = path.read_bytes()[:24]
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        raise McpError(f"{path.name} is not a PNG")
    return struct.unpack(">II", head[16:24])


def verify_png(path: pathlib.Path, info: dict) -> pathlib.Path:
    """A render that is not exactly this board is not this board's render."""
    want = (round(info["width"]), round(info["height"]))
    got = png_size(path)
    if got != want:
        path.unlink(missing_ok=True)
        raise McpError(f"{path.name} rendered {got[0]}x{got[1]}, board {info['name']} is {want[0]}x{want[1]}")
    return path


def rescue_pass(before: set[str], target: pathlib.Path, info: dict, attempts: dict[str, int]) -> tuple[pathlib.Path, str] | None:
    """Copy a fresh exporter render that matches the board. One pass, no waiting."""
    for entry in exporter_renders():
        if entry in before or attempts.get(entry, 0) >= 2:
            continue
        attempts[entry] = attempts.get(entry, 0) + 1
        probe = target.with_name(target.stem + ".rescue.png")
        compose("cp", f"{SERVICE}:{TMP}/{entry}", str(probe))
        if not probe.is_file():
            continue
        try:
            got = png_size(probe)
        except McpError:
            probe.unlink(missing_ok=True)
            continue
        if got != (round(info["width"]), round(info["height"])):
            probe.unlink(missing_ok=True)  # a neighbouring board's render
            continue
        probe.replace(target)
        return target, entry
    return None


def export_png(url: str, info: dict, target: pathlib.Path, wait: float = WAIT_S,
               poll: float = POLL_S, provenance: list[str] | None = None) -> pathlib.Path:
    """Write this board's PNG to `target` from the bridge or the exporter's own file.

    Both paths run together and the first PNG of exactly the board's size wins. A
    bridge task timeout is only that path losing — the exporter rendered seconds
    ago and its file outlives the task. Waiting is bounded by `wait`, which is
    longer than the 120 s task limit on purpose. `provenance` collects one line
    saying which path won and after how long.
    """
    note = provenance if provenance is not None else []
    before = set(exporter_renders())
    box: dict = {}

    def fire() -> None:
        try:
            box["result"] = call_tool(url, "export_shape",
                                      {"shapeId": info["id"], "format": "png", "mode": "shape"})
        except Exception as exc:  # noqa: BLE001 - this path losing is not the export failing
            box["error"] = exc

    threading.Thread(target=fire, daemon=True).start()
    started = time.monotonic()
    bridged = None
    attempts: dict[str, int] = {}
    while True:
        result = box.get("result")
        if result is not None and bridged is None:
            try:
                data = image_bytes(result)
            except McpError as exc:
                bridged = str(exc)  # "timed out after 120 seconds": keep polling the disk
            else:
                target.write_bytes(data)
                verify_png(target, info)
                note.append(f"bridge {time.monotonic() - started:.1f}s")
                return target
        found = rescue_pass(before, target, info, attempts)
        if found is not None:
            note.append(f"exporter {found[1]} {time.monotonic() - started:.1f}s")
            return found[0]
        if time.monotonic() - started >= wait:
            cause = bridged or str(box.get("error") or "bridge still busy")
            raise McpError(f"no {round(info['width'])}x{round(info['height'])} render for "
                           f"{info['name']} within {wait:g}s ({cause})")
        time.sleep(poll)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--board", required=True, help="board name exactly as it appears in the file")
    parser.add_argument("--page", help="page that holds the board (default: the open page)")
    parser.add_argument("--format", default="png", choices=("png", "svg"))
    parser.add_argument("--out", default="design/shots", type=pathlib.Path)
    parser.add_argument("--wait", type=float, default=WAIT_S,
                        help="seconds to wait for a matching render (default %(default)s)")
    parser.add_argument("--poll", type=float, default=POLL_S,
                        help="seconds between exporter polls (default %(default)s)")
    arguments = parser.parse_args()

    page = "penpot.currentPage" if arguments.page is None else (
        f"penpot.currentFile.pages.find(p => p.name === {json.dumps(arguments.page)})"
    )
    code = FIND_BOARD.format(page=page, name=json.dumps(arguments.board))

    arguments.out.mkdir(parents=True, exist_ok=True)
    note: list[str] = []
    try:
        url = load_url()
        info = payload(call_execute_code(url, code))
        target = arguments.out / f"{arguments.board}.{arguments.format}"
        if arguments.format == "png":
            export_png(url, info, target, arguments.wait, arguments.poll, note)
        else:
            result = call_tool(url, "export_shape",
                               {"shapeId": info["id"], "format": arguments.format, "mode": "shape"})
            target.write_bytes(image_bytes(result))
    except McpError as exc:
        message = str(exc)
        if "board not found" in message or "page not found" in message:
            fail(message, 1)
        fail(message)
    except Exception as exc:  # noqa: BLE001 - transport errors become exit 2
        fail(f"{type(exc).__name__}: {exc}")

    size = png_size(target) if arguments.format == "png" else None
    dims = f"{size[0]}x{size[1]}" if size else f"{info['width']}x{info['height']}"
    print(f"{target}  {target.stat().st_size} bytes  ({dims})" + (f"  [{note[0]}]" if note else ""))
    return 0



if __name__ == "__main__":
    raise SystemExit(main())
