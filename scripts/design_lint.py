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
    "max_uppercase_ratio": 0.35,
    # Label-heavy UIs (nav, kickers, table headers) track 20-25% of their text
    # nodes in uppercase without shouting; a table/label surface with a fee
    # matrix reaches ~31% (İHKD 09, 27/87). Above 35% it reads as
    # tracking-as-decoration, not hierarchy.
    "min_card_padding": 16,
    "min_panel_w": 200,
    "min_panel_h": 60,
    "dominant_ignore_prefix": [],
    "banned_text": ["lorem", "ipsum", "todo", "xxx", "placeholder", "başlık buraya"],
    "fit_tol": 1.0,        # px tolerance for ink-vs-container containment
    "fit_bar_delta": 4.0,  # MEDIUM when an accent bar differs from its text span by more
    "fit_rule_min": 60.0,  # hairline rules shorter than this are ticks, not boundaries
    # Audit rules (2026-11-02): classes the eye found and the gate could not see.
    "min_gap_ratio": 0.35,       # stacked title/meta ink gap under this x its line is a finding
    "min_gap_high_ratio": 0.25,  # under this share of the line it is HIGH
    "min_gap_title_size": 22,    # only a heading over a meta (not a label over a title)
    "min_gap_meta_size": 16,
    "min_gap_descender_ratio": 0.3,  # a figure/caps line ends at its baseline, but
                                     # textBounds still reserves the font's descent
                                     # (measured 0.30em on 06's 44px "96")
    "marker_centre_tol": 1.5,    # px a bullet centre may drift from the line's ink centre
    "marker_rule_tol": 2.0,      # px a list separator may drift from the marker's left edge
    "marker_rule_gap": 48.0,     # how close below the item a separator still belongs to it
    "surface_white": ["#FFFFFF"],
    "surface_alt": ["#E8EBED"],  # inset/side-panel surface, never a card grid
    "surface_card_min_w": 120.0,
    "surface_card_min_h": 60.0,
    "surface_alt_min_w": 400.0,  # a large alt card beside white cards is a role conflict
    "surface_band_ratio": 0.8,   # wider than this share of the board is a band, not a card
    "float_btn_min_w": 60.0,
    "float_btn_max_w": 420.0,
    "float_max_gap": 160.0,      # horizontal gap between a button and its row link
    "float_centre_tol": 6.0,     # px the two centres may differ before it reads misaligned
    "float_high_centre_diff": 16.0,
    "float_max_centre_diff": 120.0,
    "min_stat_size": 30.0,       # a stats-row number is display type, not body copy
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
    stroke: !!((s.strokes || []).length),
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


# Glyphs whose ink goes below the baseline. A line of digits or capitals ends
# at its baseline, but `textBounds` still reaches down through the font's
# descender, so an ink-gap measured from it understates the air the eye sees.
DESCENDERS = set("gjpqyçş,;()[]{}|/\\")


def has_descender(raw: str | None) -> bool:
    return any(ch in DESCENDERS for ch in str(raw or ""))


def is_panel(node: dict, rules: dict) -> bool:
    """A content board whose inner edge is a padding contract: full-bleed
    boards (x=0) are edge-to-edge by design, and single-label pills/chips
    carry centered labels, not padding — the two populations separate by
    size (İHKD chips top out at 187x36, smallest panel is 1200x72)."""
    if (node.get("x") or 0) == 0:
        return False
    if (node.get("w") or 0) < rules["min_panel_w"] or (node.get("h") or 0) < rules["min_panel_h"]:
        return False
    if node.get("stroke"):
        return True
    fill = node.get("fill")
    try:
        return bool(fill) and saturation(fill) <= 0.5
    except (ValueError, TypeError):
        return False


def is_background(solid: dict, board_w: float) -> bool:
    """A solid a text may legitimately sit ON (full containment is not a
    defect): imagery overlays, muted surfaces (zebra bands, cards, panels)
    and full-width bands. A compact SATURATED sibling — a red button, an
    accent chip — is a control, never a background: a text fully inside it
    is a collision the old straddle-only check could not see (the DAHİL /
    'Devam et' overlap read as a 'label on its pill'). Ancestors are handled
    separately by the caller; this answers the sibling case only."""
    if solid.get("img"):
        return True
    try:
        if not solid.get("fill") or saturation(solid["fill"]) <= 0.5:
            return True
    except (ValueError, TypeError):
        return True
    return (solid.get("w") or 0) >= 0.8 * (board_w or 0)


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
        by_id = {n["id"]: n for n in inside}
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
        ink_boxes = {}
        for t in inks:
            if t["inkW"] and t["inkH"]:
                x = t["inkX"] if t.get("inkX") is not None else t["x"]
                y = t["inkY"] if t.get("inkY") is not None else t["y"]
                ink_boxes[t["id"]] = (x, y, x + t["inkW"], y + t["inkH"])
        occupants: dict[str, list[str]] = {}
        for n in solids:
            inside_ids = [tid for tid, (lx, ty, rx, by) in ink_boxes.items()
                          if lx >= n["x"] - 1 and ty >= n["y"] - 1
                          and rx <= n["x"] + n["w"] + 1 and by <= n["y"] + n["h"] + 1]
            occupants[n["id"]] = inside_ids
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
                # full containment in a background solid (muted band, photo,
                # full-width strip) is a text sitting ON its surface; a lone
                # text inside a compact saturated sibling is that control's
                # own label (the active-pill pattern) and is equally clean.
                # Anything beyond the label — DAHİL/'Devam et' — collides.
                straddles = t["inkX"] < n["x"] - 2 or t["inkX"] + t["inkW"] > n["x"] + n["w"] + 2
                if not straddles:
                    if is_background(n, board["w"]):
                        continue
                    if occupants.get(n["id"]) == [t["id"]]:
                        continue
                    add("high", f"text {t['name']} sits on sibling control {n['name']} "
                               f"(ink fully inside {n['w']:.0f}x{n['h']:.0f}px solid)")
                    break
                add("high", f"text {t['name']} paints over shape {n['name']} ({ox:.0f}x{oy:.0f}px ink overlap)")
                break

        for node in texts:
            blob = (node["text"] or "").lower()
            if any(word in blob for word in rules["banned_text"]) or (node["text"] or "").strip() in BANNED_EXACT:
                add("high", f"placeholder copy in {node['name']}: {node['text'][:40]!r}")

        # a text that never laid out (1x1 box with copy) paints nothing:
        # the exporter clips to the box, so an unmeasured label is an
        # invisible label. Layout that never commits is a build defect —
        # seed an estimated box at build time and refit — not a timing
        # artifact worth waiting out.
        for node in texts:
            if (node["w"] or 0) <= 2 and (node["h"] or 0) <= 2 and (node["text"] or "").strip():
                add("high", f"text {node['name']} has an unlaid-out box "
                             f"({node['w']:.0f}x{node['h']:.0f}px) — refit, then re-export")

        # text must not hug a panel's stroked/surface edge: S.board children
        # use page-absolute coords, so x:120 inside a board at x:120 is zero
        # padding against the stroke (İHKD 04 propose). A label fully ON a
        # nested pill is legitimate background (same straddle logic as the
        # text-over-shape check) and pills themselves are not panels.
        for panel in [n for n in inside if n["type"] == "board" and is_panel(n, rules)]:
            kids = [n for n in inside if n.get("parentId") == panel["id"]]
            solids = [n for n in kids if n["type"] in ("rectangle", "board")
                      and (n.get("fill") or n.get("img"))]
            for t in kids:
                if t["type"] != "text" or not (t.get("inkW") or t.get("w")):
                    continue
                # unlaid-out texts report null bounds (read as 0): fall back to
                # the box edge so missing layout never reads as negative inset
                ink_l = t["x"]
                if t.get("inkW"):
                    ink_l = t["inkX"] if t.get("inkX") is not None else t["x"]
                if ink_l - panel["x"] >= rules["min_card_padding"]:
                    continue
                ink_t = t["inkY"] if t.get("inkY") is not None else t["y"]
                ink_r = ink_l + (t.get("inkW") or t.get("w") or 0)
                ink_b = ink_t + (t.get("inkH") or t.get("h") or 0)
                on_pill = any(
                    s["x"] - 2 <= ink_l and ink_r <= s["x"] + s["w"] + 2
                    and s["y"] - 2 <= ink_t and ink_b <= s["y"] + s["h"] + 2
                    for s in solids
                )
                if on_pill:
                    continue
                add("medium", f"{t['name']}: ink starts {ink_l - panel['x']:.0f}px inside {panel['name']} — panel padding under {rules['min_card_padding']}px")

        # two unrelated texts must never share ink: the İHKD 01 hero
        # caption/red-label crash passed every gate because text-over-shape
        # only looks at shapes. Stacks (a vertical gap between inks) and
        # inline same-line pairs (adjacent, no x-overlap) can never trip this;
        # only true rectangle overlap flags, which has no legitimate use here.
        # Pairs without measured ink are skipped: unlaid-out boxes overlap
        # routinely before fit, and that timing noise is not a finding.
        texts = [n for n in inside if n["type"] == "text"]
        for ia, a in enumerate(texts):
            if not a.get("inkW"):
                continue
            al = a["inkX"] if a.get("inkX") is not None else a["x"]
            at = a["inkY"] if a.get("inkY") is not None else a["y"]
            ar, ab = al + a["inkW"], at + (a.get("inkH") or 0)
            for b in texts[ia + 1:]:
                if not b.get("inkW"):
                    continue
                bl = b["inkX"] if b.get("inkX") is not None else b["x"]
                bt = b["inkY"] if b.get("inkY") is not None else b["y"]
                ox = min(ar, bl + b["inkW"]) - max(al, bl)
                oy = min(ab, bt + (b.get("inkH") or 0)) - max(at, bt)
                if ox > 8 and oy > 4:
                    add("medium", f"text {a['name']} collides with text {b['name']} ({ox:.0f}x{oy:.0f}px ink overlap)")

        # ---- fit family: content must sit inside the slot it was given ----
        # A text box can sit neatly inside its card while its measured ink
        # spills past the card edge, a row boundary or a hairline rule — the
        # box-vs-board overflow check above cannot see any of that, so a tall
        # card grid reads clean while glyphs paint over the next row (the
        # 07-program schedule: 5 meta texts crossed row rules at 0 high).
        # All three checks read measured ink (textBounds), never the box.
        tol = rules["fit_tol"]
        inked = [n for n in inside if n["type"] == "text" and n.get("inkW") and n.get("inkH")]

        def ink_box(n):
            x = n["inkX"] if n.get("inkX") is not None else n["x"]
            y = n["inkY"] if n.get("inkY") is not None else n["y"]
            return (x, y, x + n["inkW"], y + n["inkH"])

        def contains(outer, lx, ty, rx, by):
            return (outer["x"] - tol <= lx and outer["y"] - tol <= ty
                    and rx <= outer["x"] + outer["w"] + tol and by <= outer["y"] + outer["h"] + tol)

        # 1. container overflow: the smallest rect/board on the same surface
        # that wraps the text BOX wins (parent chain or a same-parent slot);
        # when the measured INK leaves that container, the content outgrew
        # its slot. The top board itself is excluded — box-vs-board overflow
        # above already owns that edge. When no slot wraps the box, the
        # nearest rect/board ancestor (else the board) becomes the container,
        # so a board-level text can no longer skip the ink check silently; a
        # box that leaves even that fallback is a MEDIUM "no container".
        slots = [n for n in inside
                 if n["type"] in ("rectangle", "board") and n["id"] != board["id"]
                 and (n["w"] or 0) > 4 and (n["h"] or 0) > 4]

        def nearest_box(t):
            current, seen = t.get("parentId"), set()
            while current and current not in seen:
                node = by_id.get(current)
                if node and node["type"] in ("rectangle", "board"):
                    return node
                seen.add(current)
                current = node.get("parentId") if node else None
            return board

        def overflow_text(slot, ix, iy, ir, ib):
            over = []
            if ix < slot["x"] - tol:
                over.append(f"left +{slot['x'] - ix:.0f}px")
            if ir > slot["x"] + slot["w"] + tol:
                over.append(f"right +{ir - slot['x'] - slot['w']:.0f}px")
            if iy < slot["y"] - tol:
                over.append(f"top +{slot['y'] - iy:.0f}px")
            if ib > slot["y"] + slot["h"] + tol:
                over.append(f"bottom +{ib - slot['y'] - slot['h']:.0f}px")
            return over

        for t in inked:
            lx, ty, rx, by = t["x"], t["y"], t["x"] + (t["w"] or 0), t["y"] + (t["h"] or 0)
            parent_slot = nearest_box(t)
            if parent_slot and parent_slot.get("id") != board["id"]:
                box_over = overflow_text(parent_slot, lx, ty, rx, by)
                if box_over:
                    add("high", f"text {t['name']} box ({rx - lx:.0f}x{by - ty:.0f}) exceeds its "
                                f"container {parent_slot['name']} ({', '.join(box_over)} outside)")
                    continue
            cands = [s for s in slots
                     if (s["id"] == t.get("parentId") or is_ancestor(s["id"], t["id"])
                         or s.get("parentId") == t.get("parentId"))
                     and contains(s, lx, ty, rx, by)]
            if cands:
                slot = min(cands, key=lambda s: (s["w"] or 0) * (s["h"] or 0))
            else:
                fallback = parent_slot or board
                if contains(fallback, lx, ty, rx, by):
                    slot = fallback
                else:
                    add("medium", f"text {t['name']} has no enclosing container "
                                  f"(box {rx - lx:.0f}x{by - ty:.0f} at x={lx:.0f} y={ty:.0f})")
                    continue
            ix, iy, ir, ib = ink_box(t)
            over = overflow_text(slot, ix, iy, ir, ib)
            if over:
                add("high", f"text {t['name']} overflows its container {slot['name']} ({', '.join(over)} ink outside)")

        # 2. boundary entry: ink that straddles a sibling container's edge has
        # entered the next slot — including the zebra/row bands a schedule
        # paints behind alternating rows. Full containment is owned by the
        # paints-over-shape check above (background solid: clean; compact
        # saturated sibling: control collision), so this loop only flags edge
        # crossings. Hairline rules are too thin for an area check, so they
        # get their own strict crossing test below.
        entered: set[str] = set()
        for t in inked:
            ix, iy, ir, ib = ink_box(t)
            for s in slots:
                if s.get("parentId") != t.get("parentId") or s["id"] == t["id"]:
                    continue
                if (s["w"] or 0) <= 4 or (s["h"] or 0) <= 4:
                    continue
                if s["id"] == t.get("parentId") or is_ancestor(s["id"], t["id"]):
                    continue
                ox = min(ir, s["x"] + s["w"]) - max(ix, s["x"])
                oy = min(ib, s["y"] + s["h"]) - max(iy, s["y"])
                if ox <= tol or oy <= tol:
                    continue
                if contains(s, ix, iy, ir, ib):
                    continue  # owned by paints-over-shape: background or control-sit
                add("high", f"text {t['name']} enters sibling container {s['name']} ({ox:.0f}x{oy:.0f}px ink inside)")
                entered.add(t["id"])
                break

        # 3. rule crossing: a hairline (<=2px) rule is a row/column
        # boundary, and ink crossing its line paints two slots at once. The
        # area-based checks above divide by ~zero here, so crossing is
        # strict: ink must start on one side and end on the other with a
        # real run (>8px) along the rule. Texts already caught entering a
        # container are not reported twice.
        long_rules = [n for n in inside
                      if n["type"] == "rectangle"
                      and (((n["h"] or 0) <= 2 + tol and (n["w"] or 0) >= rules["fit_rule_min"])
                           or ((n["w"] or 0) <= 2 + tol and (n["h"] or 0) >= rules["fit_rule_min"]))]
        for t in inked:
            if t["id"] in entered:
                continue
            ix, iy, ir, ib = ink_box(t)
            for r in long_rules:
                if r.get("parentId") != t.get("parentId"):
                    continue
                horizontal = (r["h"] or 0) <= 2 + tol
                if horizontal:
                    ry = r["y"] + (r["h"] or 0) / 2
                    run = min(ir, r["x"] + r["w"]) - max(ix, r["x"])
                    if iy < ry - tol and ib > ry + tol and run > 8:
                        add("high", f"text {t['name']} crosses rule {r['name']} (ink {iy:.0f}-{ib:.0f}px over line y={ry:.0f})")
                        break
                else:
                    rx = r["x"] + (r["w"] or 0) / 2
                    run = min(ib, r["y"] + r["h"]) - max(iy, r["y"])
                    if ix < rx - tol and ir > rx + tol and run > 8:
                        add("high", f"text {t['name']} crosses rule {r['name']} (ink {ix:.0f}-{ir:.0f}px over line x={rx:.0f})")
                        break

        # 3b. column band: a row rule's LENGTH is the band its texts must stay
        # inside. The container checks above need a box; a row separated only
        # by a hairline has none, so a title that outgrows the row paints past
        # the column edge into the gutter or an arrow and every box-based rule
        # reads clean (İHKD 01: journal meta ended 12px past its 300px band,
        # the group rows sat 21px from their box edge with no band at all).
        # A link underline ("<name> under") marks a text span, not a column.
        bands = [n for n in long_rules
                 if (n["h"] or 0) <= 2 and not n["name"].endswith(" under")]
        for t in inked:
            if t["id"] in entered:
                continue
            ix, iy, ir, ib = ink_box(t)
            for r in bands:
                if r.get("parentId") != t.get("parentId"):
                    continue
                if not (-tol <= ix - r["x"] <= 60):
                    continue
                if (t.get("w") or 0) - (ir - ix) > 8:
                    # the text declares a box wider than its ink, so containment
                    # is that box's job (rule 3 above); a hairline further down
                    # belongs to the next block, not to this text's column
                    # (11-akademi: the 760px lede against the search field's
                    # 400px underline, 128px below and unrelated)
                    continue
                if not (0 < r["y"] - ib <= 140):
                    continue
                over = ir - (r["x"] + r["w"])
                if over > tol:
                    add("high", f"text {t['name']} runs {over:.0f}px past its "
                                f"{r['w']:.0f}px column band ({r['name']})")
                    break

        # 4. bar vs content: a thin saturated vertical bar is an accent that
        # belongs to the text column beside it, so its height must match the
        # column's ink span within fit_bar_delta. Same-parent pairing only —
        # a page-long divider next to an unrelated column is not its bar —
        # and unsaturated dividers are exempt by design.
        thin_bars = [n for n in inside
                     if n["type"] == "rectangle" and n["id"] != board["id"]
                     and (n["w"] or 0) <= 3 and (n["h"] or 0) >= 40]
        for bar in thin_bars:
            try:
                if not bar.get("fill") or saturation(bar["fill"]) <= 0.5:
                    continue
            except (ValueError, TypeError):
                continue
            mates = [n for n in inked
                     if n.get("parentId") == bar.get("parentId")
                     and (n["inkX"] if n.get("inkX") is not None else n["x"]) >= bar["x"] - tol
                     and (n["inkX"] if n.get("inkX") is not None else n["x"]) <= bar["x"] + 160
                     and min(ink_box(n)[3], bar["y"] + bar["h"]) - max(ink_box(n)[1], bar["y"]) > 10]
            if not mates:
                continue
            top = min(ink_box(n)[1] for n in mates)
            bot = max(ink_box(n)[3] for n in mates)
            if abs(bar["h"] - (bot - top)) > rules["fit_bar_delta"]:
                add("medium", f"bar {bar['name']} h={bar['h']:.0f}px vs content span {bot - top:.0f}px "
                              f"(Δ{abs(bar['h'] - (bot - top)):.0f}px over {rules['fit_bar_delta']:.0f}px)")

        # 5. sibling surfaces must not touch: two same-parent rect/board
        # solids (hairlines and chips excluded by touch_min) whose facing
        # edges close under touch_gap with a real run along the edge, on
        # different surfaces (fills differ, or either is an image). A photo
        # glued to its card's edge with a 0px joint reads as a leak, not a
        # layout; same-fill joints are invisible seams and stay clean.
        touch_min, touch_gap, touch_run = 24.0, 4.0, 24.0
        surfaces = [n for n in inside
                    if n["type"] in ("rectangle", "board") and n["id"] != board["id"]
                    and (n["w"] or 0) >= touch_min and (n["h"] or 0) >= touch_min
                    and (n.get("fill") or n.get("img"))]

        def same_surface(a: dict, b: dict) -> bool:
            if a.get("img") or b.get("img"):
                return False
            fa, fb = (a.get("fill") or "").upper(), (b.get("fill") or "").upper()
            return bool(fa) and fa == fb

        for ia in range(len(surfaces)):
            for ib in range(ia + 1, len(surfaces)):
                a, b = surfaces[ia], surfaces[ib]
                if a.get("parentId") != b.get("parentId"):
                    continue
                if same_surface(a, b):
                    continue
                if a["y"] <= b["y"]:
                    vgap = b["y"] - (a["y"] + a["h"])
                else:
                    vgap = a["y"] - (b["y"] + b["h"])
                if 0 <= vgap < touch_gap:
                    run = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"])
                    if run >= touch_run:
                        add("medium", f"{a['name']} touches {b['name']} "
                                     f"({vgap:.0f}px gap, different surfaces) — a glued joint reads as a leak")
                        continue
                if a["x"] <= b["x"]:
                    hgap = b["x"] - (a["x"] + a["w"])
                else:
                    hgap = a["x"] - (b["x"] + b["w"])
                if 0 <= hgap < touch_gap:
                    run = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
                    if run >= touch_run:
                        add("medium", f"{a['name']} touches {b['name']} "
                                     f"({hgap:.0f}px gap, different surfaces) — a glued joint reads as a leak")

        # 6. dead space: a card/panel whose content ends far above its own
        # bottom edge reads as a leak, not air. Trailing void (container
        # bottom minus last descendant ink bottom) beyond dead_med — and
        # beyond 1.5x the largest contained line height, so display type
        # is not punished — is MEDIUM; beyond dead_high is HIGH.
        dead_med, dead_high = 32.0, 80.0
        for c in surfaces:
            desc = [t for t in inked if t["id"] == c["id"] or is_ancestor(c["id"], t["id"])]
            if not desc:
                continue
            bottoms = [ink_box(t)[3] for t in desc]
            # a card whose last object is a tile, a photo or a chart is full:
            # its own text stops high inside that object, which is the object's
            # business, not the card's (10-konaklama: four 90px hall tiles, the
            # letters 68px above the card's edge while the tiles end 26px above
            # it). Only substantial objects count, so a hairline cannot mask.
            bottoms += [n["y"] + (n["h"] or 0) for n in inside
                        if n["id"] != c["id"] and is_ancestor(c["id"], n["id"])
                        and n["type"] != "text"
                        and (n.get("fill") or n.get("img"))
                        and (n["w"] or 0) >= 24 and (n["h"] or 0) >= 24]
            lines = [(t.get("fontSize") or 0) * (line_height_multiplier(t.get("lineHeight")) or 1.5)
                     for t in desc]
            trailing = (c["y"] + c["h"]) - max(bottoms)
            if trailing > dead_med and trailing > 1.5 * max(lines or [0]):
                # row-equalized cards are exempt from the medium: bottoms
                # align with a sibling card and content is top-anchored, so
                # the void is the grid's — but past dead_high the row needs
                # regrouping, exemption or not
                sibs = [s for s in surfaces
                        if s["id"] != c["id"] and s.get("parentId") == c.get("parentId")
                        and abs((s["y"] + s["h"]) - (c["y"] + c["h"])) <= 4]
                top_anchored = min(ink_box(t)[1] for t in desc) - c["y"] <= 24
                if sibs and top_anchored and trailing <= dead_high:
                    continue
                level = "high" if trailing > dead_high else "medium"
                add(level, f"dead space in {c['name']}: {trailing:.0f}px below the last ink "
                           f"(content ends, card continues)")

        # 8. intra-card gap: two texts stacked in one column of one card must
        # read as one block. A title pushed up and a meta pushed down — a gap
        # over 1.5x the line height — is MEDIUM. A photo or rule between them
        # breaks the chain: the gap belongs to the divider, not the texts.
        cardlike = [n for n in inside
                    if n["type"] in ("rectangle", "board") and n["id"] != board["id"]
                    and (n["w"] or 0) >= 24 and (n["h"] or 0) >= 24
                    and (n.get("fill") or n.get("img"))]
        for c in cardlike:
            kids = sorted([t for t in inked if t.get("parentId") == c["id"]],
                          key=lambda t: ink_box(t)[1])
            for a, b in zip(kids, kids[1:]):
                ax0, ay0, ax1, ay1 = ink_box(a)
                bx0, by0, bx1, by1 = ink_box(b)
                if by0 < ay1 - tol:
                    continue
                run = min(ax1, bx1) - max(ax0, bx0)
                if run <= 0.5 * min(ax1 - ax0, bx1 - bx0):
                    continue
                gap = by0 - ay1
                mid = (ay1 + by0) / 2
                def divides(n):
                    """An object in the air between the two lines owns that gap.

                    Solids and composites (an ECG trace, a quote bar) count when
                    they span the gap's middle; a hairline rule counts when it
                    sits anywhere inside the gap, because a 1px divider between
                    two rows is a divider (20-panel aidat: 2026 / 2025, 36px
                    apart with a rule at their centre) and the old ">8px tall"
                    test could never see it.
                    """
                    if n["id"] in (a["id"], b["id"], c["id"]):
                        return False
                    if min(ax1, bx1, n["x"] + (n["w"] or 0)) - max(ax0, bx0, n["x"]) <= 8:
                        return False
                    if (n["h"] or 0) <= 2:
                        return ay1 - 1 <= n["y"] <= by0 + 1
                    return n["y"] <= mid <= n["y"] + (n["h"] or 0)

                if any(divides(n) for n in inside):
                    continue
                label = str(b.get("text") or "")
                if (label and label == label.upper() and any(ch.isalpha() for ch in label)
                        and len(label) <= 40 and (b.get("fontSize") or 99) <= 13):
                    continue  # an all-caps kicker starts a block; its air above is
                              # the block break, not a drifting title/meta pair
                              # (16-makale: p3 over "SAYILARLA PROGRAM")
                line = max(a["fontSize"] * (line_height_multiplier(a.get("lineHeight")) or 1.5),
                           b["fontSize"] * (line_height_multiplier(b.get("lineHeight")) or 1.5))
                trail = (c["y"] + (c["h"] or 0)) - by1
                if b == kids[-1] and gap > 10 * line and trail < 64:
                    continue  # docked footer: an absurd gap above a bottom-pinned
                    # last line is a pinned footer, not drifting copy
                if gap > 1.5 * line:
                    add("medium", f"intra-card gap in {c['name']}: {a['name']} / {b['name']} "
                                   f"({gap:.0f}px between stacked texts)")

        # 7. empty corridor: a horizontal strip with no content spanning most
        # of the board reads as a missing row, not air — but only inside a
        # data region. Section air between prose blocks is rhythm and stays
        # clean: the strip must touch a card-like solid (a filled rect/board
        # narrower than the full grid, e.g. a session card or a break band)
        # on its top or bottom edge. Strips taller than corr_h with content
        # coverage under corr_cover and no near-full-width block touching
        # either edge are HIGH.
        corr_h, corr_cover, corr_span = 64.0, 0.4, 0.8
        kids = [n for n in inside if n.get("parentId") == board["id"]]
        edges = sorted({board["y"], board["y"] + board["h"]}
                       | {k["y"] for k in kids} | {k["y"] + (k["h"] or 0) for k in kids})
        for e1, e2 in zip(edges, edges[1:]):
            if e2 - e1 <= corr_h:
                continue
            inter = [k for k in kids if k["y"] < e2 - 0.5 and k["y"] + (k["h"] or 0) > e1 + 0.5]
            spans = sorted((max(k["x"], board["x"]), min(k["x"] + (k["w"] or 0), board["x"] + board["w"]))
                           for k in inter)
            union, cx0, cx1 = 0.0, None, None
            for s0, s1 in spans:
                if cx0 is None:
                    cx0, cx1 = s0, s1
                elif s0 <= cx1:
                    cx1 = max(cx1, s1)
                else:
                    union += max(0.0, cx1 - cx0)
                    cx0, cx1 = s0, s1
            if cx0 is not None:
                union += max(0.0, cx1 - cx0)
            if union / (board["w"] or 1) >= corr_cover:
                continue
            touch = [k for k in kids
                     if abs(k["y"] + (k["h"] or 0) - e1) <= 1 or abs(k["y"] - e2) <= 1]
            # a hairline is not a block: only a substantial full-width band
            # (content grid or wider) turns the strip into section air
            if any((k["w"] or 0) >= corr_span * (board["w"] or 0) and (k["h"] or 0) >= 24
                   for k in touch):
                continue
            # tolerance 6: cards carry a 4px top pad, so a card starting
            # just inside the next row still bounds the strip above it
            above = [k for k in kids
                       if k["type"] in ("rectangle", "board") and (k.get("fill") or k.get("img"))
                       and (k["w"] or 0) >= 24 and (k["h"] or 0) >= 24
                       and (k["w"] or 0) < corr_span * (board["w"] or 0)
                       and 40 <= (k["h"] or 0) <= 400
                       and abs(k["y"] + (k["h"] or 0) - e1) <= 6]
            below = [k for k in kids
                       if k["type"] in ("rectangle", "board") and (k.get("fill") or k.get("img"))
                       and (k["w"] or 0) >= 24 and (k["h"] or 0) >= 24
                       and (k["w"] or 0) < corr_span * (board["w"] or 0)
                       and 40 <= (k["h"] or 0) <= 400
                       and abs(k["y"] - e2) <= 6]
            if not above or not below:
                continue
            add("high", f"empty corridor {e2 - e1:.0f}px (y {e1:.0f}-{e2:.0f}px): "
                        f"no content, no divider — reads as a missing row")

        # ---- audit rules (2026-11-02): classes the eye caught, no gate owned ----

        # 9. min-gap: a title and its meta in one list row must not touch.
        # The 01 group rows sit 5px apart against a 19.5px meta line. Scoped to
        # a heading over a meta inside a row closed by a hairline, so the
        # 19-giris logo lockup and the 12-kurs-detay progress stat stay clean.
        for i, a in enumerate(inked):
            ax0, ay0, ax1, ay1 = ink_box(a)
            for b in inked[i + 1:]:
                if a.get("parentId") != b.get("parentId"):
                    continue
                bx0, by0, bx1, by1 = ink_box(b)
                if by0 >= ay1:
                    gap, top, bot = by0 - ay1, a, b
                elif ay0 >= by1:
                    gap, top, bot = ay0 - by1, b, a
                else:
                    continue
                band = min(ax1, bx1) - max(ax0, bx0)
                if band <= 0.5 * min(ax1 - ax0, bx1 - bx0):
                    continue
                line = min(
                    (top.get("fontSize") or 0) * (line_height_multiplier(top.get("lineHeight")) or 1.5),
                    (bot.get("fontSize") or 0) * (line_height_multiplier(bot.get("lineHeight")) or 1.5),
                )
                visible = gap + (0 if has_descender(top.get("text")) else
                                 rules["min_gap_descender_ratio"] * (top.get("fontSize") or 0))
                if line <= 0 or visible >= rules["min_gap_ratio"] * line:
                    continue
                if (top.get("fontSize") or 0) < rules["min_gap_title_size"]:
                    continue
                if (bot.get("fontSize") or 0) > rules["min_gap_meta_size"]:
                    continue
                bx0, by0, bx1, by1 = ink_box(bot)
                seps = [r for r in inside
                        if r["type"] == "rectangle" and (r["h"] or 0) <= 2
                        and (r["w"] or 0) >= rules["fit_rule_min"]
                        and r.get("parentId") == bot.get("parentId")
                        and 6 <= r["y"] - by1 <= 48
                        and min(bx1, r["x"] + r["w"]) - max(bx0, r["x"]) > 0.5 * (bx1 - bx0)]
                if not seps:
                    continue
                level = "high" if visible < rules["min_gap_high_ratio"] * line else "medium"
                add(level, f"text {top['name']} / {bot['name']} ink gap {gap:.0f}px "
                           f"under {rules['min_gap_ratio']:.2f}x line ({line:.0f}px) — title and meta touch")

        # 10. list marker: a bullet/dot belongs on the line's ink centre, and
        # the separator starts at the marker's left edge. A dot at row+6 sits
        # 2-4px high; the rule below it drifts left/right.
        markers = [n for n in inside
                   if n["type"] in ("rectangle", "ellipse", "circle")
                   and 2 <= (n["w"] or 0) <= 10 and 2 <= (n["h"] or 0) <= 10
                   and (n.get("fill") or n.get("img"))]
        for dot in markers:
            dcy = dot["y"] + (dot["h"] or 0) / 2
            mates = []
            for t in inked:
                if t.get("parentId") != dot.get("parentId"):
                    continue
                ix0, iy0, ix1, iy1 = ink_box(t)
                if ix0 < dot["x"] + (dot["w"] or 0) - 2:
                    continue
                line = (t.get("fontSize") or 0) * (line_height_multiplier(t.get("lineHeight")) or 1.5)
                if line <= 0:
                    continue
                centre = iy0 + min(iy1 - iy0, line) / 2
                if abs(centre - dcy) > 0.9 * line:
                    continue
                if ix0 - (dot["x"] + (dot["w"] or 0)) > 40:
                    continue
                mates.append((abs(centre - dcy), t, centre))
            if not mates:
                continue
            diff, mate, centre = min(mates)
            if diff > rules["marker_centre_tol"]:
                add("high", f"list marker {dot['name']} centre {dcy:.1f}px vs "
                            f"{mate['name']} line centre {centre:.1f}px (Δ{diff:.1f}px)")
                continue
            expected = min(dot["x"], ink_box(mate)[0])
            for r in inside:
                if (r["type"] != "rectangle" or (r["h"] or 0) > 2
                        or (r["w"] or 0) < rules["fit_rule_min"]
                        or r.get("parentId") != dot.get("parentId")):
                    continue
                if not (ink_box(mate)[3] < r["y"] <= ink_box(mate)[3] + 64):
                    continue
                if abs(r["x"] - expected) > rules["marker_rule_gap"]:
                    continue
                if abs(r["x"] - expected) > rules["marker_rule_tol"]:
                    add("medium", f"list separator {r['name']} starts at x={r['x']:.0f}, "
                                  f"expected {expected:.0f} from {dot['name']}")
                break

        # 11. surface role: cards are white, surface.alt is for insets. A grid
        # of alt cards beside a white card (13-kilavuzlar pockets) and a large
        # alt card on a page of white cards (20-panel ecg) are one defect.
        white = {value.upper() for value in rules["surface_white"]}
        alt = {value.upper() for value in rules["surface_alt"]}

        def surface_role(n):
            fill = (n.get("fill") or "").upper()
            if fill in white:
                return "white"
            if fill in alt:
                return "alt"
            return None

        cards = []
        for n in inside:
            if n["type"] not in ("rectangle", "board") or n["id"] == board["id"]:
                continue
            if n.get("img") or not surface_role(n):
                continue
            width, height = n["w"] or 0, n["h"] or 0
            if width < rules["surface_card_min_w"] or height < rules["surface_card_min_h"]:
                continue
            if width >= 0.9 * board["w"]:
                continue
            if n["x"] <= board["x"] + 1 or n["x"] + width >= board["x"] + board["w"] - 1:
                continue
            if not any(t["id"] == n["id"] or is_ancestor(n["id"], t["id"]) for t in inked):
                continue
            cards.append(n)
        for i, a in enumerate(cards):
            for b in cards[i + 1:]:
                if a.get("parentId") != b.get("parentId"):
                    continue
                if (abs((a["w"] or 0) - (b["w"] or 0)) <= max(8, 0.08 * (a["w"] or 0))
                        and abs((a["h"] or 0) - (b["h"] or 0)) <= max(8, 0.08 * (a["h"] or 0))
                        and surface_role(a) != surface_role(b)):
                    add("medium", f"same-size cards {a['name']} ({surface_role(a)}) and "
                                   f"{b['name']} ({surface_role(b)}) use different surface tokens")
        by_parent_cards: dict[str, list[dict]] = {}
        for c in cards:
            by_parent_cards.setdefault(c.get("parentId") or "", []).append(c)
        for group in by_parent_cards.values():
            alt_cards = [c for c in group if surface_role(c) == "alt"]
            if not alt_cards or not any(surface_role(c) == "white" for c in group):
                continue
            for i, a in enumerate(alt_cards):
                mates = [b for b in alt_cards[i + 1:]
                         if abs((a["w"] or 0) - (b["w"] or 0)) <= max(8, 0.08 * (a["w"] or 0))
                         and abs((a["h"] or 0) - (b["h"] or 0)) <= max(8, 0.08 * (a["h"] or 0))]
                if mates:
                    add("medium", f"{1 + len(mates)} same-size cards in {a.get('parent')} use "
                                   f"surface.alt beside a white card — card surface is white; "
                                   f"alt is for insets")
                    break
        large_alt = [c for c in cards if surface_role(c) == "alt"
                     and (c["w"] or 0) >= rules["surface_alt_min_w"]
                     and (c["w"] or 0) < rules["surface_band_ratio"] * board["w"]]
        if large_alt and any(surface_role(c) == "white" for c in cards):
            card = large_alt[0]
            add("medium", f"large surface.alt card {card['name']} "
                           f"({card['w']:.0f}x{card['h']:.0f}x) sits with white cards on the same "
                           f"board — alt is for insets, not cards")

        # 12. floating sibling: a link and a button in one CTA row share a
        # centre line. The 01 kongre band put "Programı gör" 63px above the
        # "Kayıt ol" button (different parents, no x-overlap), so the gap read
        # as two unrelated actions.
        buttons = [n for n in inside
                   if n["type"] in ("rectangle", "board")
                   and rules["float_btn_min_w"] <= (n["w"] or 0) <= rules["float_btn_max_w"]
                   and 24 <= (n["h"] or 0) <= 88
                   and any(c.get("parentId") == n["id"] and c["type"] == "text"
                           and "/ label" in (c["name"] or "") for c in inside)]
        links = []
        for t in inked:
            name = (t["name"] or "").lower()
            is_link = any(k in name for k in ("link", "cta", "under"))
            if not is_link:
                is_link = any(
                    s["type"] == "rectangle" and s.get("parentId") == t.get("parentId")
                    and (s["h"] or 0) <= 2 and (s["w"] or 0) >= 20
                    and abs(s["y"] - (t["y"] + (t["h"] or 0) + 2)) <= 8
                    and abs(s["x"] - t["x"]) <= 4
                    for s in inside
                )
            if is_link:
                links.append(t)
        for button in buttons:
            bcy = button["y"] + (button["h"] or 0) / 2
            for link in links:
                if link.get("parentId") != button.get("parentId"):
                    continue
                ix0, iy0, ix1, iy1 = ink_box(link)
                if min(button["x"] + (button["w"] or 0), ix1) - max(button["x"], ix0) > 0:
                    continue
                hgap = max(0, max(button["x"], ix0) - min(button["x"] + (button["w"] or 0), ix1))
                if hgap > rules["float_max_gap"]:
                    continue
                diff = abs((iy0 + iy1) / 2 - bcy)
                if diff <= rules["float_centre_tol"] or diff > rules["float_max_centre_diff"]:
                    continue
                row0 = min(iy0, button["y"]) - 8
                row1 = max(iy1, button["y"] + (button["h"] or 0)) + 8
                gap0 = min(button["x"] + (button["w"] or 0), ix1)
                gap1 = max(button["x"], ix0)
                blocked = any(
                    n["id"] not in (button["id"], link["id"])
                    and n["type"] in ("rectangle", "board", "text")
                    and (n.get("fill") or n.get("img"))
                    and n["x"] < gap1 and n["x"] + (n["w"] or 0) > gap0
                    and n["y"] < row1 and n["y"] + (n["h"] or 0) > row0
                    and not is_ancestor(n["id"], button["id"])
                    and not is_ancestor(n["id"], link["id"])
                    for n in inside
                )
                if blocked:
                    continue
                level = "high" if diff > rules["float_high_centre_diff"] else "medium"
                add(level, f"CTA group misaligned: {link['name']} centre {((iy0 + iy1) / 2):.0f}px "
                           f"vs {button['name']} centre {bcy:.0f}px (Δ{diff:.0f}px) — link and "
                           f"button should share a centre line")

        # 13. stat size: a stats row's number is display type, not body copy.
        # 01's dark proof band ran 16px values against 13px labels; the
        # threshold lives in DEFAULTS so a project can declare a smaller grid.
        def numeric(t):
            value = (t.get("text") or "").strip()
            if not value or len(value) > 16:
                return False
            digits = sum(ch.isdigit() for ch in value)
            return digits >= 1 and digits / len(value) >= 0.4

        stat_values = []
        for t in texts:
            if not numeric(t):
                continue
            for label in texts:
                if (label["id"] == t["id"] or label.get("parentId") != t.get("parentId")
                        or numeric(label) or (label.get("fontSize") or 0) >= (t.get("fontSize") or 0)):
                    continue
                if abs((label.get("inkX") or label["x"]) - (t.get("inkX") or t["x"])) > 6:
                    continue
                below = (label.get("inkY") or label["y"]) - ((t.get("inkY") or t["y"]) + (t.get("inkH") or t["h"]))
                if 0 < below <= 60:
                    stat_values.append(t)
                    break
        stat_rows: dict[tuple, list[dict]] = {}
        for t in stat_values:
            stat_rows.setdefault((t.get("parentId"), round(t["y"] / 8)), []).append(t)
        for group in stat_rows.values():
            if len(group) < 2:
                continue
            small = [t for t in group if (t.get("fontSize") or 0) < rules["min_stat_size"]]
            if small:
                value = min(small, key=lambda t: t["fontSize"] or 0)
                add("medium", f"stats row in {group[0].get('parent')}: {value['name']} is "
                               f"{value['fontSize']}px under the {rules['min_stat_size']}px stat "
                               f"minimum ({len(group)} values)")

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
