#!/usr/bin/env python3
"""Build one İHKD screen: focus its page, then run lib.js + the screen file.

    python3 design/ihkd/build/build.py screen-01
    python3 design/ihkd/build/build.py all
    python3 design/ihkd/build/build.py screen-02 --flows design/ihkd/build/flows.js

Penpot does not switch `currentPage` synchronously, so opening the page and writing to
it must be two MCP calls; this runner does that in the right order and prints the
warnings the screen reported. Exit codes: 0 built, 1 screen error or a layout that
never settled, 2 environment or transport (a timed-out call is reported, never retried).

Layout commits asynchronously after a large build, so the runner polls the board's own
texts until they all have ink — 250 ms apart, bounded by --fit-deadline (default 20 s).
The fit pass is scoped to the board just built, and lib.js is sent once: later polls
reuse `storage.IK`, re-sending it only when the helpers or lib version moved on.

One build at a time: `build/.build.lock` holds PID + screen + start time, and a lock
older than five minutes is treated as stale (a killed build cannot block the next).

`--flows FILE` is opt-in: after a successful build (+fit) the file's JS content is
executed once in the plugin context (same session semantics as the build — the page
is already open, so the file opens whatever pages it needs itself). A flows-stage
failure never fails the completed build: it prints a warning line and exits 0.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from penpot_exec import McpError, TaskTimeout, call_execute_code, ensure_helpers, fail, load_url, payload  # noqa: E402

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

LOCK = HERE / ".build.lock"
LOCK_STALE_S = 300.0
POLL_S = 0.25
POLL_MAX_S = 1.0
OPEN_DEADLINE_S = 5.0
FIT_DEADLINE_S = 20.0
LIB_VERSION = re.compile(r'const VERSION = "([^"]+)";')


class Locked(Exception):
    """Another build owns the lock and it is not stale."""


TimedOut = TaskTimeout


def acquire_lock(screen: str) -> pathlib.Path:
    for _ in range(2):
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            held = LOCK.read_text().strip() if LOCK.exists() else "?"
            age = time.time() - LOCK.stat().st_mtime if LOCK.exists() else 0.0
            if age < LOCK_STALE_S:
                raise Locked(f"another build holds {LOCK} ({held}, {age:.0f}s old)")
            print(f"build: ignoring stale lock ({held}, {age:.0f}s old)", file=sys.stderr)
            LOCK.unlink(missing_ok=True)
            continue
        with os.fdopen(fd, "w") as fh:
            fh.write(f"pid={os.getpid()} screen={screen} started={time.strftime('%Y-%m-%dT%H:%M:%S')}\n")
        return LOCK
    raise Locked(f"could not take {LOCK}")


def release_lock() -> None:
    try:
        if LOCK.exists() and f"pid={os.getpid()} " in LOCK.read_text():
            LOCK.unlink()
    except OSError:
        pass


CURRENT_JS = "return JSON.stringify({ page: penpot.currentPage.name });"


def open_page(url: str, page: str, deadline: float = OPEN_DEADLINE_S) -> float:
    """Make `page` the current page, forcing a real switch.

    `penpot.openPage` on the page that is already current is a no-op, and a no-op
    never re-runs layout: every text added since that page was opened keeps
    `textBounds: null` (a rebuild then looks unfinished forever and fit cannot
    measure it). Leaving the page and coming back is what makes the renderer
    measure the new shapes.
    """
    started = time.monotonic()
    current = payload(call_execute_code(url, CURRENT_JS))
    if isinstance(current, dict) and current.get("page") == page:
        call_execute_code(url, f"""
const other = penpot.currentFile.pages.find((p) => p.name !== {json.dumps(page)});
if (other) penpot.openPage(other);
return JSON.stringify({{ left: other ? other.name : null }});
""")
        leave_by = time.monotonic() + 2.0
        while time.monotonic() < leave_by:
            state = payload(call_execute_code(url, CURRENT_JS))
            if not (isinstance(state, dict) and state.get("page") == page):
                break
            time.sleep(POLL_S)
    call_execute_code(url, f"""
const p = penpot.currentFile.pages.find(x => x.name === {json.dumps(page)});
if (!p) throw new Error("page not found: " + {json.dumps(page)});
penpot.openPage(p);
return JSON.stringify({{ opened: p.name }});
""")
    while time.monotonic() - started < deadline:
        current = payload(call_execute_code(url, CURRENT_JS))
        if isinstance(current, dict) and current.get("page") == page:
            return time.monotonic() - started
        time.sleep(POLL_S)
    raise McpError(f"page {page!r} did not become current within {deadline:.0f}s")


def status_js(page: str, board: str) -> str:
    """Fit-poll for the active board only; asks for a lib re-send on a version drift."""
    return f"""
const P = {json.dumps(page)}, B = {json.dumps(board)};
if (!storage.IK || storage.IK.VERSION !== __LIB_VERSION__ || storage.IK_HELPERS !== storage.H.version) {{
  return JSON.stringify({{ reload: true }});
}}
if (penpot.currentPage.name !== P) {{
  const target = penpot.currentFile.pages.find(x => x.name === P);
  if (target) penpot.openPage(target);
  return JSON.stringify({{ reopened: P }});
}}
const IK = storage.IK;
const p = penpot.currentFile.pages.find(x => x.name === P);
const b = (p.root.children || []).find(x => x.name === B);
let nulls = 0;
const walk = (s) => {{
  if (s.type === "text" && !(s.textBounds && s.textBounds.height)) nulls++;
  (s.children || []).forEach(walk);
}};
if (b) (b.children || []).forEach(walk);
return JSON.stringify({{ nulls: nulls, fitted: IK.fit(P, B), cards: IK.fitCards ? IK.fitCards(P, B) : 0, bars: IK.fitBars(P, B) }});
"""


def poll_fit(url: str, page: str, board: str, lib: str, deadline: float) -> tuple[bool, float, int]:
    """Poll fit until the board is quiet. Returns (quiet, seconds, passes)."""
    started = time.monotonic()
    body = status_js(page, board)
    version = json.dumps(LIB_VERSION.search(lib).group(1)) if LIB_VERSION.search(lib) else '""'
    code = body.replace("__LIB_VERSION__", version)
    passes = 0
    wait = POLL_S
    while time.monotonic() - started < deadline:
        time.sleep(wait)
        try:
            state = payload(call_execute_code(url, code))
            state = json.loads(state) if isinstance(state, str) else state
        except TimedOut:
            raise
        except McpError as exc:
            print(f"  fit poll: {exc}", file=sys.stderr)
            continue
        if not isinstance(state, dict):
            continue
        if state.get("reload"):
            code = lib + "\n" + body.replace("__LIB_VERSION__", version)
            continue
        if state.get("reopened"):
            continue
        passes += 1
        if (not state.get("nulls") and not state.get("fitted") and not state.get("bars")
                and not state.get("cards")):
            return True, time.monotonic() - started, passes
        # A resize is not visible in `textBounds` until the next layout commit
        # (~0.5-1 s); polling at 250 ms only re-applies the same resize to stale
        # ink, so back off while a pass keeps changing shapes.
        wait = min(POLL_MAX_S, wait * 2)
    return False, time.monotonic() - started, passes


def live_state(url: str, page: str, board: str) -> str:
    """Board node count and unmeasured-text count, for a call that timed out."""
    code = f"""
const p = penpot.currentFile.pages.find(x => x.name === {json.dumps(page)});
const b = p && (p.root.children || []).find(x => x.name === {json.dumps(board)});
if (!b) return JSON.stringify({{ found: false, page: p ? p.name : null }});
let nodes = 0, nulls = 0;
const walk = (s) => {{
  nodes++;
  if (s.type === "text" && !(s.textBounds && s.textBounds.height)) nulls++;
  (s.children || []).forEach(walk);
}};
(b.children || []).forEach(walk);
return JSON.stringify({{ found: true, page: penpot.currentPage.name, nodes: nodes, nulls: nulls }});
"""
    try:
        state = payload(call_execute_code(url, code))
        return json.dumps(json.loads(state) if isinstance(state, str) else state)
    except McpError as exc:
        return f"live state unavailable ({exc})"


def run(url: str, screen: str, fit_deadline: float) -> tuple[dict, bool, float]:
    page, board = SCREENS[screen]
    t0 = time.monotonic()
    opened = open_page(url, page)
    lib = (HERE / "lib.js").read_text()
    body = (HERE / f"{screen}.js").read_text()
    result = payload(call_execute_code(url, lib + "\n" + body))
    built = time.monotonic()
    quiet, fit_s, passes = poll_fit(url, page, board, lib, fit_deadline)
    total = time.monotonic() - t0
    report = json.loads(result) if isinstance(result, str) else result
    print(f"  open {opened:.2f}s  build {built - t0 - opened:.2f}s  "
          f"fit {fit_s:.2f}s ({passes} pass(es), {'quiet' if quiet else 'NOT quiet'})  "
          f"total {total:.2f}s")
    return report, quiet, total


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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("screens", nargs="*", help="screen-NN names, or 'all'")
    ap.add_argument("--flows", type=pathlib.Path)
    ap.add_argument("--fit-deadline", type=float, default=FIT_DEADLINE_S,
                    help="seconds to wait for the built board to settle (default %(default)s)")
    args = ap.parse_args(argv)
    names = args.screens or ["all"]
    if names[0] == "all":
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

    try:
        acquire_lock(names[0])
    except Locked as exc:
        print(f"build: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        fail(f"cannot write {LOCK}: {exc}")

    code = 0
    try:
        for name in names:
            page, board = SCREENS[name]
            try:
                report, quiet, _ = run(url, name, args.fit_deadline)
            except TimedOut as exc:
                print(f"{name}: {exc}", file=sys.stderr)
                print(f"{name}: live state {live_state(url, page, board)} — not retrying", file=sys.stderr)
                return 2
            except McpError as exc:
                print(f"{name}: ERROR {exc}", file=sys.stderr)
                return 1
            gaps = report.get("gaps") or []
            print(f"{name}: {page} / {board} — warnings {len(report.get('warnings') or [])}"
                  + (f", token gaps {sorted(set(gaps))}" if gaps else ""))
            for w in report.get("warnings") or []:
                print(f"  ! {w}")
            if not quiet:
                print(f"{name}: ERROR layout not quiet after {args.fit_deadline:.1f}s; "
                      f"live state {live_state(url, page, board)}", file=sys.stderr)
                code = 1
        if args.flows is not None:
            ok, msg = run_flows(url, args.flows)
            print(msg)
    finally:
        release_lock()
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
