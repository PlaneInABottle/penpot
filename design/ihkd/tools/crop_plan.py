#!/usr/bin/env python3
"""Re-cut every board's 1:1 evidence from the project's declared crop plan.

    python3 design/ihkd/tools/crop_plan.py --nodes-dir /tmp/ihkd-nodes [--board 01-ana-sayfa] [--dry-run]

The plan (`crop-plan.json`, next to this file) is the project-owned record of
what the 1:1 review must contain per board: the render to slice, the page whose
`design_lint.py --dump-nodes` geometry resolves the automatic regions, the real
primary action's shape name, and any board-relative region this project needs
beyond the automatic four. `crop_board.py` owns the cropping; this script only
expands the plan into its documented CLI (one `--region` per declared crop) so a
re-cut after a tool or board change is one command, not hand-typed geometry.

It never exports: a stale render is the caller's problem, and `crop_board`'s
source-sha rule resets attestations when the pixels change.

Exit codes: 0 every listed board re-cut, 1 one crop_board run failed,
2 input/environment (missing plan, missing node dump, no crop_board).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = HERE / "crop-plan.json"
CROP = ROOT / "scripts" / "crop_board.py"


def command(entry: dict, nodes_dir: pathlib.Path) -> list[str]:
    nodes = nodes_dir / f"nodes-{entry['page']}.json"
    if not nodes.is_file():
        raise SystemExit(f"error: missing node dump {nodes} — run "
                         f"`python3 scripts/design_lint.py --page {entry['page']} --dump-nodes {nodes}`")
    png = ROOT / entry["png"]
    if not png.is_file():
        raise SystemExit(f"error: missing render {png} — export {entry['board']} first")
    args = [sys.executable, str(CROP), "--board", entry["board"], "--png", str(png),
            "--out", str(ROOT / entry["out"]), "--regions", str(nodes)]
    if entry.get("primary"):
        args += ["--primary-action", entry["primary"]]
    for region in entry.get("regions", []):
        args += ["--region", json.dumps(region, ensure_ascii=False)]
    return args


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nodes-dir", type=pathlib.Path, required=True)
    ap.add_argument("--board", help="one board from the plan")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    try:
        plan = json.loads(PLAN.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read {PLAN}: {exc}", file=sys.stderr)
        return 2
    boards = plan.get("boards") or []
    if args.board:
        boards = [b for b in boards if b.get("board") == args.board]
        if not boards:
            print(f"error: {args.board!r} is not in the plan", file=sys.stderr)
            return 2

    failed = 0
    for entry in boards:
        cmd = command(entry, args.nodes_dir)
        print(f"== {entry['board']}  (primary: {entry.get('primary') or 'none declared'}, "
              f"declared regions: {len(entry.get('regions', []))})")
        print("   " + " ".join(cmd[1:]))
        if args.dry_run:
            continue
        result = subprocess.run(cmd, capture_output=True, text=True)
        for line in (result.stdout or "").splitlines():
            print("   " + line)
        if result.returncode:
            failed += 1
            print("   FAILED", file=sys.stderr)
            for line in (result.stderr or "").splitlines():
                print("   " + line, file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
