#!/usr/bin/env python3
"""Design QA for a Penpot page: token coverage, naming, prototype and component hygiene.

    design_qa.py                        # audit the current page
    design_qa.py --page Showcase        # audit a named page (never switches the view)
    design_qa.py --strict               # exit 1 on hard-coded fills too
    design_qa.py --json report.json     # write the raw audit payload
    design_qa.py --lint-json lint.json  # also fail on high findings from
                                        # `design_lint.py --json lint.json`

Exit codes: 0 clean, 1 findings that --strict escalates or that are always fatal
(orphan components, duplicate token set names, high lint findings via --lint-json),
2 environment problem.

Read-only against the file, and leaves the user's current page alone: a named page
is audited in place, so `penpot.currentPage` never changes. The browser tab with the
target file must have the MCP plugin connected; the audit is computed inside it.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.error

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from penpot_exec import McpError, call_execute_code, ensure_helpers, fail, load_url, payload  # noqa: E402


def audit(url: str, page: str | None) -> dict:
    """Audit `page` by name (or the current page) without switching the browser view."""
    result = call_execute_code(
        url,
        f"return JSON.stringify(storage.H.audit({json.dumps(page) if page else 'null'}));",
    )
    data = payload(result)
    if not isinstance(data, dict):
        raise McpError(f"unexpected audit result: {data!r}")
    if data.get("error"):
        raise McpError(str(data["error"]))
    return data


def coverage_counts(fills: str) -> tuple[int, int]:
    """'6/56' -> (6, 56); a missing or malformed value counts as an empty total."""
    filled, _, total = str(fills or "").partition("/")
    try:
        return int(filled or 0), int(total or 0)
    except ValueError:
        return 0, 0


def coverage_percent(fills: str) -> int:
    filled, total = coverage_counts(fills)
    return round(100 * filled / total) if total else 100


def duplicate_set_names(sets: list[dict]) -> list[str]:
    """Names used by more than one token set; a second set under another name is fine."""
    seen: dict[str, int] = {}
    for token_set in sets:
        seen[token_set["name"]] = seen.get(token_set["name"], 0) + 1
    return sorted(name for name, count in seen.items() if count > 1)


def lint_high_findings(doc: object) -> list[dict]:
    """High findings from a `design_lint.py --json` payload (findings file or node list)."""
    nodes = doc if isinstance(doc, list) else (doc.get("findings", []) if isinstance(doc, dict) else [])
    return [f for f in nodes if isinstance(f, dict) and f.get("severity") == "high"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--page")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", type=pathlib.Path)
    ap.add_argument("--lint-json", type=pathlib.Path,
                    help="lint --json findings file; high findings there are fatal here")
    args = ap.parse_args(argv)

    try:
        url = load_url()
        ensure_helpers(url)
        report = audit(url, args.page)
    except McpError as exc:
        fail(str(exc))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        fail(f"{type(exc).__name__}: {exc}")

    sets = report["tokenSets"]
    orphans = sorted(c["name"] for c in report["components"] if c.get("orphan"))
    duplicated = duplicate_set_names(sets)
    coverage = report["tokenCoverage"]
    filled, total = coverage_counts(coverage["fills"])

    findings: list[str] = []
    info: list[str] = []
    if filled != total:
        findings.append(
            f"{total - filled} shape(s) use a hard-coded fill: {', '.join(coverage['hardColors'])}"
        )
    if coverage.get("renderMismatches"):
        findings.append(
            f"{coverage['renderMismatches']} token-bound fill(s) render another colour "
            f"(binding is metadata; the literal fill is what paints): "
            + "; ".join(coverage.get("mismatchSample", []))
        )
    if orphans:
        findings.append(f"orphan component(s): {', '.join(orphans)}")
    if duplicated:
        findings.append(f"duplicate token set name(s): {', '.join(duplicated)}")
    elif len(sets) > 1:
        info.append(
            f"{len(sets)} token sets: {', '.join(s['name'] for s in sets)} "
            "(several sets are fine, only duplicate names are fatal)"
        )
    if report["unnamed"]:
        findings.append(f"{report['unnamed']} shape(s) keep a default name")
    if not report["flows"]:
        findings.append("no prototype flow on this page")

    lint_high: list[dict] = []
    if args.lint_json:
        try:
            lint_doc = json.loads(args.lint_json.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(f"cannot read lint findings {args.lint_json}: {exc}")
        else:
            lint_high = lint_high_findings(lint_doc)
            if lint_high:
                boards = sorted({f.get("board", "?") for f in lint_high})
                findings.append(
                    f"{len(lint_high)} high lint finding(s) on {', '.join(boards)}: "
                    + "; ".join(f.get("finding", "?") for f in lint_high[:5])
                )

    print(f"page: {report['page']}  boards: {report['boards']}  shapes: {report['shapes']}")
    print(
        f"token coverage: fills {coverage['fills']} ({coverage_percent(coverage['fills'])}%), "
        f"text sizes {coverage['textSizes']}"
    )
    print(f"prototype: {len(report['flows'])} flow(s), {report['interactiveShapes']} interactive shape(s)")
    print(f"components: {len(report['components'])}, token sets: {len(sets)}")
    print("findings:" if findings else "findings: none")
    for line in findings:
        print(f"  - {line}")
    for line in info:
        print(f"info: {line}")

    if args.json:
        args.json.write_text(json.dumps(report, indent=2) + "\n")
        print(f"wrote {args.json}")

    fatal = bool(orphans or duplicated or coverage.get("renderMismatches") or lint_high)
    return 1 if fatal or (args.strict and filled != total) else 0


if __name__ == "__main__":
    sys.exit(main())
