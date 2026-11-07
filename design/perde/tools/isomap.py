"""Procedural isometric city used by the Perde exploration boards.

The map is a stand-in: a drawn massing model, not a real Istanbul survey. It exists so the
four directions can be compared on the same ground. Everything is emitted as SVG and
imported into Penpot with `createShapeFromSvg`.

    python3 design/perde/tools/isomap.py maket > /tmp/map.svg

Paint order is back-to-front by `gx + gy`; within one building the top face is drawn last so
its own side faces never cut into it.
"""

from __future__ import annotations

import json
import sys

W, H = 1440, 900


def _hash(gx: int, gy: int, seed: int) -> float:
    n = (gx * 73856093) ^ (gy * 19349663) ^ (seed * 83492791)
    n &= 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    n ^= n >> 16
    return (n & 0x7FFFFFFF) / 0x7FFFFFFF


def _pt(gx: float, gy: float, z: float, t: float, zh: float, ox: float, oy: float):
    return ((gx - gy) * t / 2 + ox, (gx + gy) * t / 4 - z * zh + oy)


def _d(pts) -> str:
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"


class Scene:
    def __init__(self, style: dict, seed: int = 7, n: int = 20, t: float = 112):
        self.s = style
        self.seed = seed
        self.n = n
        self.t = t
        self.zh = t * 0.34
        self.ox = W / 2
        self.oy = 24
        self.slab = 0.7
        self.rows: list[str] = []
        self.defs: list[str] = []

    # -- geometry -----------------------------------------------------------------
    def p(self, gx, gy, z=0.0):
        return _pt(gx, gy, z, self.t, self.zh, self.ox, self.oy)

    def cell(self, gx, gy, w, d, h, z0=0.0):
        """Four corners at the given footprint, lifted by h."""
        a = self.p(gx, gy, z0 + h)
        b = self.p(gx + w, gy, z0 + h)
        c = self.p(gx + w, gy + d, z0 + h)
        e = self.p(gx, gy + d, z0 + h)
        return a, b, c, e

    def faces(self, gx, gy, w, d, h, z0=0.0):
        a, b, c, e = self.cell(gx, gy, w, d, h, z0)
        a0, b0, c0, e0 = self.cell(gx, gy, w, d, 0.0, z0)
        return (a, b, c, e), (e, c, c0, e0), (c, b, b0, c0)

    # -- style helpers ------------------------------------------------------------
    def pick(self, gx, gy, key):
        pal = self.s[key]
        return pal[int(_hash(gx, gy, self.seed + hash(key) % 97) * len(pal)) % len(pal)]

    def is_water(self, gx, gy):
        # Decide by screen position, not grid index: the sea must reach the frame's right and
        # bottom edges, whatever the grid origin is.
        sx = (gx - gy) * self.t / 2 + self.ox
        sy = (gx + gy) * self.t / 4 + self.oy
        return sx > 1130 or sy > 788

    def is_road(self, gx, gy):
        return gx % 5 == 0 or gy % 5 == 0

    def is_park(self, gx, gy):
        return not self.is_road(gx, gy) and _hash(gx, gy, self.seed + 11) > 0.90

    def height(self, gx, gy):
        r = _hash(gx, gy, self.seed + 3)
        h = 0.5 + (r ** 1.9) * 2.2
        if _hash(gx, gy, self.seed + 5) > 0.962:
            h = 3.0 + _hash(gx, gy, self.seed + 6) * 1.0
        return h

    # -- layers -------------------------------------------------------------------
    def ground(self):
        s = self.s
        self.rows.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="{s["table"]}"/>')
        water, land = [], []
        for gy in range(self.n):
            for gx in range(self.n):
                if self.is_water(gx, gy):
                    water.append(_d(self.cell(gx, gy, 1, 1, 0)[:4]))
                else:
                    land.append(_d(self.cell(gx, gy, 1, 1, 0)[:4]))
        # One path per material: neighbouring tiles share an edge, so no seam appears.
        self.rows.append(f'<path d="{"".join(water)}" fill="{s["water"]}"/>')
        self.rows.append(f'<path d="{"".join(land)}" fill="{s["land"]}"/>')

    def slab_faces(self):
        s = self.s
        out = []
        for gy in range(self.n):
            for gx in range(self.n):
                if self.is_water(gx, gy):
                    continue
                a, b, c, e = self.cell(gx, gy, 1, 1, 0)
                a1, b1, c1, e1 = self.cell(gx, gy, 1, 1, -self.slab)
                if self.is_water(gx, gy + 1):
                    out.append(_d((e, c, c1, e1)))
                if self.is_water(gx + 1, gy):
                    out.append(_d((c, b, b1, c1)))
        self.rows.append(f'<path d="{"".join(out)}" fill="{s["slab"]}"/>')

    def roads(self):
        out = []
        for gy in range(self.n):
            for gx in range(self.n):
                if self.is_water(gx, gy) or not self.is_road(gx, gy):
                    continue
                out.append(_d(self.cell(gx, gy, 1, 1, 0.02)[:4]))
        self.rows.append(f'<path d="{"".join(out)}" fill="{self.s["road"]}"/>')

    def parks(self):
        out = []
        for gy in range(self.n):
            for gx in range(self.n):
                if self.is_water(gx, gy) or not self.is_park(gx, gy):
                    continue
                out.append(_d(self.cell(gx, gy, 1, 1, 0.03)[:4]))
        if out:
            self.rows.append(f'<path d="{"".join(out)}" fill="{self.s["park"]}"/>')

    def landmarks(self):
        return [(5, 13, "dome", 2.6), (12, 6, "tower", 1.0)]

    def reserved(self):
        cells = set()
        for gx, gy, kind, w in self.landmarks():
            if kind == "dome":
                for x in range(int(gx), int(gx + w) + 1):
                    for y in range(int(gy), int(gy + w) + 1):
                        cells.add((x, y))
            else:
                cells.add((gx, gy))
        return cells

    def buildings(self):
        s = self.s
        skip = self.reserved()
        ordered = [
            (gx + gy, gx, gy, None)
            for gy in range(self.n) for gx in range(self.n)
            if not self.is_water(gx, gy) and not self.is_road(gx, gy)
            and not self.is_park(gx, gy) and (gx, gy) not in skip
        ]
        for gx, gy, kind, w in self.landmarks():
            ordered.append((gx + gy, gx, gy, (kind, w)))
        ordered.sort(key=lambda i: (i[0], i[1]))
        for _, gx, gy, mark in ordered:
            if mark:
                self.landmark(gx, gy, mark[0])
                continue
            h = self.height(gx, gy)
            top, left, right = self.faces(gx, gy, 1, 1, h)
            self.rows.append(f'<path d="{_d(left)}" fill="{self.pick(gx, gy, "wall_left")}"/>')
            self.rows.append(f'<path d="{_d(right)}" fill="{self.pick(gx, gy, "wall_right")}"/>')
            if s.get("outline"):
                self.rows.append(
                    f'<path d="{_d(left)}{_d(right)}" fill="none" stroke="{s["outline"]}" '
                    f'stroke-width="{s.get("outline_w", 1)}" stroke-linejoin="round"/>')
            self.rows.append(f'<path d="{_d(top)}" fill="{self.pick(gx, gy, "wall_top")}"/>')
            if s.get("roof_line"):
                self.rows.append(
                    f'<path d="{_d(top)}" fill="none" stroke="{s["roof_line"]}" '
                    f'stroke-width="{s.get("outline_w", 1)}"/>')
            if s.get("windows") and h > 1.1:
                self.windows(gx, gy, h)

    def windows(self, gx, gy, h):
        s = self.s
        a, b, c, e = self.cell(gx, gy, 1, 1, h)
        rx = (e[0] + c[0]) / 2
        ry = (e[1] + c[1]) / 2
        rows_n = max(1, int(h * 2.2))
        cols_n = 3
        for r in range(rows_n):
            for k in range(cols_n):
                f1 = 0.18 + 0.62 * (k / max(1, cols_n - 1))
                f2 = 0.18 + 0.72 * (r / max(1, rows_n))
                # bilinear inside the left face parallelogram
                x = (e[0] + (c[0] - e[0]) * f1) + (a[0] - e[0]) * 0
                y = (e[1] + (c[1] - e[1]) * f1) - (h * self.zh) * (1 - f2)
                if _hash(gx * 7 + k, gy * 7 + r, self.seed + 21) < 0.55:
                    continue
                self.rows.append(
                    f'<rect x="{x - 2.1:.1f}" y="{y:.1f}" width="4.2" height="3.4" '
                    f'rx="0.6" fill="{s["windows"]}" opacity="0.9"/>')

    def landmark(self, gx, gy, kind="dome"):
        s = self.s
        if kind == "dome":
            w = d = 1.9
            h = 1.1
            top, left, right = self.faces(gx, gy, w, d, h)
            body = s.get("landmark_body", s["landmark_side"])
            dome = s["landmark_top"]
            self.rows.append(f'<path d="{_d(left)}" fill="{s["landmark_side"]}"/>')
            self.rows.append(f'<path d="{_d(right)}" fill="{s["landmark_side"]}"/>')
            self.rows.append(f'<path d="{_d(top)}" fill="{body}"/>')
            a, b, c, e = top
            cx, cy = (a[0] + c[0]) / 2, (a[1] + c[1]) / 2
            rx, ry = self.t * 0.60, self.t * 0.27
            # drum, then a half-ellipse dome: the silhouette is what makes it read as a mosque
            self.rows.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx * 1.04:.1f}" '
                             f'ry="{ry * 0.40:.1f}" fill="{body}"/>')
            self.rows.append(f'<path d="M{cx - rx:.1f},{cy:.1f} A{rx:.1f},{ry * 2.1:.1f} 0 0 1 '
                             f'{cx + rx:.1f},{cy:.1f} Z" fill="{dome}"/>')
            self.rows.append(f'<ellipse cx="{cx - rx * 0.26:.1f}" cy="{cy - ry * 1.05:.1f}" '
                             f'rx="{rx * 0.30:.1f}" ry="{ry * 0.34:.1f}" fill="#FFFFFF" opacity="0.20"/>')
            self.rows.append(f'<rect x="{cx - 1.3:.1f}" y="{cy - ry * 2.1 - 15:.1f}" width="2.6" '
                             f'height="17" fill="{dome}"/>')
            for dx in (-1, 1):
                mx, my = self.p(gx + w / 2 + dx * (w / 2 + 0.30), gy + d / 2, 0)
                mw, mh = 6.0, self.zh * 4.4
                self.rows.append(f'<rect x="{mx - mw / 2:.1f}" y="{my - mh:.1f}" width="{mw:.1f}" '
                                 f'height="{mh:.1f}" fill="{s["landmark_side"]}"/>')
                self.rows.append(f'<rect x="{mx - mw / 2 - 1.6:.1f}" y="{my - mh - 2:.1f}" '
                                 f'width="{mw + 3.2:.1f}" height="3" fill="{body}"/>')
                self.rows.append(
                    f'<path d="M{mx - mw / 2 - 1.8:.1f},{my - mh - 2:.1f} L{mx:.1f},{my - mh - 18:.1f} '
                    f'L{mx + mw / 2 + 1.8:.1f},{my - mh - 2:.1f} Z" fill="{dome}"/>')
        else:  # tower: a cylinder, so it reads as Galata rather than a cone
            h = 6.6
            top, left, right = self.faces(gx + 0.30, gy + 0.30, 0.40, 0.40, h)
            self.rows.append(f'<path d="{_d(left)}" fill="{s["landmark_side"]}"/>')
            self.rows.append(f'<path d="{_d(right)}" fill="{s["landmark_side"]}"/>')
            self.rows.append(f'<path d="{_d(top)}" fill="{s["landmark_top"]}"/>')
            cx, cy = (top[0][0] + top[2][0]) / 2, (top[0][1] + top[2][1]) / 2
            self.rows.append(f'<rect x="{cx - 15:.1f}" y="{cy - 34:.1f}" width="30" height="34" '
                             f'fill="{s["landmark_side"]}"/>')
            self.rows.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="15" ry="7.5" '
                             f'fill="{s["landmark_top"]}"/>')
            self.rows.append(f'<path d="M{cx - 15:.1f},{cy - 34:.1f} L{cx - 11:.1f},{cy + 1:.1f} '
                             f'L{cx + 11:.1f},{cy + 1:.1f} L{cx + 15:.1f},{cy - 34:.1f} Z" '
                             f'fill="{s["landmark_side"]}"/>')
            self.rows.append(f'<ellipse cx="{cx:.1f}" cy="{cy - 34:.1f}" rx="15" ry="7.5" '
                             f'fill="{s["landmark_top"]}"/>')
            self.rows.append(f'<path d="M{cx - 12:.1f},{cy - 34:.1f} L{cx:.1f},{cy - 56:.1f} '
                             f'L{cx + 12:.1f},{cy - 34:.1f} Z" fill="{s["landmark_top"]}"/>')

    def render(self) -> str:
        self.ground()
        self.slab_faces()
        self.roads()
        self.parks()
        self.buildings()
        defs = "".join(self.defs)
        body = "".join(self.rows)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
                f'viewBox="0 0 {W} {H}"><defs>{defs}</defs>{body}</svg>')


STYLES = {
    "maket": {
        "table": "#E7DBC4",
        "water": "#A9C6BF",
        "land": "#DBCEB4",
        "slab": "#B7A78A",
        "road": "#F1E8D6",
        "park": "#BCCE9C",
        "wall_top": ["#F8F1E3", "#F0E7D5", "#FCF6EB"],
        "wall_left": ["#B8A37F", "#AE9772", "#C1AC89"],
        "wall_right": ["#DCCCAE", "#D4C3A1", "#E3D5BA"],
        "windows": None,
        "outline": None,
        "landmark_top": "#8FA6A0",
        "landmark_side": "#D9C9A9",
        "landmark_body": "#EADFC6",
        "dome": "#8FA6A0",
    },
    "gece": {
        "table": "#0E1D24",
        "water": "#0D2129",
        "land": "#1A2C33",
        "slab": "#101F25",
        "road": "#223A43",
        "park": "#1E3A32",
        "wall_top": ["#2C444D", "#33505A", "#274049"],
        "wall_left": ["#182B33", "#142630", "#1B3039"],
        "wall_right": ["#213741", "#1D323B", "#253D47"],
        "windows": "#F0B45C",
        "outline": None,
        "landmark_top": "#3B5862",
        "landmark_side": "#22363F",
    },
    "rizo": {
        "table": "#F3EDE1",
        "water": "#C9D3DB",
        "land": "#F3EDE1",
        "slab": "#2C3A55",
        "road": "#F3EDE1",
        "park": "#BFD0B8",
        "wall_top": ["#C05A3C", "#2C3A55", "#F3EDE1"],
        "wall_left": ["#9C4630", "#1F2B40", "#DCD2C1"],
        "wall_right": ["#C05A3C", "#2C3A55", "#EFE6D6"],
        "windows": None,
        "outline": "#2C3A55",
        "outline_w": 1.4,
        "landmark_top": "#C05A3C",
        "landmark_side": "#9C4630",
    },
    "konsol": {
        "table": "#EEF0EC",
        "water": "#D9E6E7",
        "land": "#E9EBE5",
        "slab": "#D3D8D0",
        "road": "#FFFFFF",
        "park": "#DCE6CF",
        "wall_top": ["#FFFFFF", "#F7F8F5", "#FCFCFA"],
        "wall_left": ["#DDE1DA", "#D5DAD2", "#E2E5DE"],
        "wall_right": ["#EDEFEA", "#E6E9E3", "#F1F3EF"],
        "windows": None,
        "outline": "#C3C9C0",
        "outline_w": 0.9,
        "landmark_top": "#D7DCD4",
        "landmark_side": "#C3C9C0",
    },
}


def build(style: str = "maket", seed: int = 7) -> str:
    return Scene(STYLES[style], seed=seed).render()


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "maket"
    svg = build(name)
    sys.stdout.write(svg)
    print(f"\n{len(svg)} bytes -> stderr", file=sys.stderr)
