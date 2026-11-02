#!/usr/bin/env python3
"""Mechanical craft checks for a Penpot page.

    design_lint.py --page <page>
    design_lint.py --page <page> --rules design/<project>/craft-rules.json --json /tmp/lint.json

Complements design_qa.py: that one checks wiring (token coverage, render truth, hygiene),
this one checks craft thresholds — type scale, rhythm, accent count, alignment axes,
radius, shadows, overflow, placeholder copy. Thresholds are the defaults below and can be
overridden per project with `--rules` (a flat JSON of the same keys).

Exit codes: 0 no high findings, 1 high findings, 2 environment or transport.
"""

from __future__ import annotations

import argparse
import colorsys
import json
import pathlib
import re
import sys
import urllib.error

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from penpot_exec import McpError, call_execute_code, ensure_helpers, fail, load_url, payload  # noqa: E402

DEFAULTS = {
    "max_type_sizes": 6,
    "min_step_ratio": 1.25,
    "min_display_ratio": 3.0,
    "max_accents": 1,
    "min_body_size": 14,
    "max_measure_chars": 80,
    "allowed_radii": [0, 2, 4, 8, 12, 999],
    "board_widths": [1440, 390],
    "max_uppercase_ratio": 0.15,
    "dominant_ignore_prefix": [],
    "banned_text": ["lorem", "ipsum", "todo", "xxx", "placeholder", "başlık buraya"],
}

BANNED_EXACT = {"Text", "Rectangle", "Board", "Group"}

COLLECT = """
const page = penpot.currentFile.pages.find(p => p.name === __PAGE__);
if (!page) throw new Error("page not found: " + __PAGE__);
const out = [];
const walk = (s, parent) => {
  out.push({
    id: s.id, parentId: parent ? parent.id : null,
    name: s.name, type: s.type, parent: parent ? parent.name : null,
    x: Math.round(s.x * 10) / 10, y: Math.round(s.y * 10) / 10,
    w: Math.round(s.width * 10) / 10, h: Math.round(s.height * 10) / 10,
    fill: (s.fills && s.fills[0] && s.fills[0].fillColor) || null,
    img: !!((s.fills || []).find(f => f.fillImage)),
    radius: s.borderRadius === undefined ? null : s.borderRadius,
    shadows: (s.shadows || []).length,
    fontSize: s.type === "text" ? Number(s.fontSize) : null,
    lineHeight: s.type === "text" ? String(s.lineHeight) : null,
    text: s.type === "text" ? String(s.characters || "") : null,
    align: s.type === "text" ? String(s.align || "left") : null,
    inkX: s.type === "text" && s.textBounds ? Math.round(s.textBounds.x * 10) / 10 : null,
    inkY: s.type === "text" && s.textBounds ? Math.round(s.textBounds.y * 10) / 10 : null,
    inkW: s.type === "text" && s.textBounds ? Math.round(s.textBounds.width * 10) / 10 : null,
    inkH: s.type === "text" && s.textBounds ? Math.round(s.textBounds.height * 10) / 10 : null,
    inkTop: null,
    inkBottom: null,
  });
  (s.children || []).forEach(c => walk(c, s));
};
(page.root.children || []).forEach(s => walk(s, null));
return JSON.stringify(out);
"""


def saturation(hex_color: str) -> float:
    text = hex_color.lstrip("#")[:6]
    if len(text) != 6:
        return 0.0
    red, green, blue = (int(text[i : i + 2], 16) / 255 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(red, green, blue)[2]


def line_height_multiplier(raw: str | None) -> float | None:
    if not raw:
        return None
    try:
        value = float(str(raw).rstrip("%"))
    except ValueError:
        return None
    return value / 100 if value > 4 else value


def lint(nodes: list[dict], rules: dict) -> list[dict]:
    findings: list[dict] = []
    boards = [n for n in nodes if n["type"] == "board" and n["parentId"] is None]
    by_parent: dict[str, list[dict]] = {}
    for node in nodes:
        if node["parentId"]:
            by_parent.setdefault(node["parentId"], []).append(node)

    def subtree(board_id: str) -> list[dict]:
        out: list[dict] = []
        stack = list(by_parent.get(board_id, []))
        while stack:
            node = stack.pop()
            out.append(node)
            stack.extend(by_parent.get(node["id"], []))
        return out

    for board in boards:
        region = board["name"]

        def add(severity: str, message: str) -> None:
            findings.append({"board": region, "severity": severity, "finding": message})

        inside = subtree(board["id"])
        if int(board["w"]) not in rules["board_widths"]:
            add("medium", f"board width {board['w']} is not one of {rules['board_widths']}")

        texts = [n for n in inside if n["type"] == "text" and n["fontSize"]]
        sizes = sorted({n["fontSize"] for n in texts})
        if len(sizes) > rules["max_type_sizes"]:
            add("high", f"{len(sizes)} distinct type sizes (max {rules['max_type_sizes']}): {sizes}")
        if sizes:
            chrome = rules["dominant_ignore_prefix"] or []
            pool = [n for n in texts if not any(n["name"].startswith(c) for c in chrome)] or texts
            top_size = max(n["fontSize"] for n in pool)
            topmost = min((n for n in pool if n["fontSize"] == top_size), key=lambda n: n["y"])
            offset = topmost["y"] - board["y"]
            if offset > 900:
                add("high", f"largest type ({topmost['fontSize']}px, {topmost['name']}) starts at y={offset:.0f} — the page opens without a dominant element")
            counts = {size: sum(1 for n in texts if n["fontSize"] == size) for size in sizes}
            body = max(counts, key=counts.get)
            if sizes[-1] / body < rules["min_display_ratio"]:
                add(
                    "high",
                    f"display {sizes[-1]}px is only {sizes[-1] / body:.2f}x the body {body}px "
                    f"(min {rules['min_display_ratio']}x) — no scale drama",
                )
            if len(sizes) > 1:
                gaps = [b / a for a, b in zip(sizes, sizes[1:])]
                if min(gaps) < rules["min_step_ratio"]:
                    add("medium", f"type steps too close: {[round(g, 2) for g in gaps]}")

        for node in texts:
            if node["fontSize"] < rules["min_body_size"] and len(node["text"] or "") > 40:
                add("low", f"small paragraph at {node['fontSize']}px: {node['name']}")
            multiplier = line_height_multiplier(node["lineHeight"])
            if multiplier and node["fontSize"] >= 40 and multiplier > 1.25:
                add("medium", f"{node['name']}: {node['fontSize']}px at line-height {multiplier}")
            if node["w"] and node["fontSize"]:
                measure = len(node["text"] or "") / max(node["w"] / (node["fontSize"] * 0.5), 0.1)
                if 14 <= node["fontSize"] <= 20 and len(node["text"] or "") > 120 and measure > rules["max_measure_chars"]:
                    add("low", f"{node['name']}: ~{measure:.0f} characters per line")

        accents: dict[int, str] = {}
        for node in inside:
            fill = node["fill"]
            if not fill or saturation(fill) <= 0.5:
                continue
            text = fill.lstrip("#")[:6]
            if len(text) != 6:
                continue
            red, green, blue = (int(text[i : i + 2], 16) / 255 for i in (0, 2, 4))
            hue = round(colorsys.rgb_to_hls(red, green, blue)[0] * 12)
            accents.setdefault(hue, fill.upper())
        if len(accents) > rules["max_accents"]:
            add("high", f"{len(accents)} saturated accent hues (max {rules['max_accents']}): {sorted(accents.values())}")

        bad_radius = {
            n["radius"] for n in inside
            if isinstance(n["radius"], (int, float))
            and n["radius"] not in rules["allowed_radii"]
            and abs(n["radius"] * 2 - n["h"]) > 1  # a full pill/circle is fine at any size
        }
        if bad_radius:
            add("low", f"radius values outside the scale: {sorted(bad_radius)}")

        shadows = [n["name"] for n in inside if n["shadows"]]
        if shadows:
            add("medium", f"{len(shadows)} shape(s) with a shadow: {shadows[:3]}")

        bx, by = board["x"], board["y"]
        for node in inside:
            left, top = node["x"] - bx, node["y"] - by
            if left < -0.5 or top < -0.5 or left + node["w"] > board["w"] + 0.5 or top + node["h"] > board["h"] + 0.5:
                add("high", f"{node['name']} overflows the board (x={left:.0f} y={top:.0f} w={node['w']:.0f} h={node['h']:.0f})")
                break

        uppercase = [n for n in texts if (n["text"] or "").strip() and (n["text"] or "") == (n["text"] or "").upper() and len((n["text"] or "").strip()) > 3]
        if texts and len(uppercase) / len(texts) > rules["max_uppercase_ratio"]:
            add("medium", f"{len(uppercase)}/{len(texts)} text nodes are uppercase-tracked")

        # a one-line value+unit faked with two top-aligned boxes at different sizes
        # always drifts: box tops are not baselines. Flag the pattern for a 1:1
        # baseline check instead of trusting the coordinates.
        inks = [n for n in inside if n["type"] == "text" and n["inkW"] and n["inkH"] and n["inkW"] > 1]
        inline_flags = 0
        for i in range(len(inks)):
            for j in range(i + 1, len(inks)):
                a, b = inks[i], inks[j]
                if a["fontSize"] == b["fontSize"]:
                    continue
                if abs(a["y"] - b["y"]) > 12:
                    continue
                ox = min(a["inkX"] + a["inkW"], b["inkX"] + b["inkW"]) - max(a["inkX"], b["inkX"])
                oy = min(a["inkY"] + a["inkH"], b["inkY"] + b["inkH"]) - max(a["inkY"], b["inkY"])
                small = min(a["inkH"], b["inkH"])
                gap = max(a["inkX"], b["inkX"]) - min(a["inkX"] + a["inkW"], b["inkX"] + b["inkW"])
                if oy > small * 0.5 and gap < 48:
                    inline_flags += 1
                    if inline_flags <= 4:
                        add("medium", f"inline mixed-size pair {a['name']} ({a['fontSize']}px) / {b['name']} ({b['fontSize']}px): verify the shared baseline at 1:1")
        if inline_flags > 4:
            add("medium", f"{inline_flags - 4} more inline mixed-size pair(s) need a 1:1 baseline check")

        # text must not overlap text: ink rectangles come from textBounds (page-absolute)
        for i in range(len(inks)):
            for j in range(i + 1, len(inks)):
                a, b = inks[i], inks[j]
                ox = min(a["inkX"] + a["inkW"], b["inkX"] + b["inkW"]) - max(a["inkX"], b["inkX"])
                oy = min(a["inkY"] + a["inkH"], b["inkY"] + b["inkH"]) - max(a["inkY"], b["inkY"])
                if ox > 30 and oy > 12:
                    add("high", f"text overlap {a['name']} / {b['name']} ({ox:.0f}x{oy:.0f}px)")

        # text ink must not paint over a sibling shape: copy edits change ink width
        # without moving boxes (hero title slid 14px under its photo), and the
        # text-vs-text check above cannot see it. Ancestors (cards, bands, boards)
        # are the legitimate background and are excluded.
        parent_of = {n["id"]: n.get("parentId") for n in inside}
        def is_ancestor(anc_id, node_id):
            seen, cur = set(), parent_of.get(node_id)
            while cur and cur not in seen:
                if cur == anc_id:
                    return True
                seen.add(cur)
                cur = parent_of.get(cur)
            return False
        solids = [n for n in inside if n["type"] in ("rectangle", "board")
                  and (n["w"] or 0) > 4 and (n["h"] or 0) > 4 and (n.get("fill") or n.get("img"))]
        for t in inks:
            if not t["inkW"] or not t["inkH"]:
                continue
            for n in solids:
                if n["id"] == t.get("parentId") or is_ancestor(n["id"], t["id"]) or is_ancestor(t["id"], n["id"]):
                    continue
                ox = min(t["inkX"] + t["inkW"], n["x"] + n["w"]) - max(t["inkX"], n["x"])
                oy = min(t["inkY"] + t["inkH"], n["y"] + n["h"]) - max(t["inkY"], n["y"])
                if ox <= 8 or oy <= 8 or ox * oy <= 200:
                    continue
                # full containment = label sitting ON its pill/panel (legitimate
                # background); only a straddled edge is a collision
                straddles = t["inkX"] < n["x"] - 2 or t["inkX"] + t["inkW"] > n["x"] + n["w"] + 2
                if not straddles:
                    continue
                add("high", f"text {t['name']} paints over shape {n['name']} ({ox:.0f}x{oy:.0f}px ink overlap)")
                break

        for node in texts:
            blob = (node["text"] or "").lower()
            if any(word in blob for word in rules["banned_text"]) or (node["text"] or "").strip() in BANNED_EXACT:
                add("high", f"placeholder copy in {node['name']}: {node['text'][:40]!r}")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--page", required=True)
    parser.add_argument("--rules", type=pathlib.Path)
    parser.add_argument("--json", type=pathlib.Path)
    parser.add_argument("--dump-nodes", type=pathlib.Path,
                        help="write the raw geometry collector output for rhythm.py")
    args = parser.parse_args()

    rules = dict(DEFAULTS)
    if args.rules:
        try:
            rules.update(json.loads(args.rules.read_text()))
        except (OSError, json.JSONDecodeError) as error:
            fail(f"{args.rules}: {error}")

    try:
        url = load_url()
        ensure_helpers(url)
        nodes = payload(call_execute_code(url, COLLECT.replace("__PAGE__", json.dumps(args.page))))
        if not isinstance(nodes, list):
            fail("collector returned no node list")
    except McpError as exc:
        fail(str(exc))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        fail(f"{type(exc).__name__}: {exc}")

    if args.dump_nodes:
        args.dump_nodes.write_text(json.dumps(nodes, indent=1) + "\n")
        print(f"wrote {args.dump_nodes} ({len(nodes)} nodes)")

    findings = lint(nodes, rules)
    high = [f for f in findings if f["severity"] == "high"]

    print(f"page: {args.page}  shapes: {len(nodes)}  findings: {len(findings)} ({len(high)} high)")
    for finding in findings:
        print(f"  [{finding['severity']:<6}] {finding['board']}: {finding['finding']}")
    if not findings:
        print("  clean on the mechanical checks — that proves compliance, not design")

    if args.json:
        args.json.write_text(json.dumps({"page": args.page, "findings": findings}, indent=2) + "\n")
        print(f"wrote {args.json}")
    return 1 if high else 0


if __name__ == "__main__":
    raise SystemExit(main())
