#!/usr/bin/env python3
"""One command for the finished-screen gate, with per-step timings.

    gate.py --pages Üyelik
    gate.py --pages Kurumsal,Kongre --boards 01,05,07
    gate.py --pages Üyelik --project design/ihkd
    gate.py stage design/ihkd/build/build.py design/ihkd/shots/19-giris.png

Per page it runs design_lint.py (+--json and --dump-nodes), then design_qa.py
(--lint-json), then the project's ux-gate spec once when that file exists. The
heavy steps — export_board.py and crop_board.py — run only for the boards named
in --boards; `01` resolves through design/<project>/build/build.py's SCREENS map,
so the page comes from the same table the build uses.

One summary table, one total, one exit code: 0 every step passed, 1 findings,
2 environment/transport (a step's own exit code 2 maps here). The lint's own
counts are echoed per page: `medium` there are reported but never gate, and
`acknowledged` ones carry a recorded design reason (craft-rules.json), so only
the unexplained medium count is worth reading. `design_qa` exits 0 for advisory
findings (hard-coded fills, unnamed shapes, no flow); the gate prints those lines
and its PASS line then says "not clean", so exit 0 never hides them. Exit 2 also covers
an INVALID step: design_lint reports a page whose texts were never measured
(textBounds unavailable — the page is not open), and a gate that printed PASS
there would pass a page nobody looked at.

`stage PATH...` is the only supported way to commit design work: `design/*/` is
gitignored, so `git status` stays quiet until `git add -f` runs. It applies -f
only under design/ and verifies each path landed in the index.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPTS = HERE
DEFAULT_PROJECT = ROOT / "design" / "ihkd"
# design_lint exits 2 on a page it never measured; that is not the environment
# and must never be summarized as PASS.
INVALID_MARKER = "page not active: textBounds unavailable"


sys.path.insert(0, str(HERE))
from export_board import WAIT_S as EXPORT_WAIT_S  # noqa: E402


def py(script: str) -> list[str]:
    return [sys.executable, str(SCRIPTS / script)]


def export_timeout(step_timeout: float) -> float:
    """The export owns a rescue window longer than the MCP task limit it recovers
    from; the gate's per-step timeout must not kill it first."""
    return max(step_timeout, EXPORT_WAIT_S + 60)


def load_screens(build_py: pathlib.Path) -> dict[str, tuple[str, str]]:
    """SCREENS from the project's build.py: screen-NN -> (page, board)."""
    if not build_py.is_file():
        return {}
    spec = importlib.util.spec_from_file_location("gate_build_screens", build_py)
    if spec is None or spec.loader is None:
        return {}
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:  # noqa: BLE001 - a broken build.py must not hide the gate's own steps
        return {}
    return dict(getattr(module, "SCREENS", {}))


def resolve_board(token: str, screens: dict[str, tuple[str, str]]) -> tuple[str, str] | None:
    """'01', 'screen-01' or a full board name -> (page, board)."""
    key = token if token.startswith("screen-") else f"screen-{token.zfill(2)}"
    if key in screens:
        return screens[key]
    for page, board in screens.values():
        if board == token:
            return page, board
    return None


def run_step(label: str, argv: list[str], timeout: float) -> dict:
    started = time.monotonic()
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        code, output = proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        code, output = 2, f"timed out after {timeout:.0f}s"
    except OSError as exc:
        code, output = 2, f"{type(exc).__name__}: {exc}"
    seconds = time.monotonic() - started
    print(f"  {label:<34} exit {code}  {seconds:6.2f}s")
    return {"step": label, "code": code, "seconds": seconds, "output": output,
            "invalid": INVALID_MARKER in output}


def report(step: dict, keep: int = 12) -> None:
    """Print the tail of a failing step so the table stays readable."""
    lines = [ln for ln in step["output"].splitlines() if ln.strip()]
    for line in lines[-keep:]:
        print(f"      {line}")


def stage(paths: list[str]) -> int:
    if not paths:
        print("error: stage needs at least one path", file=sys.stderr)
        return 2
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"error: not a git checkout: {exc}", file=sys.stderr)
        return 2
    root = pathlib.Path(top).resolve()
    failures = 0
    for raw in paths:
        path = pathlib.Path(raw)
        if not path.is_absolute():
            path = pathlib.Path.cwd() / path
        path = path.resolve()  # /var -> /private/var on macOS, matching git's root
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            print(f"stage: {raw} is outside {root}", file=sys.stderr)
            failures += 1
            continue
        argv = ["git", "add", "-f", rel] if rel.startswith("design/") else ["git", "add", rel]
        added = subprocess.run(argv, cwd=root, capture_output=True, text=True)
        check = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=root,
                               capture_output=True, text=True)
        if added.returncode != 0 or check.returncode != 0:
            detail = (added.stderr or added.stdout or check.stderr).strip().splitlines()
            print(f"stage: FAILED {rel} — {detail[0] if detail else 'not in the index'}", file=sys.stderr)
            failures += 1
        else:
            print(f"stage: {rel} ({'git add -f' if rel.startswith('design/') else 'git add'})")
    return 1 if failures else 0


def gate(pages: list[str], boards: list[str], project: pathlib.Path, timeout: float) -> int:
    screens = load_screens(project / "build" / "build.py")
    if boards and not screens:
        print(f"error: no SCREENS in {project / 'build' / 'build.py'}", file=sys.stderr)
        return 2
    targets: list[tuple[str, str]] = []
    for token in boards:
        found = resolve_board(token, screens)
        if found is None:
            print(f"error: board {token!r} is not in {project.name}'s SCREENS", file=sys.stderr)
            return 2
        targets.append(found)

    steps: list[dict] = []
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="gate-") as tmp:
        tmpdir = pathlib.Path(tmp)
        for page in pages:
            lint_json = tmpdir / f"lint-{page}.json"
            nodes_json = tmpdir / f"nodes-{page}.json"
            lint_argv = py("design_lint.py") + ["--page", page, "--json", str(lint_json),
                                                "--dump-nodes", str(nodes_json)]
            rules = project / "craft-rules.json"
            if rules.is_file():
                lint_argv += ["--rules", str(rules)]
            steps.append(run_step(f"design_lint {page}", lint_argv, timeout))
            steps.append(run_step(f"design_qa {page}",
                                  py("design_qa.py") + ["--page", page, "--lint-json", str(lint_json)],
                                  timeout))
            steps.append(run_step(f"copy_lint {page}",
                                  py("copy_lint.py") + ["--page", page, "--project", str(project)],
                                  timeout))

        spec = project / "ux-spec.json"
        if spec.is_file():
            steps.append(run_step("ux_gate", py("ux_gate.py") + ["--spec", str(spec)], timeout))

        shots = project / "shots"
        for page, board in targets:
            export_step = run_step(f"export_board {board}",
                                   py("export_board.py") + ["--board", board, "--page", page, "--out", str(shots)],
                                   export_timeout(timeout))
            steps.append(export_step)
            rendered = shots / f"{board}.png"
            if export_step["code"] != 0 or not rendered.is_file():
                # Crop from the file it just produced; a second live export would
                # repeat the same 120 s bridge timeout for a render that already
                # exists — and without a render there is nothing to crop.
                print(f"  crop_board {board:<24} skipped (export exit {export_step['code']})")
                continue
            nodes = tmpdir / f"nodes-{page}.json"
            crop_argv = py("crop_board.py") + ["--png", str(rendered), "--board", board,
                                               "--out", str(shots / board)]
            if nodes.is_file():
                crop_argv += ["--regions", str(nodes)]
            steps.append(run_step(f"crop_board {board}", crop_argv, timeout))

    total = time.monotonic() - started
    print()
    print(f"{'step':<36}{'exit':>5}{'seconds':>10}")
    for step in steps:
        print(f"{step['step']:<36}{step['code']:>5}{step['seconds']:>10.2f}"
              + ("  INVALID" if step.get("invalid") else ""))
    print(f"{'total':<36}{'':>5}{total:>10.2f}")
    for step in steps:
        if not step["step"].startswith("design_lint"):
            continue
        for line in step["output"].splitlines():
            if line.startswith("page: "):
                print(f"  {line}")

    # design_qa exits 0 for advisory findings (hard-coded fills, unnamed shapes,
    # no flow). A gate that only reads exit codes would hide them and print PASS
    # over an unclean QA report, so surface those lines explicitly.
    advisory: list[str] = []
    advisory_count = 0
    for step in steps:
        if not step["step"].startswith("design_qa") or step["code"] != 0:
            continue
        for line in step["output"].splitlines():
            text = line.strip()
            if text.startswith("- "):
                advisory.append(f"{step['step']}: {text}")
                advisory_count += 1
            elif text.startswith("verdict: findings"):
                advisory.append(f"{step['step']}: {text}")
    if advisory:
        print()
        print(f"{advisory_count} non-fatal QA finding(s) — not a clean pass:")
        for line in advisory:
            print(f"  {line}")

    failing = [s for s in steps if s["code"] != 0]
    for step in failing:
        print()
        print(f"--- {step['step']} (exit {step['code']})")
        report(step)

    invalid = [s for s in steps if s.get("invalid")]
    if invalid:
        print(f"gate: FAIL (invalid) — {len(invalid)} step(s) read a page that was not "
              f"measured: open it and rerun — {total:.1f}s")
        return 2
    if any(s["code"] == 2 for s in steps):
        print(f"gate: ENVIRONMENT ({sum(1 for s in steps if s['code'] == 2)} step(s)) — {total:.1f}s")
        return 2
    if failing:
        print(f"gate: FINDINGS ({len(failing)} step(s)) — {total:.1f}s")
        return 1
    if advisory:
        print(f"gate: PASS ({advisory_count} non-fatal QA finding(s) — not clean; "
              f"see above) — {total:.1f}s")
        return 0
    print(f"gate: PASS — {total:.1f}s")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command")
    stage_ap = sub.add_parser("stage", help="git add -f design paths, verify they landed")
    stage_ap.add_argument("paths", nargs="+")
    ap.add_argument("--pages", default="", help="comma-separated page names")
    ap.add_argument("--boards", default="", help="comma-separated board numbers or names (heavy steps)")
    ap.add_argument("--project", type=pathlib.Path, default=DEFAULT_PROJECT)
    ap.add_argument("--step-timeout", type=float, default=300.0)
    args = ap.parse_args(argv)

    if args.command == "stage":
        return stage(args.paths)
    pages = [p.strip() for p in args.pages.split(",") if p.strip()]
    boards = [b.strip() for b in args.boards.split(",") if b.strip()]
    if not pages:
        ap.error("--pages is required (or use the stage subcommand)")
    return gate(pages, boards, args.project, args.step_timeout)


if __name__ == "__main__":
    raise SystemExit(main())
