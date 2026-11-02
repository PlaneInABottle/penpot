#!/usr/bin/env python3
"""Slice a board render into verifiable 1:1 review tiles.

    crop_board.py --board 07-program --page Kongre --out design/ihkd/shots/07-program
    crop_board.py --png design/ihkd/shots/07-program.png --out design/ihkd/shots/07-program
    crop_board.py --png shot.png --out tiles/ --regions /tmp/lint-kongre.json
    crop_board.py --attest design/ihkd/shots/07-program/manifest.json

"Looked at it 1:1" is not evidence. This script cuts the export into
viewport-sized tiles (default 1440x900, 10% overlap) plus focused region
crops, and writes a manifest. The reviewer marks every tile and region
`reviewed: true` with a finding note; `--attest` verifies that claim and
is what the Definition of done runs — exit 1 until every tile is attested.

Image backend: PIL when importable, otherwise ImageMagick `magick`.
Reviewers read only the tile PNGs, never the full render.

Exit codes: 0 done / attested, 1 tiles unreviewed, 2 environment or transport.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from penpot_exec import McpError, call_execute_code, fail, load_url, payload  # noqa: E402
from export_board import FIND_BOARD, call_tool, image_bytes  # noqa: E402

try:
    from PIL import Image

    HAVE_PIL = True
except ImportError:  # pragma: no cover - exercised only without PIL
    HAVE_PIL = False


def tile_boxes(img_w: int, img_h: int, tile_w: int, tile_h: int, overlap: float) -> list[tuple[int, int, int, int]]:
    """Viewport boxes (x, y, w, h) covering the image; last row/col ends at the edge."""
    stride_x = max(1, round(tile_w * (1 - overlap)))
    stride_y = max(1, round(tile_h * (1 - overlap)))
    xs = list(range(0, max(img_w - tile_w, 1), stride_x))
    ys = list(range(0, max(img_h - tile_h, 1), stride_y))
    if not xs:
        xs = [0]
    if not ys:
        ys = [0]
    if xs[-1] + tile_w < img_w:
        xs.append(img_w - tile_w)
    if ys[-1] + tile_h < img_h:
        ys.append(img_h - tile_h)
    return [(x, y, min(tile_w, img_w - x), min(tile_h, img_h - y)) for y in ys for x in xs]


def pick_regions(nodes: list[dict]) -> list[dict]:
    """Smallest text, densest ink window and primary CTA from lint node geometry."""
    texts = [n for n in nodes if n.get("type") == "text" and n.get("inkW") and n.get("inkH")]
    boards = {n["id"]: n for n in nodes if n.get("type") == "board" and n.get("parentId") is None}
    out: list[dict] = []
    if texts:
        small = min(texts, key=lambda n: (n.get("fontSize") or 99, n.get("y") or 0))
        out.append({"slug": "smallest-text", "name": small["name"],
                    "x": small["inkX"], "y": small["inkY"], "w": small["inkW"], "h": small["inkH"]})
    if texts:
        xs = sorted({int(n["inkX"]) for n in texts})
        best: dict | None = None
        for gx in xs[:: max(1, len(xs) // 40)]:
            window = [n for n in texts if gx <= n["inkX"] < gx + 720]
            area = sum(n["inkW"] * (n["inkH"] or 0) for n in window)
            if best is None or area > best[1]:
                ys = sorted(n["inkY"] for n in window)
                best = ({"slug": "densest", "name": f"{len(window)} texts near x={gx}",
                         "x": gx, "y": min(ys) - 24, "w": 720, "h": 900}, area)
        if best:
            out.append(best[0])
    ctas = [n for n in texts
            if "cta" in (n.get("name") or "").lower() or "primary" in (n.get("name") or "").lower()]
    if ctas:
        cta = min(ctas, key=lambda n: n.get("y") or 0)
        out.append({"slug": "primary-action", "name": cta["name"],
                    "x": cta["inkX"], "y": cta["inkY"], "w": cta["inkW"], "h": cta["inkH"]})
    for region in out:
        region["x"] = int(max(0, region["x"] - 24))
        region["y"] = int(max(0, region["y"] - 24))
        region["w"] = int(region["w"] + 48)
        region["h"] = int(region["h"] + 48)
    out.append({"note": f"page boards: {', '.join(sorted(b['name'] for b in boards.values()))}"} if boards else {})
    return [r for r in out if "slug" in r]


class Cropper:
    """PIL first, ImageMagick fallback. Neither installed is exit 2."""

    def __init__(self, src: pathlib.Path):
        self.src = src
        if HAVE_PIL:
            self.img = Image.open(src)
            self.size = self.img.size
        else:
            out = subprocess.run(["magick", "identify", "-format", "%w %h", str(src)],
                                 capture_output=True, text=True)
            if out.returncode != 0:
                fail("no PIL and `magick identify` failed — install Pillow or ImageMagick")
            self.img = None
            self.size = tuple(int(v) for v in out.stdout.split())

    def crop(self, box: tuple[int, int, int, int], dest: pathlib.Path) -> None:
        x, y, w, h = (int(v) for v in box)
        if HAVE_PIL:
            assert self.img is not None
            self.img.crop((x, y, x + w, y + h)).save(dest)
        else:
            result = subprocess.run(
                ["magick", str(self.src), "-crop", f"{w}x{h}+{x}+{y}", "+repage", str(dest)],
                capture_output=True, text=True)
            if result.returncode != 0:
                fail(f"`magick crop` failed: {result.stderr.strip()[:200]}")


def export_source(url: str, board: str, page: str | None) -> tuple[bytes, dict]:
    find = "penpot.currentPage" if page is None else (
        f"penpot.currentFile.pages.find(p => p.name === {json.dumps(page)})")
    info = payload(call_execute_code(url, FIND_BOARD.format(page=find, name=json.dumps(board))))
    result = call_tool(url, "export_shape", {"shapeId": info["id"], "format": "png", "mode": "shape"})
    return image_bytes(result), info


def attest_manifest(path: pathlib.Path) -> int:
    """Exit 0 when every tile and region is reviewed with a note, else 1."""
    try:
        manifest = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"attest: cannot read {path}: {exc}", file=sys.stderr)
        return 2
    pending = [e.get("file", "?") for e in manifest.get("tiles", []) + manifest.get("regions", [])
               if not e.get("reviewed") or not (e.get("note") or "").strip()]
    if pending:
        print(f"attest: {len(pending)} of "
              f"{len(manifest.get('tiles', [])) + len(manifest.get('regions', []))} unreviewed:")
        for name in pending[:20]:
            print(f"  - {name}")
        return 1
    print(f"attest: {path} — all tiles and regions reviewed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--board", help="board name to export (needs the plugin bridge)")
    parser.add_argument("--page", help="page holding the board")
    parser.add_argument("--png", type=pathlib.Path, help="use this render instead of exporting")
    parser.add_argument("--out", type=pathlib.Path, help="tile directory to create")
    parser.add_argument("--tile", default="1440x900", help="viewport tile size WxH")
    parser.add_argument("--overlap", type=float, default=0.1)
    parser.add_argument("--regions", type=pathlib.Path,
                        help="lint --dump-nodes geometry for smallest-text/densest/CTA crops")
    parser.add_argument("--attest", type=pathlib.Path, help="verify a manifest and exit")
    args = parser.parse_args(argv)

    if args.attest:
        return attest_manifest(args.attest)
    if not args.out:
        fail("--out is required (or use --attest MANIFEST on its own)")
    try:
        tile_w, tile_h = (int(v) for v in args.tile.lower().split("x"))
    except ValueError:
        fail(f"--tile must be WxH, got {args.tile!r}")

    out: pathlib.Path = args.out
    out.mkdir(parents=True, exist_ok=True)
    if args.png:
        src = args.png
        board_name = args.board or args.png.stem
    elif args.board:
        try:
            url = load_url()
            data, info = export_source(url, args.board, args.page)
        except McpError as exc:
            fail(str(exc))
        except (OSError, TimeoutError) as exc:
            fail(f"{type(exc).__name__}: {exc}")
        src = out / "source.png"
        src.write_bytes(data)
        board_name = args.board
        print(f"exported {args.board} ({info['width']}x{info['height']}) -> {src}")
    else:
        fail("--board (live export) or --png (existing render) is required")

    cropper = Cropper(src)
    img_w, img_h = cropper.size
    boxes = tile_boxes(img_w, img_h, tile_w, tile_h, args.overlap)
    manifest: dict = {"board": board_name, "source": src.name,
                      "image": {"w": img_w, "h": img_h},
                      "tile": {"w": tile_w, "h": tile_h, "overlap": args.overlap},
                      "tiles": [], "regions": []}
    for i, (x, y, w, h) in enumerate(boxes, 1):
        name = f"tile-{i:02d}.png"
        cropper.crop((x, y, w, h), out / name)
        manifest["tiles"].append({"file": name, "x0": x, "y0": y, "x1": x + w, "y1": y + h,
                                  "reviewed": False, "note": ""})
    if args.regions:
        try:
            nodes = json.loads(args.regions.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"cannot read regions geometry {args.regions}: {exc}")
        nodes = nodes if isinstance(nodes, list) else []
        board_node = next((n for n in nodes
                           if n.get("type") == "board" and n.get("parentId") is None
                           and n.get("name") == board_name), None)
        scoped = nodes
        if board_node is not None:
            kids: dict[str, list[dict]] = {}
            for n in nodes:
                if n.get("parentId"):
                    kids.setdefault(n["parentId"], []).append(n)
            subtree = [board_node]
            stack = list(kids.get(board_node["id"], []))
            while stack:
                node = stack.pop()
                subtree.append(node)
                stack.extend(kids.get(node["id"], []))
            scoped = subtree
            ox, oy = board_node["x"], board_node["y"]
        else:
            ox = oy = 0
        for region in pick_regions(scoped):
            name = f"region-{region['slug']}.png"
            # pick_regions reports page-absolute geometry; tiles are board-relative
            x = max(0, min(region["x"] - ox, max(img_w - 8, 0)))
            y = max(0, min(region["y"] - oy, max(img_h - 8, 0)))
            cropper.crop((x, y, min(region["w"], img_w - x), min(region["h"], img_h - y)), out / name)
            manifest["regions"].append({"file": name, "subject": region["name"],
                                        "x": x, "y": y, "w": region["w"], "h": region["h"],
                                        "reviewed": False, "note": ""})
    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    print(f"{board_name}: {img_w}x{img_h} -> {len(boxes)} tiles"
          + (f" + {len(manifest['regions'])} regions" if manifest["regions"] else "")
          + f" in {out}")
    print(f"review each PNG, mark reviewed+note in {manifest_path}, then rerun with --attest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
