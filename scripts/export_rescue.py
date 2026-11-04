#!/usr/bin/env python3
"""Export a Penpot board, with exporter-disk recovery on loopback targets only.

`export_shape` returns its PNG through the plugin bridge, which the MCP server
abandons after 120 s on tall boards while the exporter itself rendered in a few
seconds and left the bitmap in its temp dir. The recovery lives in
`export_board.export_png`, which uses the bridge alone on hosted targets and both
paths on loopback targets, checking the PNG's width x height. Two same-size boards are
still indistinguishable on the disk path; the bridge path identifies the shape
by id.

    export_rescue.py --board 06-kongre --page Kongre --out design/shots

Exit codes: 0 rendered, 1 board not found, 2 environment or transport.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from export_board import FIND_BOARD, POLL_S, WAIT_S, export_png, png_size  # noqa: E402
from penpot_exec import McpError, call_execute_code, fail, load_url, payload  # noqa: E402


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--board", required=True)
    ap.add_argument("--page")
    ap.add_argument("--out", default="design/shots", type=pathlib.Path)
    ap.add_argument("--wait", type=float, default=WAIT_S)
    ap.add_argument("--poll", type=float, default=POLL_S)
    args = ap.parse_args(argv)

    page = "penpot.currentPage" if not args.page else (
        f"penpot.currentFile.pages.find(p => p.name === {json.dumps(args.page)})"
    )
    try:
        url = load_url()
        info = payload(call_execute_code(url, FIND_BOARD.format(page=page, name=json.dumps(args.board))))
        args.out.mkdir(parents=True, exist_ok=True)
        target = args.out / f"{args.board}.png"
        export_png(url, info, target, args.wait, args.poll)
    except McpError as exc:
        message = str(exc)
        fail(message, 1 if "board not found" in message or "page not found" in message else 2)
    except OSError as exc:
        fail(f"{type(exc).__name__}: {exc}")

    w, h = png_size(target)
    print(f"{target}  {target.stat().st_size} bytes ({w}x{h})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
