#!/usr/bin/env python3
"""Render a Penpot board by pulling the exporter's own PNG.

`export_shape` returns the image through the plugin bridge, which the MCP server
abandons after 120 s on tall boards while the exporter renders in ~2 s and leaves
the bitmap in its temp directory. `export_board.export_png` runs both paths
together and accepts only a PNG of the board's exact size, so this tool is now a
batch loop over the project's board table — the exporter has a task limit, so a
whole-page run is retried board by board, never in bulk.

    python3 design/ihkd/tools/render.py 01-ana-sayfa --page Kurumsal --out design/ihkd/shots
    python3 design/ihkd/tools/render.py --all

Exit codes: 0 rendered, 1 board not found, 2 environment or transport.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from export_board import POLL_S, WAIT_S, export_png, png_size  # noqa: E402
from penpot_exec import McpError, call_execute_code, ensure_helpers, fail, load_url, payload  # noqa: E402

BOARDS = {
    "01-ana-sayfa": "Kurumsal",
    "02-dernek": "Kurumsal",
    "03-yonetim": "Kurumsal",
    "04-calisma-gruplari": "Kurumsal",
    "05-grup-detay": "Kurumsal",
    "06-kongre": "Kongre",
    "07-program": "Kongre",
    "08-bildiri": "Kongre",
    "09-kayit": "Kongre",
    "10-konaklama": "Kongre",
    "11-akademi": "Akademi",
    "12-kurs-detay": "Akademi",
    "13-kilavuzlar": "Akademi",
    "14-dergi": "Akademi",
    "15-haberler": "İçerik",
    "16-makale": "İçerik",
    "17-takvim": "İçerik",
    "18-uyelik": "Üyelik",
    "19-giris": "Üyelik",
    "20-panel": "Üyelik",
}

FIND = """
const p = penpot.currentFile.pages.find(x => x.name === {page});
if (!p) throw new Error("page not found");
const b = p.root.children.find(s => s.name === {board});
if (!b) throw new Error("board not found");
return JSON.stringify({{ id: b.id, name: b.name, width: b.width, height: b.height }});
"""


def render(url: str, board: str, page: str, outdir: pathlib.Path,
           wait: float = WAIT_S, poll: float = POLL_S) -> pathlib.Path:
    code = FIND.format(page=json.dumps(page), board=json.dumps(board))
    info = payload(call_execute_code(url, code))
    outdir.mkdir(parents=True, exist_ok=True)
    return export_png(url, info, outdir / f"{board}.png", wait, poll)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("boards", nargs="*")
    ap.add_argument("--page")
    ap.add_argument("--out", default="design/ihkd/shots", type=pathlib.Path)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--wait", type=float, default=WAIT_S)
    ap.add_argument("--poll", type=float, default=POLL_S)
    args = ap.parse_args(argv)

    names = list(BOARDS) if (args.all or not args.boards) else args.boards
    unknown = [n for n in names if n not in BOARDS]
    if unknown:
        fail(f"unknown board(s): {', '.join(unknown)}")

    try:
        url = load_url()
        ensure_helpers(url)
    except McpError as exc:
        fail(str(exc))

    for name in names:
        page = args.page or BOARDS[name]
        try:
            target = render(url, name, page, args.out, args.wait, args.poll)
        except McpError as exc:
            print(f"{name}: ERROR {exc}", file=sys.stderr)
            return 1
        w, h = png_size(target)
        print(f"{target}  {target.stat().st_size} bytes ({w}x{h})")
        time.sleep(1.0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
