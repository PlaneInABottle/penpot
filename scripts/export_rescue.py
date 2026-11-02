#!/usr/bin/env python3
"""Export a Penpot board by rescuing the exporter's own render.

`export_shape` returns its PNG through the plugin bridge, which times out on
large boards (the MCP task limit is ~120s while a tall-board PNG is ~1MB).
The exporter itself renders in a few seconds and leaves the bitmap in its temp
dir, so this tool fires the export, ignores the task result, and copies the
newest render out of the exporter container.

    export_rescue.py --board 06-kongre --page Kongre --out design/shots

Generic: only assumes the compose service `penpot-exporter` and its tmp dir.
Exit codes: 0 rendered, 1 board not found, 2 environment or transport.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import threading
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from penpot_exec import McpError, call_execute_code, ensure_helpers, fail, load_url, payload  # noqa: E402
from export_board import call_tool  # noqa: E402

SERVICE = "penpot-exporter"
TMP = "/tmp/penpot"


def compose(*args: str) -> str:
    result = subprocess.run(
        ["docker", "compose", *args], cwd=HERE.parent,
        capture_output=True, text=True,
    )
    return (result.stdout or "") + (result.stderr or "")


def listing() -> list[str]:
    out = compose("exec", "-T", SERVICE, "sh", "-c", f"ls -t {TMP} 2>/dev/null")
    # render artifacts are named penpot.*.png.<uuid> — the .png sits mid-name
    return [l.strip() for l in out.splitlines() if ".png" in l.strip()]


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--board", required=True)
    ap.add_argument("--page")
    ap.add_argument("--out", default="design/shots", type=pathlib.Path)
    ap.add_argument("--wait", type=float, default=45.0)
    args = ap.parse_args(argv)

    try:
        url = load_url()
        ensure_helpers(url)
    except McpError as exc:
        fail(str(exc))

    page = "penpot.currentPage" if not args.page else (
        f"penpot.currentFile.pages.find(p => p.name === {json.dumps(args.page)})"
    )
    code = (
        f"const p = {page}; if (!p) throw new Error('page not found');"
        f"const b = p.root.children.find(s => s.name === {json.dumps(args.board)});"
        "if (!b) throw new Error('board not found');"
        "return JSON.stringify({ id: b.id });"
    )
    try:
        info = payload(call_execute_code(url, code))
    except McpError as exc:
        message = str(exc)
        fail(message, 1 if "board not found" in message or "page not found" in message else 2)

    before = set(listing())

    def fire() -> None:
        try:
            call_tool(url, "export_shape", {"shapeId": info["id"], "format": "png", "mode": "shape"})
        except Exception:
            pass  # the task result is irrelevant; the file is what matters

    threading.Thread(target=fire, daemon=True).start()

    path = None
    deadline = time.time() + args.wait
    while time.time() < deadline:
        time.sleep(2.0)
        fresh = [f for f in listing() if f not in before]
        if fresh:
            path = fresh[0]
            break
    if not path:
        fail(f"no render appeared for {args.board} within {args.wait:.0f}s")

    args.out.mkdir(parents=True, exist_ok=True)
    target = args.out / f"{args.board}.png"
    compose("cp", f"{SERVICE}:{TMP}/{path}", str(target))
    if not target.is_file() or target.stat().st_size < 1000:
        fail(f"copy failed for {args.board}")
    print(f"{target}  {target.stat().st_size} bytes (rescued {path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
