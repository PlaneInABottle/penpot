#!/usr/bin/env python3
"""Systematic spacing audit for a Penpot page, from lint geometry.

    design_lint.py --page Kurumsal --json /tmp/lint-k.json
    rhythm.py /tmp/lint-k.json

Groups top-level shapes by board, sorts them by y, and prints the gaps between
consecutive blocks plus the left/right content margins. Gaps cluster at the
declared section rhythm; any gap beyond 2x the median is flagged for a written
reason. Generic: no project assumptions, only geometry.

Exit codes: 0 checked, 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report", type=pathlib.Path, help="lint --json output")
    ap.add_argument("--rhythm", type=float, default=0.0, help="declared section rhythm in px (0 = derive median)")
    args = ap.parse_args(argv)

    try:
        nodes = json.loads(args.report.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"rhythm: cannot read {args.report}: {exc}", file=sys.stderr)
        return 2
    if isinstance(nodes, dict) and "findings" in nodes:
        print("rhythm: this looks like a --json findings file; need the node list", file=sys.stderr)
        return 2

    boards = [n for n in nodes if n.get("type") == "board" and n.get("parentId") is None]
    by_parent: dict[str, list[dict]] = {}
    for n in nodes:
        if n.get("parentId"):
            by_parent.setdefault(n["parentId"], []).append(n)

    for board in boards:
        kids = sorted(by_parent.get(board["id"], []), key=lambda n: (n.get("y") or 0, n.get("x") or 0))
        print(f"== {board['name']} ({len(kids)} top-level) ==")
        gaps = []
        prev_bottom = None
        for k in kids:
            top = k.get("y") or 0
            if prev_bottom is not None and top > prev_bottom:
                gaps.append(round(top - prev_bottom, 1))
            bottom = top + (k.get("h") or 0)
            if prev_bottom is None or bottom > prev_bottom:
                prev_bottom = bottom
        rhythm = args.rhythm or (sorted(gaps)[len(gaps) // 2] if gaps else 0)
        big = [g for g in gaps if rhythm and g > 2 * rhythm]
        small = [g for g in gaps if g < 8]
        print(f"   gaps: {gaps}")
        print(f"   rhythm~{rhythm:g}px  over-2x: {big or '-'}  hairlines<8px: {len(small)}")
        xs = [(k.get("x") or 0) for k in kids if (k.get("w") or 0) > 0]
        ends = [(k.get("x") or 0) + (k.get("w") or 0) for k in kids if (k.get("w") or 0) > 0]
        if xs and ends:
            print(f"   leftmost x: {min(xs):.0f}  rightmost end: {max(ends):.0f} (board {board.get('w')})")
        bh = board.get("h") or 0
        if prev_bottom is not None and bh > prev_bottom:
            print(f"   trailing void: {round(bh - prev_bottom):.0f}px of empty board below last shape")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
