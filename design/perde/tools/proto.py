"""Compose and run one Perde prototype screen.

    python3 design/perde/tools/proto.py screen-a --run
    python3 design/perde/tools/proto.py screen-a --run --export

The screen file holds the layout; this tool only injects the block map image that
`createShapeFromSvg` cannot carry (a raster placeholder, pinned in brief §6).
"""

from __future__ import annotations

import argparse
import base64
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROJ = HERE.parent
ROOT = PROJ.parents[1]
MAP_JPEG = pathlib.Path("/tmp/n-28.jpg")


def compose(screen: str) -> pathlib.Path:
    prelude = (PROJ / "build" / "_prelude.js").read_text()
    body = (PROJ / "build" / f"{screen}.js").read_text()
    if "__SPRITES__" in body:
        sprites = (PROJ / "build" / "sprites.json").read_text()
        body = body.replace("__SPRITES__", "const SPRITES = " + sprites + ";")
    out = pathlib.Path(f"/tmp/perde-{screen}.js")
    out.write_text(prelude + "\n" + body)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("screen")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--export", action="store_true")
    ap.add_argument("--board", default=None)
    args = ap.parse_args()

    path = compose(args.screen)
    print(f"composed {path} ({path.stat().st_size // 1024} KB)")
    if not args.run:
        return 0
    code = subprocess.call([sys.executable, str(ROOT / "scripts" / "penpot_exec.py"), "--file", str(path)])
    if code != 0 or not args.export:
        return code
    name = args.board or args.screen.replace("screen-", "").upper()
    return subprocess.call([
        sys.executable, str(ROOT / "scripts" / "export_board.py"),
        "--board", name, "--page", "Page 1", "--out", str(PROJ / "shots"),
    ])


if __name__ == "__main__":
    raise SystemExit(main())
