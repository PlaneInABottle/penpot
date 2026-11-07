"""Rasterise the vector figurines into pixel sprites.

Each figure is rendered from `figures.json` at 512x576, reduced to a 16x18 grid with an area
filter, then snapped to its own flat palette. A one-cell cream outline is added so a sprite
still separates from a photo map. Output: `sprites.json` consumed by the Penpot screen.

    python3 design/perde/tools/pixelize.py
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess

from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
BUILD = HERE.parent / "build"
W, H = 16, 18
OUTLINE_LIGHT = "#2A2419"   # a dark cutline for pale figures
OUTLINE_DARK = "#FCF8EF"    # a cream cutline for dark figures
ALPHA_MIN = 96


def render(name: str, inner: str) -> Image.Image:
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="512" height="576" '
        f'viewBox="0 0 64 72">{inner}</svg>'
    )
    src = pathlib.Path(f"/tmp/fig-{name}.svg")
    dst = pathlib.Path(f"/tmp/fig-{name}.png")
    src.write_text(svg)
    subprocess.run(["rsvg-convert", "-w", "512", "-h", "576", "-o", str(dst), str(src)], check=True)
    return Image.open(dst).convert("RGBA").resize((W, H), Image.BOX)


def palette(inner: str) -> list[tuple[int, int, int]]:
    seen = []
    for raw in re.findall(r"#[0-9A-Fa-f]{6}", inner):
        rgb = tuple(int(raw[i:i + 2], 16) for i in (1, 3, 5))
        if rgb not in seen:
            seen.append(rgb)
    return seen


def nearest(rgb, pal):
    return min(range(len(pal)), key=lambda i: sum((rgb[k] - pal[i][k]) ** 2 for k in range(3)))


LETTERS = "abcdefghijklmnopqrstuvwxyz"


def grid(im: Image.Image, pal) -> tuple[list[str], dict[str, str]]:
    rows = []
    for y in range(H):
        line = []
        for x in range(W):
            r, g, b, a = im.getpixel((x, y))
            line.append("." if a < ALPHA_MIN else LETTERS[nearest((r, g, b), pal)])
        rows.append(line)

    # cream outline: an empty cell touching ink becomes a cutout edge
    edge = [row[:] for row in rows]
    for y in range(H):
        for x in range(W):
            if rows[y][x] != ".":
                continue
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < H and 0 <= nx < W and rows[ny][nx] not in ".,":
                    edge[y][x] = "o"
                    break
    rows = edge
    full = [r[:] for r in edge]

    # trim fully empty rows so the sprite sits on its ground line
    while rows and all(c == "." for c in rows[0]):
        rows.pop(0)
    while rows and all(c == "." for c in rows[-1]):
        rows.pop()

    # pale figures need a dark cutline or they vanish on a light map
    solid = [(y, x) for y in range(H) for x in range(W) if full[y][x] not in ".,"]
    luma = 0.0
    if solid:
        acc = 0.0
        for y, x in solid:
            r, g, b, a = im.getpixel((x, y))
            acc += (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
        luma = acc / len(solid)
    mapping = {LETTERS[i]: "#%02X%02X%02X" % c for i, c in enumerate(pal)}
    mapping["o"] = OUTLINE_LIGHT if luma > 0.62 else OUTLINE_DARK
    return ["".join(r) for r in rows], mapping


def main() -> int:
    figures = json.loads((BUILD / "figures.json").read_text())
    out = {}
    for name, inner in figures.items():
        pal = palette(inner)
        im = render(name, inner)
        rows, mapping = grid(im, pal)
        out[name] = {"rows": rows, "pal": mapping}
        print(f"{name:8} {len(rows[0])}x{len(rows)}  {len(pal)} colours")
    (BUILD / "sprites.json").write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
