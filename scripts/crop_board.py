#!/usr/bin/env python3
"""Slice a board render into verifiable 1:1 review tiles.

    crop_board.py --board 07-program --page Kongre --out design/ihkd/shots/07-program
    crop_board.py --png design/ihkd/shots/07-program.png --out design/ihkd/shots/07-program
    crop_board.py --png shot.png --out tiles/ --regions /tmp/lint-kongre.nodes.json
    crop_board.py --png shot.png --out tiles/ --primary-action 'hero cta'
    crop_board.py --png shot.png --out tiles/ --region '{"slug":"icons-arrows","name":"icon row","x":120,"y":900,"w":240,"h":40}'
    crop_board.py --attest design/ihkd/shots/07-program/manifest.json

"Looked at it 1:1" is not evidence. This script cuts the export into
viewport-sized tiles (default 1440x900, 10% overlap) plus focused region
crops, and writes a manifest. The reviewer marks every tile and region
`reviewed: true` with a finding note; `--attest` verifies that claim and
is what the Definition of done runs — exit 1 until every tile is attested.

Regions come from three sources, merged by slug (explicit wins):

1. `--regions NODES.json` (repeatable): a `design_lint.py --dump-nodes`
   list (not `--json`, which is findings, not geometry). Auto cuts the
   smallest text, the densest text window, the primary action and an
   icon/arrow row when one exists.
2. `--primary-action NAME`: overrides the heuristic CTA pick, e.g. a nav
   ghost that sits above the hero button.
3. `--region JSON` (repeatable): one declared region, exactly
   `{"slug": "...", "name": "...", "x": 0, "y": 0, "w": 0, "h": 0}`, with
   page-absolute coordinates and positive w/h. Reuse the slug to replace an
   auto region; a declared region survives a rerun.

A rerun keeps declared/manual regions and re-crops them. If the source image
changed (sha256), every `reviewed`/`note` resets because the pixels are new;
same source keeps attestations. Generated `tile-NN.png`/`region-*.png` files
that the new run no longer writes are removed; other files in the output
directory are never touched. `--attest` fails when a manifest references a
PNG that is not on disk.

Image backend: PIL when importable, otherwise ImageMagick `magick`.
Reviewers read only the tile PNGs, never the full render.

Exit codes: 0 done / attested, 1 unreviewed or missing tile/region, 2 input,
environment or transport.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
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


ICON_ARROW = re.compile(r"\b(icon|arrow|chevron)\b", re.IGNORECASE)
GENERATED = re.compile(r"^(tile-\d+\.png|region-[A-Za-z0-9._-]+\.png)$")
SLUG = re.compile(r"^[A-Za-z0-9._-]+$")


def _padded(region: dict) -> dict:
    region = dict(region)
    region["x"] = int(max(0, (region["x"] or 0) - 24))
    region["y"] = int(max(0, (region["y"] or 0) - 24))
    region["w"] = int((region["w"] or 0) + 48)
    region["h"] = int((region["h"] or 0) + 48)
    return region


def _ink_region(node: dict) -> dict | None:
    if not (node.get("inkW") and node.get("inkH")):
        return None
    return {"name": node["name"], "x": node["inkX"], "y": node["inkY"],
            "w": node["inkW"], "h": node["inkH"]}


def pick_regions(nodes: list[dict], primary_action: str | None = None) -> list[dict]:
    """Smallest text, densest ink window, primary action and icon/arrow row.

    The CTA heuristic ignores a nav/menu ghost; `primary_action` names the real
    control and always wins. Regions the board does not have are omitted, never
    invented.
    """
    texts = [n for n in nodes if n.get("type") == "text" and n.get("inkW") and n.get("inkH")]
    out: list[dict] = []
    if texts:
        small = min(texts, key=lambda n: (n.get("fontSize") or 99, n.get("y") or 0))
        out.append({"slug": "smallest-text", **_ink_region(small)})
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

    if primary_action:
        hit = next((n for n in nodes if n.get("name") == primary_action
                    and (n.get("inkW") or n.get("w"))), None)
        if hit is None:
            raise ValueError(f"--primary-action {primary_action!r} is not a node in the geometry")
        region = _ink_region(hit) or {"name": hit["name"], "x": hit["x"], "y": hit["y"],
                                      "w": hit["w"], "h": hit["h"]}
        out = [r for r in out if r["slug"] != "primary-action"]
        out.append({"slug": "primary-action", **region})
    else:
        ctas = [n for n in texts
                if any(k in (n.get("name") or "").lower() for k in ("cta", "primary"))
                and not any(k in (n.get("name") or "").lower() for k in ("nav", "menu", "header"))]
        if ctas:
            cta = min(ctas, key=lambda n: n.get("y") or 0)
            out.append({"slug": "primary-action", **_ink_region(cta)})

    icons = [n for n in nodes if ICON_ARROW.search(n.get("name") or "") and _ink_region(n)]
    if icons:
        x0 = min(n["inkX"] for n in icons)
        y0 = min(n["inkY"] for n in icons)
        x1 = max(n["inkX"] + n["inkW"] for n in icons)
        y1 = max(n["inkY"] + n["inkH"] for n in icons)
        out.append({"slug": "icons-arrows", "name": f"{len(icons)} icon/arrow shape(s)",
                    "x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0})

    return [_padded(region) for region in out]


def parse_region(raw: str) -> dict:
    """One `--region` JSON object; exact fields are documented in the module docstring."""
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--region is not JSON: {exc}") from exc
    if not isinstance(spec, dict):
        raise ValueError("--region must be a JSON object")
    slug = spec.get("slug")
    if not isinstance(slug, str) or not SLUG.match(slug):
        raise ValueError("--region needs a non-empty slug of letters, digits, '.', '_' or '-'")
    values = {}
    for key in ("x", "y", "w", "h"):
        value = spec.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"--region {slug!r}: {key} must be a number")
        values[key] = value
    if values["w"] <= 0 or values["h"] <= 0:
        raise ValueError(f"--region {slug!r}: w and h must be positive")
    name = spec.get("name")
    return {"slug": slug, "name": name if isinstance(name, str) and name else slug, **values}


def source_hash(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    info = payload(call_execute_code(url, FIND_BOARD.format(page=find, name=json.dumps(board)), write=False))
    result = call_tool(url, "export_shape", {"shapeId": info["id"], "format": "png", "mode": "shape"})
    return image_bytes(result), info


def attest_manifest(path: pathlib.Path) -> int:
    """Exit 0 when every referenced PNG exists and is reviewed with a note, else 1."""
    try:
        manifest = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"attest: cannot read {path}: {exc}", file=sys.stderr)
        return 2
    entries = list(manifest.get("tiles", [])) + list(manifest.get("regions", []))
    missing = [e.get("file", "?") for e in entries
               if not (path.parent / str(e.get("file", ""))).is_file()]
    pending = [e.get("file", "?") for e in entries
               if not e.get("reviewed") or not (e.get("note") or "").strip()]
    coverage = manifest.get("coverage") or {}
    present = {str(e.get("file", "")).removeprefix("region-").removesuffix(".png")
               for e in manifest.get("regions", [])}
    absent_regions = [slug for slug in coverage.get("required", []) if slug not in present]
    if missing:
        print(f"attest: {len(missing)} referenced PNG(s) missing from {path.parent}:")
        for name in missing[:20]:
            print(f"  - {name}")
    if absent_regions:
        print(f"attest: required region(s) not produced: {', '.join(absent_regions)} — "
              "declare them with --region after inspecting the board")
    if pending:
        print(f"attest: {len(pending)} of {len(entries)} unreviewed:")
        for name in pending[:20]:
            print(f"  - {name}")
    if missing or pending or absent_regions:
        return 1
    print(f"attest: {path} — all tiles and regions reviewed")
    return 0


def load_nodes(paths: list[pathlib.Path]) -> list[dict]:
    """Geometry from one or more `design_lint.py --dump-nodes` files."""
    nodes: list[dict] = []
    for path in paths:
        try:
            doc = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"cannot read regions geometry {path}: {exc}")
        if isinstance(doc, dict) and "findings" in doc:
            fail(f"{path} is a lint --json findings file; use design_lint.py --dump-nodes")
        if not isinstance(doc, list):
            fail(f"{path}: expected a node list from design_lint.py --dump-nodes")
        nodes.extend(doc)
    return nodes


def cleanup_stale(out: pathlib.Path, old: dict, keep: set[str], current_source: str) -> list[str]:
    """Remove previously generated PNGs this run no longer writes; never other files."""
    removed: list[str] = []
    for entry in list(old.get("tiles", [])) + list(old.get("regions", [])):
        name = str(entry.get("file", ""))
        if name and name not in keep and GENERATED.match(name):
            path = out / name
            if path.is_file():
                path.unlink()
                removed.append(name)
    if old.get("source") == "source.png" and current_source != "source.png":
        path = out / "source.png"
        if path.is_file():
            path.unlink()
            removed.append("source.png")
    return removed


def same_geometry(previous: dict, current: dict, keys: tuple[str, ...]) -> bool:
    return all(previous.get(key) == current[key] for key in keys)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--board", help="board name to export (needs the plugin bridge)")
    parser.add_argument("--page", help="page holding the board")
    parser.add_argument("--png", type=pathlib.Path, help="use this render instead of exporting")
    parser.add_argument("--out", type=pathlib.Path, help="tile directory to create")
    parser.add_argument("--tile", default="1440x900", help="viewport tile size WxH")
    parser.add_argument("--overlap", type=float, default=0.1)
    parser.add_argument("--regions", type=pathlib.Path, action="append", default=[],
                        help="design_lint.py --dump-nodes geometry; repeatable")
    parser.add_argument("--region", action="append", default=[], metavar="JSON",
                        help="declared region object (see the module docstring); repeatable")
    parser.add_argument("--primary-action", metavar="NAME",
                        help="shape name of the real primary action; overrides the CTA heuristic")
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

    manifest_path = out / "manifest.json"
    old: dict = {}
    if manifest_path.is_file():
        try:
            old = json.loads(manifest_path.read_text())
        except (OSError, json.JSONDecodeError):
            old = {}
    old_entries = {str(e.get("file")): e for e in
                   list(old.get("tiles", [])) + list(old.get("regions", []))}
    old_regions = {str(e.get("file")): e for e in old.get("regions", [])}
    digest = source_hash(src)
    same_source = old.get("source_sha256") == digest

    def keep_review(entry: dict, geometry: dict, keys: tuple[str, ...]) -> dict:
        if (same_source and same_geometry(entry, geometry, keys)
                and entry.get("reviewed") and (entry.get("note") or "").strip()):
            return {"reviewed": True, "note": entry["note"]}
        return {"reviewed": False, "note": ""}

    cropper = Cropper(src)
    img_w, img_h = cropper.size
    boxes = tile_boxes(img_w, img_h, tile_w, tile_h, args.overlap)
    manifest: dict = {"board": board_name, "source": src.name, "source_sha256": digest,
                      "image": {"w": img_w, "h": img_h},
                      "tile": {"w": tile_w, "h": tile_h, "overlap": args.overlap},
                      "tiles": [], "regions": []}
    for i, (x, y, w, h) in enumerate(boxes, 1):
        name = f"tile-{i:02d}.png"
        cropper.crop((x, y, w, h), out / name)
        geometry = {"file": name, "x0": x, "y0": y, "x1": x + w, "y1": y + h}
        manifest["tiles"].append({**geometry,
                                  **keep_review(old_entries.get(name, {}), geometry,
                                                ("x0", "y0", "x1", "y1"))})

    regions: dict[str, dict] = {}
    if args.regions:
        nodes = load_nodes(args.regions)
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
        try:
            picked = pick_regions(scoped, args.primary_action)
        except ValueError as exc:
            fail(str(exc), 1)
        for region in picked:
            # auto regions report page-absolute geometry; tiles are board-relative
            x = max(0, min(region["x"] - ox, max(img_w - 8, 0)))
            y = max(0, min(region["y"] - oy, max(img_h - 8, 0)))
            regions[region["slug"]] = {"name": region["name"], "x": x, "y": y,
                                       "w": region["w"], "h": region["h"], "origin": "auto"}
    for raw in args.region:
        try:
            region = parse_region(raw)
        except ValueError as exc:
            fail(str(exc))
        x = max(0, min(region["x"], max(img_w - 8, 0)))
        y = max(0, min(region["y"], max(img_h - 8, 0)))
        regions[region["slug"]] = {"name": region["name"], "x": x, "y": y,
                                   "w": region["w"], "h": region["h"], "origin": "declared"}
    for old_region in old.get("regions", []):
        if old_region.get("origin") not in (None, "manual", "declared"):
            continue
        slug = str(old_region.get("file", "")).removeprefix("region-").removesuffix(".png")
        if slug and slug not in regions:
            origin = "declared" if old_region.get("origin") == "declared" else "manual"
            regions[slug] = {"name": old_region.get("subject", slug), "x": old_region.get("x", 0),
                             "y": old_region.get("y", 0), "w": old_region.get("w", 0),
                             "h": old_region.get("h", 0), "origin": origin}

    for slug, region in regions.items():
        name = f"region-{slug}.png"
        w = min(region["w"], img_w - region["x"]) if region["x"] < img_w else 0
        h = min(region["h"], img_h - region["y"]) if region["y"] < img_h else 0
        if w > 0 and h > 0:
            cropper.crop((region["x"], region["y"], w, h), out / name)
        else:
            fail(f"region {slug!r} falls outside the {img_w}x{img_h} render")
        geometry = {"file": name, "x": region["x"], "y": region["y"],
                    "w": region["w"], "h": region["h"], "origin": region["origin"]}
        manifest["regions"].append({"file": name, "subject": region["name"],
                                    "x": region["x"], "y": region["y"], "w": region["w"],
                                    "h": region["h"], "origin": region["origin"],
                                    **keep_review(old_regions.get(name, {}), geometry,
                                                  ("x", "y", "w", "h"))})

    required = ["smallest-text", "densest", "primary-action"]
    if "icons-arrows" in regions:
        required.append("icons-arrows")
    present = [r["file"].removeprefix("region-").removesuffix(".png") for r in manifest["regions"]]
    manifest["coverage"] = {"required": required, "present": present,
                            "missing": [slug for slug in required if slug not in present]}
    manifest_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    keep = {e["file"] for e in manifest["tiles"] + manifest["regions"]}
    removed = cleanup_stale(out, old, keep, src.name)

    print(f"{board_name}: {img_w}x{img_h} -> {len(boxes)} tiles"
          + (f" + {len(manifest['regions'])} regions" if manifest["regions"] else "")
          + f" in {out}")
    if present:
        print(f"regions: {len(present)} ({', '.join(present)})"
              + ("" if "icons-arrows" in present else "; no icon/arrow row detected"))
    if manifest["coverage"]["missing"]:
        print(f"missing required regions: {', '.join(manifest['coverage']['missing'])} — "
              "declare one with --region if the board has that subject")
    if removed:
        print(f"removed stale generated PNG(s): {', '.join(removed)}")
    print(f"review each PNG, mark reviewed+note in {manifest_path}, then rerun with --attest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
