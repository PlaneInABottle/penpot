#!/usr/bin/env python3
"""Build one İHKD screen: focus its page, then run lib.js + the screen file.

    python3 design/ihkd/build/build.py screen-01
    python3 design/ihkd/build/build.py all
    python3 design/ihkd/build/build.py screen-02 --flows design/ihkd/build/flows.js

Penpot does not switch `currentPage` synchronously, so opening the page and writing to
it must be two MCP calls; this runner does that in the right order and prints the
warnings the screen reported. Exit codes: 0 built, 1 screen error, 2 environment.

`--flows FILE` is opt-in: after a successful build (+fit) the file's JS content is
executed once in the plugin context (same session semantics as the build — the page
is already open, so the file opens whatever pages it needs itself). A flows-stage
failure never fails the completed build: it prints a warning line and exits 0.
"""

from __future__ import annotations

import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from penpot_exec import McpError, call_execute_code, ensure_helpers, fail, load_url, payload  # noqa: E402

# screen -> (page, board)
SCREENS = {
    "screen-01": ("Kurumsal", "01-ana-sayfa"),
    "screen-02": ("Kurumsal", "02-dernek"),
    "screen-03": ("Kurumsal", "03-yonetim"),
    "screen-04": ("Kurumsal", "04-calisma-gruplari"),
    "screen-05": ("Kurumsal", "05-grup-detay"),
    "screen-06": ("Kongre", "06-kongre"),
    "screen-07": ("Kongre", "07-program"),
    "screen-08": ("Kongre", "08-bildiri"),
    "screen-09": ("Kongre", "09-kayit"),
    "screen-10": ("Kongre", "10-konaklama"),
    "screen-11": ("Akademi", "11-akademi"),
    "screen-12": ("Akademi", "12-kurs-detay"),
    "screen-13": ("Akademi", "13-kilavuzlar"),
    "screen-14": ("Akademi", "14-dergi"),
    "screen-15": ("İçerik", "15-haberler"),
    "screen-16": ("İçerik", "16-makale"),
    "screen-17": ("İçerik", "17-takvim"),
    "screen-18": ("Üyelik", "18-uyelik"),
    "screen-19": ("Üyelik", "19-giris"),
    "screen-20": ("Üyelik", "20-panel"),
}


def run(url: str, screen: str) -> dict:
    page, board = SCREENS[screen]
    call_execute_code(url, f"""
const p = penpot.currentFile.pages.find(x => x.name === {json.dumps(page)});
if (!p) throw new Error("page not found: " + {json.dumps(page)});
penpot.openPage(p);
return JSON.stringify({{ opened: p.name }});
""")
    time.sleep(1.2)
    lib = (HERE / "lib.js").read_text()
    body = (HERE / f"{screen}.js").read_text()
    result = payload(call_execute_code(url, lib + "\n" + body))
    # fit-until-quiet: layout commits asynchronously after a large build, so one
    # pass leaves ~100-190 texts with null textBounds on big boards. Poll both
    # signals (uncommitted texts + resized count) until both read 0, bounded.
    status_js = (lib + "\nreturn JSON.stringify((() => {"
                 " const p = penpot.currentFile.pages.find(x => x.name === " + json.dumps(page) + ");"
                 " let nulls = 0;"
                 " const walk = (s) => {"
                 " if (s.type === 'text' && !(s.textBounds && s.textBounds.height)) nulls++;"
                 " (s.children || []).forEach(walk); };"
                 " (p.root.children || []).forEach(walk);"
                 " return { nulls: nulls, fitted: IK.fit(" + json.dumps(page) + "),"
                 " bars: (IK.fitBars ? IK.fitBars(" + json.dumps(page) + ") : 0) }; })());")
    for i in range(10):
        time.sleep(3.0)
        try:
            st = payload(call_execute_code(url, status_js))
            st = json.loads(st) if isinstance(st, str) else st
        except McpError:
            break
        if not st.get("nulls") and not st.get("fitted") and not st.get("bars"):
            print(f"{screen}: fit quiet after {i + 1} pass(es)")
            break
    else:
        print(f"{screen}: warning: layout not quiet after 10 fit passes")
    return json.loads(result) if isinstance(result, str) else result


def run_flows(url: str, path: pathlib.Path) -> tuple[bool, str]:
    """Execute a flows snippet once. Never raises; a failure is a warning, not a build error."""
    try:
        code = path.read_text()
    except OSError as exc:
        return False, f"warning: flows: cannot read {path}: {exc}"
    if not code.strip():
        return False, f"warning: flows: empty file {path}"
    try:
        result = payload(call_execute_code(url, code))
    except McpError as exc:
        return False, f"warning: flows: ERROR {exc}"
    if isinstance(result, dict) and result.get("errors"):
        return False, "warning: flows: " + "; ".join(str(e) for e in result["errors"])
    links = result.get("links") if isinstance(result, dict) else None
    if links is not None:
        return True, f"flows: applied {len(links)} link(s)"
    return True, "flows: applied"


def main(argv: list[str]) -> int:
    flows_file: pathlib.Path | None = None
    names: list[str] = []
    args = list(argv)
    i = 0
    while i < len(args):
        if args[i] == "--flows":
            if i + 1 >= len(args):
                fail("--flows requires a file argument")
            flows_file = pathlib.Path(args[i + 1])
            i += 2
        else:
            names.append(args[i])
            i += 1
    if not names or names[0] == "all":
        names = list(SCREENS)
    unknown = [n for n in names if n not in SCREENS]
    if unknown:
        fail(f"unknown screen(s): {', '.join(unknown)}")
    try:
        url = load_url()
        ensure_helpers(url)
    except McpError as exc:
        fail(str(exc))
    except OSError as exc:
        fail(f"{type(exc).__name__}: {exc}")
    for name in names:
        try:
            report = run(url, name)
        except McpError as exc:
            print(f"{name}: ERROR {exc}", file=sys.stderr)
            return 1
        page, board = SCREENS[name]
        gaps = report.get("gaps") or []
        print(f"{name}: {page} / {board} — warnings {len(report.get('warnings') or [])}"
              + (f", token gaps {sorted(set(gaps))}" if gaps else ""))
        for w in report.get("warnings") or []:
            print(f"  ! {w}")
        time.sleep(0.6)
    if flows_file is not None:
        ok, msg = run_flows(url, flows_file)
        print(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
