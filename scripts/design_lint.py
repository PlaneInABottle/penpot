#!/usr/bin/env python3
"""Mechanical craft checks for a Penpot page.

    design_lint.py --page <page>
    design_lint.py --page <page> --rules design/<project>/craft-rules.json --json /tmp/lint.json

Complements design_qa.py: that one checks wiring (token coverage, render truth, hygiene),
this one checks craft thresholds — type scale, rhythm, accent count, alignment axes,
radius, shadows, overflow, placeholder copy. Thresholds are the defaults below and can be
overridden per project with `--rules` (a flat JSON of the same keys).

    design_lint.py --from-nodes /tmp/lint-corpus/Üyelik.nodes.json --rules design/ihkd/craft-rules.json

`--from-nodes` lints a frozen `--dump-nodes` file and never touches the plugin:
the before/after comparison of a rule change, the regression museum and the
corpus triage all run offline on one snapshot, so a live edit cannot move the
number a claim rests on.

Exit codes: 0 no high findings, 1 high findings, 2 environment or transport, or a
page whose texts have no measured ink (not the open page — findings are invalid).
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
    # No palette is shipped: a project declares its own surface hexes in
    # craft-rules.json (`surface_white`, `surface_alt`). A default here would
    # silently skip another project's alt surface and let the rule look green.
    "surface_white": [],
    "surface_alt": [],  # inset/side-panel surface, never a card grid
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
    "dead_pad_tol": 8.0,         # trailing void within this of the entry inset is padding
}

def palette_problems(rules: dict) -> list[str]:
    """Reject a surface palette the rule cannot read.

    `surface.role` compares hex strings against the project's declared surfaces.
    A scalar (`"surface_white": "#FFFFFF"`) iterates as characters, so no shape
    ever matches and the rule reports nothing — a silent false PASS that hid the
    project palette for a whole milestone (2026-11-03). A non-list or a non-string
    entry is a configuration error, not a finding. An empty list stays legal: the
    rule is then unconfigured and says so out loud.
    """
    problems: list[str] = []
    for field in ("surface_white", "surface_alt"):
        value = rules.get(field, [])
        if not isinstance(value, list):
            problems.append(f"{field} must be a list of hex strings, got {type(value).__name__} "
                            f"({value!r}) — a scalar silently disables surface.role")
        elif not all(isinstance(entry, str) for entry in value):
            problems.append(f"{field} must contain only hex strings, got {value!r}")
    return problems


BANNED_EXACT = {"Text", "Rectangle", "Board", "Group"}

# Above this share of unmeasured texts the page was never laid out: `textBounds`
# is null for every text on a page that is not open, so the ink rules skip them
# (`inks` / `inkW` are filtered out) and the run reports "0 high" for a page it
# never measured. That silent false PASS is a defective lint, not a clean page.
INK_NULL_MAX_RATIO = 0.05


# ---- rule registry: every rule carries its evidence record ----
# severity is the GATE level: HIGH breaks the build and is reserved for classes
# that are proven by the museum (a fixture that fails without the rule) and
# produced no wrong positive on the frozen 5-page corpus; MEDIUM is reported and
# never breaks the gate; LOW is hidden from the default output (`--verbose`
# shows it) because its live hits are declared design decisions.
# corpus = tp / fp / ok counted by eye on design/ihkd/lint-corpus (2026-11-02,
# 5 pages, 2 852 shapes): tp a real defect, fp a rule that fired on a clean
# screen, ok a finding that is a recorded design decision. `--rules-report`
# prints the table.
# born_from names the fixture or session note the rule came from; a rule with no
# real catch does not get one (it is retired, not kept).
RULES: dict[str, dict] = {
    "board.width": {
        "severity": "medium",
        "born_from": "fixture: boards are 1440/390 (build SCREENS)",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "type.sizes": {
        "severity": "high",
        "born_from": "fixture: the 13->16->30 scale; 6 sizes is the ceiling",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "type.display": {
        "severity": "high",
        "born_from": "fixture: a display only 1.5x the body has no scale drama",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "type.dominant": {
        "severity": "high",
        "born_from": "session: a page opening with a 13px kicker and no display type",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "type.steps": {
        "severity": "medium",
        "born_from": "fixture: 13->16 is this project's declared 1.2 step",
        "corpus": {"tp": 0, "fp": 0, "ok": 20}},
    "type.small_body": {
        "severity": "low",
        "born_from": "fixture: a 12px paragraph reads as fine print; corpus tp = 09-kayit FAQ answers",
        "corpus": {"tp": 3, "fp": 0, "ok": 78}},
    "type.leading": {
        "severity": "medium",
        "born_from": "fixture: display type set at 1.5 loses its block",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "type.measure": {
        "severity": "low",
        "born_from": "fixture: a 120-char line at 16px",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "accent.hues": {
        "severity": "high",
        "born_from": "fixture: one accent hue per board (İHKD red)",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "radius.scale": {
        "severity": "low",
        "born_from": "fixture: radius outside the declared scale",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "shadow.present": {
        "severity": "medium",
        "born_from": "fixture: a card shadow instead of a hairline",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "board.overflow": {
        "severity": "high",
        "born_from": "test_penpot_scripts: shape past the frame edge",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "type.uppercase": {
        "severity": "medium",
        "born_from": "fixture: tracked-caps as decoration above 35% of texts",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "inline.baseline": {
        "severity": "retired",
        "born_from": "retired 2026-11-02: flagged every mixed-size row (23/23 corpus hits read clean at 1:1)",
        "corpus": {"tp": 0, "fp": 23, "ok": 0}},
    "text.overlap": {
        "severity": "high",
        "born_from": "session: İHKD 01 hero caption / red label crash",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "text.on_control": {
        "severity": "high",
        "born_from": "session: DAHİL / 'Devam et' overlap on a saturated pill",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "text.paint_over": {
        "severity": "high",
        "born_from": "session: hero title slid 14px under its photo on a copy edit",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "copy.placeholder": {
        "severity": "high",
        "born_from": "fixture: lorem/TODO/Text left in the design",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "text.unlaid": {
        "severity": "high",
        "born_from": "session: a 1x1 text box paints nothing and the exporter clips it",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "panel.padding": {
        "severity": "medium",
        "born_from": "session: İHKD 04 propose card with 0px padding",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "text.collision": {
        "severity": "medium",
        "born_from": "session: two texts sharing ink between cards",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "fit.box": {
        "severity": "high",
        "born_from": "fixture: a 500px text box inside a 400px card",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "fit.no_container": {
        "severity": "medium",
        "born_from": "fixture: a text with no enclosing slot",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "fit.container": {
        "severity": "high",
        "born_from": "session: 07-program schedule meta crossing its row",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "fit.sibling": {
        "severity": "high",
        "born_from": "session: ink entering the next slot of a card grid",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "fit.rule": {
        "severity": "high",
        "born_from": "session: 07-program meta painting over row rules",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "fit.band": {
        "severity": "high",
        "born_from": "session: İHKD 01 journal meta 12px past its 300px band",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "fit.bar": {
        "severity": "medium",
        "born_from": "fixture: accent bar shorter than the column beside it",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "surface.touch": {
        "severity": "medium",
        "born_from": "fixture: a photo glued to its card edge with a 0px joint",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "dead_space": {
        "severity": "medium",
        "born_from": "fixture: card text stopping 80px above its own bottom edge; 3/4 live hits were symmetric padding, so the rule now exempts a void within dead_pad_tol of the entry inset",
        "corpus": {"tp": 0, "fp": 0, "ok": 4}},
    "gap.intra_card": {
        "severity": "medium",
        "born_from": "session: 20-panel aidat title/meta drifting 36px apart",
        "corpus": {"tp": 2, "fp": 0, "ok": 2}},
    "corridor.empty": {
        "severity": "high",
        "born_from": "session: a 96px strip with no content reads as a missing row",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "gap.min": {
        "severity": "high",
        "born_from": "session: İHKD 01 group rows 5px apart / 1.9px bullet drop",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "marker.centre": {
        "severity": "high",
        "born_from": "fixture: bullets dot 2-4px above the line's ink centre",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "marker.rule": {
        "severity": "medium",
        "born_from": "fixture: list separator drifting from the marker's left edge",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "surface.role": {
        "severity": "medium",
        "born_from": "session: 13-kilavuzlar alt cards beside white / 20-panel ECG card",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "cta.float": {
        "severity": "high",
        "born_from": "session: 01 kongre 'Programı gör' 63px above its button",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
    "stat.size": {
        "severity": "medium",
        "born_from": "session: 01 dark proof band ran 16px values against 13px labels",
        "corpus": {"tp": 0, "fp": 0, "ok": 0}},
}

LOW_SEVERITIES = {"low"}


def ink_unavailable(nodes: list[dict]) -> tuple[int, int]:
    """(measurable texts without ink bounds, measurable texts).

    A text with no characters carries no ink by definition and is not counted;
    a text with copy but no `textBounds` on an open page is a font problem
    (mcp-failures row 17), which the same signal reports.
    """
    measurable = [n for n in nodes if n.get("type") == "text" and (n.get("text") or "").strip()]
    missing = [n for n in measurable if n.get("inkW") is None or n.get("inkH") is None]
    return len(missing), len(measurable)


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


def rules_report() -> str:
    """The registry as a table: id, severity, born_from, live-corpus tp/fp/ok."""
    lines = [f"{'rule':<20}{'sev':<9}{'tp':>3}{'fp':>3}{'ok':>4}  born_from"]
    for rule_id in sorted(RULES):
        entry = RULES[rule_id]
        corpus = entry["corpus"]
        lines.append(f"{rule_id:<20}{entry['severity']:<9}{corpus['tp']:>3}{corpus['fp']:>3}"
                     f"{corpus['ok']:>4}  {entry['born_from']}")
    return "\n".join(lines)


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


def family(name: str | None) -> str:
    """A shape's instance family: 'sess meta 18' -> 'sess meta'.

    One cause repeated per row (19 session metas, 18 footers) is one finding:
    grouping by this key keeps the count and drops the 18 extra lines.
    """
    text = re.sub(r"\s+\d+$", "", str(name or "").strip())
    return text or "?"


def _match_ack(group: dict, acks: list[dict]) -> dict | None:
    for entry in acks:
        if str(entry.get("rule") or "") not in (group["rule"], "*"):
            continue
        board = entry.get("board")
        if board and board not in group["boards"]:
            continue
        prefix = entry.get("shape-prefix")
        if prefix and not any(str(name).startswith(prefix) for name in group["instances"]):
            continue
        return entry
    return None


def group_findings(findings: list[dict], rules: dict) -> list[dict]:
    """Collapse same-cause findings into one entry with count + instances.

    An `acknowledge` entry in the project's craft-rules.json marks a group as a
    recorded design decision: it stays in the output and in the JSON, counted
    apart, and only the unexplained medium count is watched.
    """
    raw = rules.get("acknowledge") or []
    acks = []
    for entry in raw:
        if isinstance(entry, dict) and str(entry.get("reason") or "").strip():
            acks.append(entry)
        else:
            print(f"warning: craft-rules acknowledge entry without a reason is ignored: {entry}",
                  file=sys.stderr)
    order: list[tuple] = []
    groups: dict[tuple, dict] = {}
    for finding in findings:
        key = (finding["rule"], finding["group"], finding["severity"])
        group = groups.get(key)
        if group is None:
            group = dict(finding)
            group.update({"count": 0, "instances": [], "boards": []})
            groups[key] = group
            order.append(key)
        group["count"] += 1
        instance = finding.get("shape") or finding["board"]
        if instance not in group["instances"]:
            group["instances"].append(instance)
        if finding["board"] not in group["boards"]:
            group["boards"].append(finding["board"])
    out = []
    for key in order:
        group = groups[key]
        ack = _match_ack(group, acks)
        group["acknowledged"] = bool(ack)
        group["ack_reason"] = (ack or {}).get("reason")
        # the first board names the group; a cross-board group keeps the list
        group["board"] = group["boards"][0] if len(group["boards"]) == 1 else f"{len(group['boards'])} boards"
        out.append(group)
    return out


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

        def add(rule_id: str, message: str, group: str | None = None,
                level: str | None = None, shape: str | None = None) -> None:
            entry = RULES.get(rule_id)
            if entry is None or entry["severity"] == "retired":
                raise KeyError(f"unregistered or retired rule: {rule_id}")
            findings.append({
                "rule": rule_id,
                "board": region,
                "severity": level or entry["severity"],
                "finding": message,
                "group": group or family(shape),
                "shape": shape,
            })

        inside = subtree(board["id"])
        by_id = {n["id"]: n for n in inside}
        if int(board["w"]) not in rules["board_widths"]:
            add("board.width", f"board width {board['w']:.0f} is not one of {rules['board_widths']} → set the frame to a declared width")

        texts = [n for n in inside if n["type"] == "text" and n["fontSize"]]
        sizes = sorted({n["fontSize"] for n in texts})
        if len(sizes) > rules["max_type_sizes"]:
            add("type.sizes", f"{len(sizes)} distinct type sizes (max {rules['max_type_sizes']}): {sizes} → collapse to one display, one body, one meta")
        if sizes:
            chrome = rules["dominant_ignore_prefix"] or []
            pool = [n for n in texts if not any(n["name"].startswith(c) for c in chrome)] or texts
            top_size = max(n["fontSize"] for n in pool)
            topmost = min((n for n in pool if n["fontSize"] == top_size), key=lambda n: n["y"])
            offset = topmost["y"] - board["y"]
            if offset > 900:
                add("type.dominant", f"largest type ({topmost['fontSize']}px, {topmost['name']}) starts at y={offset:.0f} — the page opens without a dominant element → move the display above y=900", shape=topmost["name"])
            counts = {size: sum(1 for n in texts if n["fontSize"] == size) for size in sizes}
            body = max(counts, key=counts.get)
            if sizes[-1] / body < rules["min_display_ratio"]:
                # A chrome sheet (menu, overlay) may carry no display step at
                # all; the project can name it in `type_display_exempt`. The
                # skip is printed, so an exemption is visible, never silent.
                exempt = rules.get("type_display_exempt") or []
                if isinstance(exempt, str):
                    exempt = [exempt]
                if board["name"] in exempt:
                    print(f"note: type.display skipped for {board['name']} "
                          f"({sizes[-1] / body:.2f}x display {sizes[-1]}px over body {body}px) "
                          f"— declared in type_display_exempt")
                else:
                    add(
                        "type.display",
                        f"display {sizes[-1]}px is only {sizes[-1] / body:.2f}x the body {body}px "
                        f"(min {rules['min_display_ratio']}x) — no scale drama → push the display to "
                        f"{body * rules['min_display_ratio']:.0f}px or drop to one size",
                    )
            if len(sizes) > 1:
                gaps = [b / a for a, b in zip(sizes, sizes[1:])]
                if min(gaps) < rules["min_step_ratio"]:
                    add("type.steps", f"type steps too close: {[round(g, 2) for g in gaps]} → widen to ≥{rules['min_step_ratio']}× or drop the redundant size")

        for node in texts:
            if node["fontSize"] < rules["min_body_size"] and len(node["text"] or "") > 40:
                add("type.small_body",
                    f"small paragraph at {node['fontSize']}px: {node['name']} "
                    f"({len(node['text'] or '')} chars at {node['fontSize']:.0f}px against a "
                    f"{rules['min_body_size']}px body) — content copy under the body size reads as "
                    f"fine print; meta is for captions and legal",
                    shape=node["name"])
            multiplier = line_height_multiplier(node["lineHeight"])
            if multiplier and node["fontSize"] >= 40 and multiplier > 1.25:
                add("type.leading", f"{node['name']}: {node['fontSize']:.0f}px at line-height {multiplier} → display type wants 1.0-1.2", shape=node["name"])
            if node["w"] and node["fontSize"]:
                measure = len(node["text"] or "") / max(node["w"] / (node["fontSize"] * 0.5), 0.1)
                if 14 <= node["fontSize"] <= 20 and len(node["text"] or "") > 120 and measure > rules["max_measure_chars"]:
                    add("type.measure", f"{node['name']}: ~{measure:.0f} characters per line (max {rules['max_measure_chars']}) → narrow the box", shape=node["name"])

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
            add("accent.hues", f"{len(accents)} saturated accent hues (max {rules['max_accents']}): {sorted(accents.values())} → keep one accent hue per board")

        bad_radius = {
            n["radius"] for n in inside
            if isinstance(n["radius"], (int, float))
            and n["radius"] not in rules["allowed_radii"]
            and abs(n["radius"] * 2 - n["h"]) > 1  # a full pill/circle is fine at any size
        }
        if bad_radius:
            add("radius.scale", f"radius values outside the scale: {sorted(bad_radius)} → use {rules['allowed_radii']}")

        shadows = [n["name"] for n in inside if n["shadows"]]
        if shadows:
            add("shadow.present", f"{len(shadows)} shape(s) with a shadow: {shadows[:3]} → use a hairline or the alt surface, not a shadow")

        bx, by = board["x"], board["y"]
        for node in inside:
            left, top = node["x"] - bx, node["y"] - by
            if left < -0.5 or top < -0.5 or left + node["w"] > board["w"] + 0.5 or top + node["h"] > board["h"] + 0.5:
                add("board.overflow", f"{node['name']} overflows the board (x={left:.0f} y={top:.0f} w={node['w']:.0f} h={node['h']:.0f}) → move or resize it inside the {board['w']:.0f}px frame", shape=node["name"])
                break

        uppercase = [n for n in texts if (n["text"] or "").strip() and (n["text"] or "") == (n["text"] or "").upper() and len((n["text"] or "").strip()) > 3]
        if texts and len(uppercase) / len(texts) > rules["max_uppercase_ratio"]:
            add("type.uppercase", f"{len(uppercase)}/{len(texts)} text nodes are uppercase-tracked (ceiling {rules['max_uppercase_ratio']}) → sentence-case some labels")

        # retired: the inline mixed-size prompt flagged every 13/16 or 13/30 row
        # (23/23 corpus hits read clean at 1:1), so it was a to-do list, not a
        # defect. The class belongs to the 1:1 tile review in the gate; see
        # RULES["inline.baseline"] for the retirement record.
        inks = [n for n in inside if n["type"] == "text" and n["inkW"] and n["inkH"] and n["inkW"] > 1]

        # text must not overlap text: ink rectangles come from textBounds (page-absolute)
        for i in range(len(inks)):
            for j in range(i + 1, len(inks)):
                a, b = inks[i], inks[j]
                ox = min(a["inkX"] + a["inkW"], b["inkX"] + b["inkW"]) - max(a["inkX"], b["inkX"])
                oy = min(a["inkY"] + a["inkH"], b["inkY"] + b["inkH"]) - max(a["inkY"], b["inkY"])
                if ox > 30 and oy > 12:
                    add("text.overlap", f"text overlap {a['name']} / {b['name']} ({ox:.0f}x{oy:.0f}px) → two texts cannot share ink; reflow the row", shape=a["name"])

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
                    add("text.on_control", f"text {t['name']} sits on sibling control {n['name']} "
                               f"(ink fully inside {n['w']:.0f}x{n['h']:.0f}px solid) → move the label "
                               f"off the control or inside it", shape=t["name"])
                    break
                add("text.paint_over", f"text {t['name']} paints over shape {n['name']} ({ox:.0f}x{oy:.0f}px ink overlap) → move the text or the shape", shape=t["name"])
                break

        for node in texts:
            blob = (node["text"] or "").lower()
            if any(word in blob for word in rules["banned_text"]) or (node["text"] or "").strip() in BANNED_EXACT:
                add("copy.placeholder", f"placeholder copy in {node['name']}: {node['text'][:40]!r} → write the real copy", shape=node["name"])

        # a text that never laid out (1x1 box with copy) paints nothing:
        # the exporter clips to the box, so an unmeasured label is an
        # invisible label. Layout that never commits is a build defect —
        # seed an estimated box at build time and refit — not a timing
        # artifact worth waiting out.
        for node in texts:
            if (node["w"] or 0) <= 2 and (node["h"] or 0) <= 2 and (node["text"] or "").strip():
                add("text.unlaid", f"text {node['name']} has an unlaid-out box "
                             f"({node['w']:.0f}x{node['h']:.0f}px) — refit, then re-export",
                    shape=node["name"])

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
                add("panel.padding", f"{t['name']}: ink starts {ink_l - panel['x']:.0f}px inside {panel['name']} — panel padding under {rules['min_card_padding']}px → inset to {rules['min_card_padding']}px or drop the panel", shape=t["name"])

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
                    add("text.collision", f"text {a['name']} collides with text {b['name']} ({ox:.0f}x{oy:.0f}px ink overlap) → give one of them its own line", shape=a["name"])

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
                    add("fit.box", f"text {t['name']} box ({rx - lx:.0f}x{by - ty:.0f}) exceeds its "
                                f"container {parent_slot['name']} ({', '.join(box_over)} outside) → "
                                f"widen {parent_slot['name']} or shrink the box", shape=t["name"])
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
                    add("fit.no_container", f"text {t['name']} has no enclosing container "
                                  f"(box {rx - lx:.0f}x{by - ty:.0f} at x={lx:.0f} y={ty:.0f}) → "
                                  f"wrap it in a slot or move it inside the grid", shape=t["name"])
                    continue
            ix, iy, ir, ib = ink_box(t)
            over = overflow_text(slot, ix, iy, ir, ib)
            if over:
                add("fit.container", f"text {t['name']} overflows its container {slot['name']} ({', '.join(over)} ink outside) → widen {slot['name']} or wrap the text", shape=t["name"])

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
                add("fit.sibling", f"text {t['name']} enters sibling container {s['name']} ({ox:.0f}x{oy:.0f}px ink inside) → keep the text inside its own slot", shape=t["name"])
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
                        add("fit.rule", f"text {t['name']} crosses rule {r['name']} (ink {iy:.0f}-{ib:.0f}px over line y={ry:.0f}) → move it above or below the rule", shape=t["name"])
                        break
                else:
                    rx = r["x"] + (r["w"] or 0) / 2
                    run = min(ib, r["y"] + r["h"]) - max(iy, r["y"])
                    if ix < rx - tol and ir > rx + tol and run > 8:
                        add("fit.rule", f"text {t['name']} crosses rule {r['name']} (ink {ix:.0f}-{ir:.0f}px over line x={rx:.0f}) → move it left or right of the rule", shape=t["name"])
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
                    add("fit.band", f"text {t['name']} runs {over:.0f}px past its "
                                f"{r['w']:.0f}px column band ({r['name']}) → shorten the text or "
                                f"widen the band to {r['w'] + over:.0f}px", shape=t["name"])
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
                add("fit.bar", f"bar {bar['name']} h={bar['h']:.0f}px vs content span {bot - top:.0f}px "
                              f"(Δ{abs(bar['h'] - (bot - top)):.0f}px over {rules['fit_bar_delta']:.0f}px) → "
                              f"match the bar to {bot - top:.0f}px", shape=bar["name"])

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
                        add("surface.touch", f"{a['name']} touches {b['name']} "
                                     f"({vgap:.0f}px gap, different surfaces) — a glued joint reads as a leak → "
                                     f"separate to ≥{touch_gap:.0f}px or unify the fills", shape=a["name"])
                        continue
                if a["x"] <= b["x"]:
                    hgap = b["x"] - (a["x"] + a["w"])
                else:
                    hgap = a["x"] - (b["x"] + b["w"])
                if 0 <= hgap < touch_gap:
                    run = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
                    if run >= touch_run:
                        add("surface.touch", f"{a['name']} touches {b['name']} "
                                     f"({hgap:.0f}px gap, different surfaces) — a glued joint reads as a leak → "
                                     f"separate to ≥{touch_gap:.0f}px or unify the fills", shape=a["name"])

        # 6. dead space: a card/panel whose content ends far above its own
        # bottom edge reads as a leak, not air. Trailing void (container
        # bottom minus last descendant ink bottom) beyond dead_med — and
        # beyond 1.5x the largest contained line height, so display type
        # is not punished — is MEDIUM; beyond dead_high is HIGH. A void that
        # matches the container's own entry inset is padding and stays clean.
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
            # symmetric padding is the container's inset, not dead space: a
            # 74px band pad over an 80px entry, a 46px sheet pad over 47px, a
            # 52px article pad over 55px all read balanced at 1:1 (corpus
            # 2026-11-02: 3 of 4 hits). Only a void that dwarfs the entry inset
            # is a leak.
            lead = min(ink_box(t)[1] for t in desc) - c["y"]
            symmetric = abs(trailing - lead) <= rules["dead_pad_tol"]
            if trailing > dead_med and trailing > 1.5 * max(lines or [0]) and not symmetric:
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
                add("dead_space", f"dead space in {c['name']}: {trailing:.0f}px below the last ink "
                           f"(content ends, card continues) → trim the card to the content or push "
                           f"the last block down", level=level, shape=c["name"])

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
                    add("gap.intra_card", f"intra-card gap in {c['name']}: {a['name']} / {b['name']} "
                                   f"({gap:.0f}px between stacked texts, ceiling {1.5 * line:.0f}px) → "
                                   f"pull the pair together or add the divider it belongs to",
                                   shape=c["name"])

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
            add("corridor.empty", f"empty corridor {e2 - e1:.0f}px (y {e1:.0f}-{e2:.0f}px): "
                        f"no content, no divider — reads as a missing row → add the row's content "
                        f"or remove the strip")

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
                add("gap.min", f"text {top['name']} / {bot['name']} ink gap {gap:.0f}px "
                           f"under {rules['min_gap_ratio']:.2f}x line ({line:.0f}px) — title and meta "
                           f"touch → open the gap to {rules['min_gap_ratio'] * line:.0f}px or drop "
                           f"the meta", level=level, shape=bot["name"])

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
                add("marker.centre", f"list marker {dot['name']} centre {dcy:.1f}px vs "
                            f"{mate['name']} line centre {centre:.1f}px (Δ{diff:.1f}px) → "
                            f"centre the dot on the line", shape=dot["name"])
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
                    add("marker.rule", f"list separator {r['name']} starts at x={r['x']:.0f}, "
                                  f"expected {expected:.0f} from {dot['name']} → align the separator "
                                  f"with the marker", shape=r["name"])
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
                    add("surface.role", f"same-size cards {a['name']} ({surface_role(a)}) and "
                                   f"{b['name']} ({surface_role(b)}) use different surface tokens → "
                                   f"card surface is white; alt is for insets",
                                   group="same-size cards", shape=a["name"])
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
                    add("surface.role", f"{1 + len(mates)} same-size cards in {a.get('parent')} use "
                                   f"surface.alt beside a white card — card surface is white; "
                                   f"alt is for insets → swap the alt cards to white",
                                   group="alt grid", shape=a.get("parent") or a["name"])
                    break
        large_alt = [c for c in cards if surface_role(c) == "alt"
                     and (c["w"] or 0) >= rules["surface_alt_min_w"]
                     and (c["w"] or 0) < rules["surface_band_ratio"] * board["w"]]
        if large_alt and any(surface_role(c) == "white" for c in cards):
            card = large_alt[0]
            add("surface.role", f"large surface.alt card {card['name']} "
                           f"({card['w']:.0f}x{card['h']:.0f}x) sits with white cards on the same "
                           f"board — alt is for insets, not cards → swap it to white",
                           group="large alt card", shape=card["name"])

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
                add("cta.float", f"CTA group misaligned: {link['name']} centre {((iy0 + iy1) / 2):.0f}px "
                           f"vs {button['name']} centre {bcy:.0f}px (Δ{diff:.0f}px) — link and "
                           f"button should share a centre line → move the link "
                           f"{(bcy - (iy0 + iy1) / 2):+.0f}px", level=level, shape=link["name"])

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
                add("stat.size", f"stats row in {group[0].get('parent')}: {value['name']} is "
                               f"{value['fontSize']}px under the {rules['min_stat_size']}px stat "
                               f"minimum ({len(group)} values) → set the value to "
                               f"{rules['min_stat_size']:.0f}px or drop the stat framing",
                               shape=value["name"])

    return group_findings(findings, rules)


def collect(page: str) -> list[dict]:
    """Live geometry from the plugin (read-only; the page must be open)."""
    try:
        url = load_url()
        ensure_helpers(url, write=False)
        nodes = payload(call_execute_code(url, COLLECT.replace("__PAGE__", json.dumps(page)), write=False))
    except McpError as exc:
        fail(str(exc))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        fail(f"{type(exc).__name__}: {exc}")
    if not isinstance(nodes, list):
        fail("collector returned no node list")
    return nodes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--page", help="page to lint live (required unless --from-nodes)")
    parser.add_argument("--from-nodes", type=pathlib.Path,
                        help="lint a frozen --dump-nodes file offline; no plugin call")
    parser.add_argument("--rules", type=pathlib.Path)
    parser.add_argument("--json", type=pathlib.Path)
    parser.add_argument("--dump-nodes", type=pathlib.Path,
                        help="write the raw geometry collector output for rhythm.py")
    parser.add_argument("--rules-report", action="store_true",
                        help="print the rule registry (severity, born_from, corpus counts) and exit")
    parser.add_argument("--verbose", action="store_true",
                        help="print low findings too (hidden by default: their live hits are design decisions)")
    args = parser.parse_args()

    rules = dict(DEFAULTS)
    if args.rules:
        try:
            rules.update(json.loads(args.rules.read_text()))
        except (OSError, json.JSONDecodeError) as error:
            fail(f"{args.rules}: {error}")
        problems = palette_problems(rules)
        if problems:
            # Config error (exit 2), never a silent skip: an unreadable palette
            # would report a green surface.role for a page it never checked.
            fail(f"{args.rules}: " + "; ".join(problems))

    if args.rules_report:
        print(rules_report())
        return 0
    if not args.page and not args.from_nodes:
        parser.error("--page or --from-nodes is required")

    if args.from_nodes:
        try:
            nodes = json.loads(args.from_nodes.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"{args.from_nodes}: {exc}")
        if not isinstance(nodes, list):
            fail(f"{args.from_nodes}: no node list")
        args.page = args.page or args.from_nodes.stem.replace(".nodes", "")
    else:
        nodes = collect(args.page)

    if args.dump_nodes:
        args.dump_nodes.write_text(json.dumps(nodes, indent=1) + "\n")
        print(f"wrote {args.dump_nodes} ({len(nodes)} nodes)")

    missing, measured = ink_unavailable(nodes)
    if measured and missing / measured > INK_NULL_MAX_RATIO:
        # Exit 2, not a finding: every ink rule was skipped, so the findings this
        # run would print say nothing about the page.
        message = (f"page not active: textBounds unavailable — open {args.page}; "
                   f"findings are NOT valid ({missing}/{measured} texts unmeasured)")
        if args.json:
            args.json.write_text(json.dumps(
                {"page": args.page, "valid": False, "findings": []}, indent=2) + "\n")
        fail(message)

    findings = lint(nodes, rules)
    high = [f for f in findings if f["severity"] == "high"]
    medium = [f for f in findings if f["severity"] == "medium" and not f["acknowledged"]]
    acked = [f for f in findings if f["acknowledged"]]
    low = [f for f in findings if f["severity"] == "low"]
    shown = [f for f in findings if f["severity"] in ("high", "medium")
             or (args.verbose and f["severity"] == "low")]

    print(f"page: {args.page}  shapes: {len(nodes)}  findings: {len(findings)} "
          f"({len(high)} high, {len(medium)} medium, {len(acked)} acknowledged"
          + (f", {len(low)} low" if args.verbose else "") + ")")
    if not rules.get("surface_white") or not rules.get("surface_alt"):
        print("warning: surface.role is not configured — declare \"surface_white\" and "
              "\"surface_alt\" in the project craft-rules.json; the rule was skipped")
    for finding in shown:
        if finding["acknowledged"]:
            continue
        count = f" (×{finding['count']})" if finding["count"] > 1 else ""
        print(f"  [{finding['severity']:<6}] {finding['board']}: {finding['finding']}{count}")
    if not shown and not acked and not low:
        print("  clean on the mechanical checks — that proves compliance, not design")
    elif not shown and not acked:
        print(f"  {len(low)} low finding(s) hidden — --verbose lists them")
    if acked:
        print(f"  acknowledged: {len(acked)} finding group(s) with a recorded design reason")
        for finding in acked:
            count = f" (×{finding['count']})" if finding["count"] > 1 else ""
            print(f"  [ack   ] {finding['board']}: {finding['rule']} — {finding['ack_reason']}{count}")

    if args.json:
        args.json.write_text(json.dumps(
            {"page": args.page, "valid": True,
             "summary": {"high": len(high), "medium": len(medium),
                         "acknowledged": len(acked), "low": len(low)},
             "findings": findings}, indent=2) + "\n")
        print(f"wrote {args.json}")
    return 1 if high else 0


if __name__ == "__main__":
    raise SystemExit(main())
