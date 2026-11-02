#!/usr/bin/env python3
"""UX gate: verify a screen delivers its story, not just its pixels.

    ux_gate.py --spec design/<project>/ux-spec.json

The spec (JSON schema, documented below) states each screen's job in words:
one task, one primary call to action, the hook->proof->path->action story,
the states that exist, the mobile twin, what the first viewport must hold,
and the numbers the copy claims. The gate checks those words against the
live Penpot file — a screen whose copy claims 96 sessions while showing 19
fails here even when every lint rule is green.

Spec schema:
    {"project": "<name>",
     "defaults": {"accentMaxRatio": 0.3, "viewportH": 900},
     "screens": [{
        "board": "01-home", "page": "Kurumsal",
        "task": "one sentence: what the visitor gets done here",
        "primaryCta": "hero cta",            # shape name under the board
        "story": {"hook": "…", "proof": "…", "path": "…", "action": "…"},
        "states": [{"state": "empty", "board": "…"}],   # boards/shapes that must exist
        "mobile": {"board": "01-home-m", "page": "Mobil"} | "n/a: <reason>",
        "firstViewport": ["hero title", "hero cta"],    # shapes inside the first 900px
        "accentMaxRatio": 0.3,               # optional per-screen override
        "claims": [{"pattern": "sess title", "count": 96, "label": "sessions listed"}]
     }]}

Exit codes: 0 all screens hold their story, 1 finding(s), 2 environment or transport.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import urllib.error

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from design_lint import COLLECT, saturation  # noqa: E402
from penpot_exec import McpError, call_execute_code, ensure_helpers, fail, load_url, payload  # noqa: E402

STORY_BEATS = ("hook", "proof", "path", "action")


def fetch_nodes(url: str, page: str) -> list[dict]:
    nodes = payload(call_execute_code(url, COLLECT.replace("__PAGE__", json.dumps(page))))
    if not isinstance(nodes, list):
        raise McpError(f"collector returned no node list for page {page}")
    return nodes


def subtree(board_id: str, nodes: list[dict]) -> list[dict]:
    kids: dict[str, list[dict]] = {}
    for node in nodes:
        if node.get("parentId"):
            kids.setdefault(node["parentId"], []).append(node)
    out: list[dict] = []
    stack = list(kids.get(board_id, []))
    while stack:
        node = stack.pop()
        out.append(node)
        stack.extend(kids.get(node["id"], []))
    return out


def is_button(name: str) -> bool:
    low = name.lower()
    return ("cta" in low or "primary" in low) and "under" not in low


def evaluate(spec: dict, pages: dict[str, list[dict]]) -> list[dict]:
    """Pure gate: spec + {page: nodes} -> findings. No network, fully testable."""
    defaults = spec.get("defaults", {}) or {}
    viewport_h = float(defaults.get("viewportH", 900))
    findings: list[dict] = []

    def add(screen: str, message: str) -> None:
        findings.append({"screen": screen, "finding": message})

    all_nodes = [n for nodes in pages.values() for n in nodes]
    boards = {(page, n["name"]): n for page, nodes in pages.items() for n in nodes
              if n.get("type") == "board" and not n.get("parentId")}

    for screen in spec.get("screens", []):
        name = screen.get("board", "?")
        page = screen.get("page")
        board = boards.get((page, name))
        if board is None:
            add(name, f"board {name!r} not found on page {page!r}")
            continue
        nodes = pages[page]
        inside = subtree(board["id"], nodes)
        by_name = {n["name"]: n for n in inside}

        if not (screen.get("task") or "").strip():
            add(name, "task is empty — one sentence per screen")
        story = screen.get("story") or {}
        for beat in STORY_BEATS:
            if not (story.get(beat) or "").strip():
                add(name, f"story beat {beat!r} is empty — hook->proof->path->action per screen")

        cta = screen.get("primaryCta") or ""
        if cta not in by_name:
            add(name, f"primaryCta {cta!r} not found under board")
        primaries = sorted({n["name"] for n in inside
                            if n.get("type") in ("board", "rectangle") and is_button(n.get("name", ""))})
        if len(primaries) > 1:
            add(name, f"{len(primaries)} primary actions ({', '.join(primaries)}) — one dominant CTA per board")

        for wanted in screen.get("firstViewport", []):
            node = by_name.get(wanted)
            if node is None:
                add(name, f"firstViewport {wanted!r} not found under board")
            elif (node.get("y") or 0) - (board.get("y") or 0) >= viewport_h:
                add(name, f"firstViewport {wanted!r} starts below the fold "
                          f"(y={node['y'] - board['y']:.0f}px >= {viewport_h:.0f}px)")

        ceiling = float(screen.get("accentMaxRatio", defaults.get("accentMaxRatio", 0.3)))
        painted = 0.0
        for node in inside:
            if node.get("type") != "rectangle":
                continue
            try:
                if not node.get("fill") or saturation(node["fill"]) <= 0.5:
                    continue
            except (ValueError, TypeError):
                continue
            top = max(node["y"], board["y"])
            bottom = min(node["y"] + (node["h"] or 0), board["y"] + viewport_h)
            if bottom > top:
                painted += (bottom - top) * (node["w"] or 0)
        ratio = painted / ((board["w"] or 1) * viewport_h)
        if ratio > ceiling:
            add(name, f"accent fills {ratio:.3f} of the first viewport (max {ceiling:.3f})")

        mobile = screen.get("mobile")
        if isinstance(mobile, dict):
            twin = boards.get((mobile.get("page", page), mobile.get("board")))
            if twin is None:
                add(name, f"mobile board {mobile.get('board')!r} not found")
        elif isinstance(mobile, str) and mobile.startswith("n/a:") and len(mobile[4:].strip()) > 3:
            pass
        else:
            add(name, "mobile is neither an existing board nor a reasoned 'n/a: …'")

        for state in screen.get("states", []):
            target = state.get("board") or state.get("shape") or ""
            hit = target in by_name or any(n["name"] == target for n in all_nodes)
            if not hit:
                add(name, f"state {state.get('state')!r}: {target!r} not found in the file")

        for claim in screen.get("claims", []):
            try:
                matched = [n["name"] for n in inside if re.search(claim.get("pattern", ""), n.get("name", ""))]
            except re.error as exc:
                add(name, f"claim {claim.get('label', '?')!r}: bad pattern ({exc})")
                continue
            if len(matched) != claim.get("count"):
                add(name, f"claim {claim.get('label', claim.get('pattern'))!r}: "
                          f"pattern matched {len(matched)}, spec says {claim.get('count')}")

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--spec", type=pathlib.Path, required=True)
    args = parser.parse_args(argv)

    try:
        spec = json.loads(args.spec.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read spec {args.spec}: {exc}")

    try:
        url = load_url()
        ensure_helpers(url)
        wanted: dict[str, None] = {}
        for screen in spec.get("screens", []):
            wanted[screen.get("page")] = None
            mobile = screen.get("mobile")
            if isinstance(mobile, dict) and mobile.get("page"):
                wanted[mobile["page"]] = None
        pages: dict[str, list[dict]] = {}
        for page in wanted:
            if not page:
                continue
            try:
                pages[page] = fetch_nodes(url, page)
            except McpError as exc:
                if "page not found" not in str(exc):
                    raise
                # Missing pages stay out of `pages`: the board lookup below
                # reports them as findings (exit 1), not transport errors.
    except McpError as exc:
        fail(str(exc))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        fail(f"{type(exc).__name__}: {exc}")

    findings = evaluate(spec, pages)
    print(f"spec: {args.spec}  screens: {len(spec.get('screens', []))}  findings: {len(findings)}")
    for finding in findings:
        print(f"  - {finding['screen']}: {finding['finding']}")
    if not findings:
        print("  story holds on every screen — claims, CTA, viewport and states verified")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
