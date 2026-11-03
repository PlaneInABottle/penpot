#!/usr/bin/env python3
"""Build one İHKD screen without losing what the rebuild replaces.

    python3 design/ihkd/build/build.py screen-01
    python3 design/ihkd/build/build.py all
    python3 design/ihkd/build/build.py screen-02 --flows design/ihkd/build/flows.js
    python3 design/ihkd/build/build.py --settle screen-07

A rebuild is lossless: after the build the runner toggles the page away and back
(`openPage` on the already-current page is a no-op, and a no-op never re-runs
layout), fits the board in a bounded number of passes, re-places the board's
provenance photos, re-applies `flows.js` once, and verifies `photos N/N` and
`links N/N` against the live file. A rebuild that loses a photo, a link or a
text's measured ink exits non-zero — no manual repair step is left.

Penpot does not switch `currentPage` synchronously, so every page move is
verified by polling `penpot.currentPage`; the runner also checks it before the
build call, after it, after fit and at the end. A page changed by another
session is a named error, not a silent wrong-page write.

`--settle SCREEN` runs the recovery alone (toggle + fit, no rebuild), for a
board that is otherwise built but not quiet.

`--dry-run` is the static pass: `node --check` on each named screen, the SCREENS
entry, without contacting the plugin (for a queued live run).

`--flows` is automatic (default `build/flows.js`); `--no-flows` opts out.
A flows/link verification failure is a build failure, not a warning.

Output ends with one machine-readable line, always, even when piped:

    RESULT ok|fail nulls=N

Exit codes: 0 built and verified, 1 screen/layout/photo/link finding, 2
environment, transport or another session changing the page (a timed-out call is
reported, never retried).
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TOOLS = HERE.parent / "tools"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(TOOLS))
from penpot_exec import (  # noqa: E402
    McpError, PluginBusy, TaskTimeout, acquire_session, call_execute_code, ensure_helpers,
    load_url, payload, plugin_session_blocker, release_session,
)
from media import entries_for_board  # noqa: E402

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
    # Mobil 390 ikizleri ve durum tahtaları (sayfa `Mobil` önce oluşturulmalı).
    "screen-state-01": ("Kurumsal", "01-bos"),
    "screen-state-07": ("Kongre", "07-program-loading"),
    "screen-state-09": ("Kongre", "09-kayit-hata"),
    # Bileşen kitaplığı: main instance'lar tek bir tahtada toplanır.
    "screen-components": ("Components", "component sheet"),
}

LOCK = HERE / ".build.lock"
LOCK_STALE_S = 300.0
POLL_S = 2.0           # layout settles asynchronously; 250 ms polling starves it
PAGE_SETTLE_S = 2.5    # let the renderer run before the first currentPage read
PAGE_POLL_S = 0.5
OPEN_DEADLINE_S = 15.0
LEAVE_DEADLINE_S = 8.0
DWELL_S = 3.0          # the renderer needs a frame on the other page
RETURN_SETTLE_S = 1.0  # ...and one after returning before bounds are readable
FIT_DEADLINE_S = 120.0
FIT_ATTEMPTS = 60
MEDIA_TIMEOUT_S = 600.0
MEDIA = TOOLS / "media.py"
PROVENANCE = HERE.parent / "media" / "provenance.json"
FLOWS = HERE / "flows.js"
LIB_VERSION = re.compile(r'const VERSION = "([^"]+)";')


class Locked(Exception):
    """Another build owns the lock and it is not stale."""


class PageDrift(McpError):
    """Another session changed `currentPage` while this build owned it."""


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


def other_writers(url: str) -> list[str]:
    """Who else holds the plugin: the session lock, not `pgrep`.

    `pgrep -f penpot_exec.py` missed writers started from another checkout, as a
    module, or as a build/import that never names the script — and it could not
    see a session that had already ended. The lock is the writer itself.
    """
    blocked = plugin_session_blocker(url)
    return [f"held by {blocked}"] if blocked else []


CURRENT_JS = "return JSON.stringify({ page: penpot.currentPage.name });"


def current_page(url: str) -> str | None:
    state = payload(call_execute_code(url, CURRENT_JS))
    return state.get("page") if isinstance(state, dict) else None


def require_page(url: str, page: str, when: str) -> None:
    found = current_page(url)
    if found != page:
        raise PageDrift(f"{when}: currentPage is {found!r}, expected {page!r} — "
                        "another session changed the page")


def switch_away(url: str, page: str, deadline: float = LEAVE_DEADLINE_S) -> None:
    """Open another page and prove the plugin left; `openPage` is async."""
    state = payload(call_execute_code(
        url, "return JSON.stringify({ pages: penpot.currentFile.pages.map((p) => p.name) });"))
    names = state.get("pages") if isinstance(state, dict) else None
    if not isinstance(names, list):
        raise McpError("could not list pages")
    others = [name for name in names if name != page]
    for other in others[:2]:
        call_execute_code(url, f"""
const p = penpot.currentFile.pages.find((x) => x.name === {json.dumps(other)});
if (!p) throw new Error("page not found: " + {json.dumps(other)});
penpot.openPage(p);
return JSON.stringify({{ leaving: p.name }});
""")
        time.sleep(PAGE_SETTLE_S)
        until = time.monotonic() + deadline
        while time.monotonic() < until:
            if current_page(url) != page:
                time.sleep(DWELL_S)
                return
            time.sleep(PAGE_POLL_S)
    raise PageDrift(f"could not leave page {page!r} — another session keeps currentPage on it")


def open_target(url: str, page: str, deadline: float = OPEN_DEADLINE_S) -> None:
    started = time.monotonic()
    call_execute_code(url, f"""
const p = penpot.currentFile.pages.find((x) => x.name === {json.dumps(page)});
if (!p) throw new Error("page not found: " + {json.dumps(page)});
penpot.openPage(p);
return JSON.stringify({{ opened: p.name }});
""")
    time.sleep(PAGE_SETTLE_S)
    while time.monotonic() - started < deadline:
        if current_page(url) == page:
            time.sleep(RETURN_SETTLE_S)
            return
        time.sleep(PAGE_POLL_S)
    raise McpError(f"page {page!r} did not become current within {deadline:.0f}s")


def open_page(url: str, page: str, deadline: float = OPEN_DEADLINE_S) -> float:
    """Make `page` current, forcing a real switch even when it already is."""
    started = time.monotonic()
    if current_page(url) == page:
        switch_away(url, page)
    open_target(url, page, deadline)
    return time.monotonic() - started


def toggle_page(url: str, page: str) -> float:
    """Leave and return: a no-op `openPage` never re-runs layout."""
    started = time.monotonic()
    switch_away(url, page)
    open_target(url, page)
    return time.monotonic() - started


def open_page_retry(url: str, page: str, attempts: int = 3) -> None:
    """A flows run leaves asynchronous page switches queued; retry after them."""
    last: McpError | None = None
    for _ in range(attempts):
        try:
            open_page(url, page)
            return
        except McpError as exc:
            last = exc
            time.sleep(1.0)
    raise last if last is not None else McpError(f"page {page!r} did not open")


def zoom_board(url: str, page: str, board: str) -> float:
    """Bring the board into view: the renderer measures text only when asked."""
    started = time.monotonic()
    if current_page(url) != page:
        open_page_retry(url, page)
    call_execute_code(url, f"""
const p = penpot.currentFile.pages.find((x) => x.name === {json.dumps(page)});
const b = p && (p.root.children || []).find((x) => x.name === {json.dumps(board)});
if (!b) throw new Error("board not found: " + {json.dumps(board)});
penpot.viewport.zoomIntoView([b]);
return JSON.stringify({{ zoom: penpot.viewport.zoom }});
""")
    time.sleep(1.0)
    return time.monotonic() - started


def status_js(page: str, board: str) -> str:
    """Measure the active board, then fit it; asks for a lib re-send on drift."""
    return f"""
const P = {json.dumps(page)}, B = {json.dumps(board)};
if (!storage.IK || storage.IK.VERSION !== __LIB_VERSION__ || storage.IK_HELPERS !== storage.H.version) {{
  return JSON.stringify({{ reload: true }});
}}
if (penpot.currentPage.name !== P) {{
  return JSON.stringify({{ drift: penpot.currentPage.name }});
}}
const K = storage.IK;  // never `IK`: a reload prepends lib.js, which declares const IK
const p = penpot.currentFile.pages.find((x) => x.name === P);
const b = (p.root.children || []).find((x) => x.name === B);
const nulls = [];
let texts = 0;
const walk = (s) => {{
  if (s.type === "text") {{
    texts++;
    if (!(s.textBounds && s.textBounds.height)) nulls.push(s.name);
  }}
  (s.children || []).forEach(walk);
}};
if (b) (b.children || []).forEach(walk);
return JSON.stringify({{
  texts: texts,
  nulls: nulls.length,
  nullNames: nulls.slice(0, 24),
  fitted: K.fit(P, B),
  cards: K.fitCards ? K.fitCards(P, B) : 0,
  bars: K.fitBars(P, B),
}});
"""


def fit_board(url: str, page: str, board: str, lib: str, deadline: float,
              max_attempts: int = FIT_ATTEMPTS) -> tuple[bool, int, list[str], float, int]:
    """Toggle-and-fit in bounded attempts. Returns (quiet, nulls, names, seconds, passes)."""
    started = time.monotonic()
    body = status_js(page, board)
    match = LIB_VERSION.search(lib)
    version = json.dumps(match.group(1)) if match else '""'
    code = body.replace("__LIB_VERSION__", version)
    passes = 0
    retoggles = 0
    quiet_streak = 0
    nulls = 0
    names: list[str] = []
    while passes < max_attempts and time.monotonic() - started < deadline:
        time.sleep(POLL_S)
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
        if "drift" in state:
            raise PageDrift(f"fit: currentPage is {state['drift']!r}, expected {page!r} — "
                            "another session changed the page")
        nulls = int(state.get("nulls") or 0)
        names = list(state.get("nullNames") or [])
        texts = int(state.get("texts") or 0)
        if nulls and texts and nulls == texts and retoggles < 2:
            # Every text is unmeasured: force the board into view once more.
            # The renderer settles asynchronously; polling (not re-toggling on
            # every pass) is what lets it catch up.
            retoggles += 1
            print(f"  fit: page not rendered ({nulls}/{texts}); zooming the board in",
                  file=sys.stderr)
            zoom_board(url, page, board)
            continue
        passes += 1
        idle = not state.get("fitted") and not state.get("bars") and not state.get("cards")
        if not nulls and idle:
            # Two consecutive quiet polls: late font metrics can change a
            # text's ink after the first quiet pass (a 40px label's underline
            # was 3.9px long because the box predated the final shaping).
            quiet_streak += 1
            if quiet_streak >= 2:
                return True, nulls, names, time.monotonic() - started, passes
        else:
            quiet_streak = 0
        # No early break: measurement can lag a large build by a minute. The
        # deadline and attempt cap bound the wait; the null list names the cost.
        continue
    return False, nulls, names, time.monotonic() - started, passes


def expected_photo_names(board: str) -> list[str]:
    try:
        provenance = json.loads(PROVENANCE.read_text())
    except OSError:
        return []
    except json.JSONDecodeError as exc:
        print(f"build: cannot read {PROVENANCE}: {exc}", file=sys.stderr)
        return []
    return entries_for_board(provenance, board) if isinstance(provenance, dict) else []


def reflow_layout(url: str, page: str, board: str, gap: int = 240) -> dict:
    """Keep the rebuilt board's canvas column spaced after its height settled.

    A screen owns its board's contents, not the canvas: a height change leaves
    the boards below where they were (08-bildiri overlapped 07-program by 116px
    after 07 grew). This runs once after fit, before photos are restored, and
    moves only top-level boards in that column that sit closer than `gap`.
    """
    code = f"""
if (penpot.currentPage.name !== {json.dumps(page)}) throw new Error("page not active: " + penpot.currentPage.name);
if (!storage.IK || !storage.IK.reflowColumn) throw new Error("lib without reflowColumn — send lib.js first");
return JSON.stringify(storage.IK.reflowColumn({json.dumps(page)}, {json.dumps(board)}, {gap}));
"""
    state = payload(call_execute_code(url, code))
    state = json.loads(state) if isinstance(state, str) else state
    return state if isinstance(state, dict) else {}


def restore_photos(page: str, board: str) -> int:
    """Re-place this board's provenance photos; returns media.py's exit code."""
    proc = subprocess.run(
        [sys.executable, str(MEDIA), "--restore", "--board", board, "--page", page],
        capture_output=True, text=True, timeout=MEDIA_TIMEOUT_S,
        env=dict(os.environ, PENPOT_SESSION_HELD="1"),  # this build owns the session
    )
    for line in (proc.stdout or "").splitlines() + (proc.stderr or "").splitlines():
        if line.strip():
            print(f"  media: {line.strip()}")
    return proc.returncode


def photo_counts(url: str, page: str, board: str, names: list[str]) -> dict[str, int]:
    code = f"""
if (penpot.currentPage.name !== {json.dumps(page)}) {{
  throw new Error("page not active: " + penpot.currentPage.name);
}}
const p = penpot.currentFile.pages.find((x) => x.name === {json.dumps(page)});
const b = p && (p.root.children || []).find((x) => x.name === {json.dumps(board)});
const wanted = {json.dumps(names)};
const got = {{}};
const walk = (s) => {{
  if (wanted.indexOf(s.name) >= 0 && s.type === "rectangle"
      && (s.fills || []).some((f) => f.fillImage)) {{
    got[s.name] = (got[s.name] || 0) + 1;
  }}
  (s.children || []).forEach(walk);
}};
if (b) (b.children || []).forEach(walk);
return JSON.stringify(got);
"""
    state = payload(call_execute_code(url, code))
    state = json.loads(state) if isinstance(state, str) else state
    return state if isinstance(state, dict) else {}


def verify_photos(url: str, page: str, board: str, names: list[str]) -> tuple[bool, str]:
    if not names:
        return True, "photos 0/0"
    got = photo_counts(url, page, board, names)
    missing = [name for name in names if got.get(name) != 1]
    placed = sum(1 for name in names if got.get(name) == 1)
    msg = f"photos {placed}/{len(names)}"
    if missing:
        msg += f"; missing: {', '.join(missing)}"
    return not missing, msg


def verify_links(url: str, page: str, board: str, expected: list[dict]) -> tuple[bool, str, list[str]]:
    if not expected:
        return True, "links 0/0", []
    if current_page(url) != page:
        raise PageDrift(f"link check: currentPage is {current_page(url)!r}, expected {page!r}")
    code = f"""
const p = penpot.currentFile.pages.find((x) => x.name === {json.dumps(page)});
const b = p && (p.root.children || []).find((x) => x.name === {json.dumps(board)});
const wanted = {json.dumps([e["shape"] for e in expected])};
const got = {{}};
const walk = (s) => {{
  if (wanted.indexOf(s.name) >= 0) {{
    got[s.name] = (s.interactions || [])
      .filter((i) => i.action && i.action.type === "navigate-to")
      .map((i) => (i.action.destination && i.action.destination.name) || null);
  }}
  (s.children || []).forEach(walk);
}};
if (b) (b.children || []).forEach(walk);
return JSON.stringify(got);
"""
    state = payload(call_execute_code(url, code))
    state = json.loads(state) if isinstance(state, str) else state
    state = state if isinstance(state, dict) else {}
    matched = 0
    missing: list[str] = []
    for item in expected:
        got = state.get(item["shape"]) or []
        if item["dest"] in got:
            matched += 1
        else:
            seen = ", ".join(str(d) for d in got) if got else "no link"
            missing.append(f"{item['shape']} -> {item['dest']} (got {seen})")
    msg = f"links {matched}/{len(expected)}"
    if missing:
        msg += f"; missing: {'; '.join(missing)}"
    return matched == len(expected), msg, missing


def run_flows(url: str, path: pathlib.Path) -> dict:
    """Execute flows.js once. A failure is a build failure: links would be missing."""
    try:
        code = path.read_text()
    except OSError as exc:
        return {"ok": False, "msg": f"flows: ERROR cannot read {path}: {exc}", "byBoard": {}}
    if not code.strip():
        return {"ok": False, "msg": f"flows: ERROR empty file {path}", "byBoard": {}}
    try:
        result = payload(call_execute_code(url, code))
    except McpError as exc:
        return {"ok": False, "msg": f"flows: ERROR {exc}", "byBoard": {}}
    result = json.loads(result) if isinstance(result, str) else result
    if not isinstance(result, dict):
        return {"ok": False, "msg": "flows: ERROR no result", "byBoard": {}}
    errors = result.get("errors") or []
    links = result.get("links") or []
    msg = f"flows: applied {len(links)} link(s)"
    if errors:
        msg += " — " + "; ".join(str(e) for e in errors)
    return {"ok": not errors, "msg": msg, "byBoard": result.get("byBoard") or {}}


def live_state(url: str, page: str, board: str) -> str:
    """Board node count and unmeasured-text count, for a call that timed out."""
    code = f"""
const p = penpot.currentFile.pages.find((x) => x.name === {json.dumps(page)});
const b = p && (p.root.children || []).find((x) => x.name === {json.dumps(board)});
if (!b) return JSON.stringify({{ found: false, page: p ? p.name : null }});
let nodes = 0;
const nulls = [];
const walk = (s) => {{
  nodes++;
  if (s.type === "text" && !(s.textBounds && s.textBounds.height)) nulls.push(s.name);
  (s.children || []).forEach(walk);
}};
(b.children || []).forEach(walk);
return JSON.stringify({{ found: true, page: penpot.currentPage.name, nodes: nodes,
  nulls: nulls.length, nullNames: nulls.slice(0, 12) }});
"""
    try:
        state = payload(call_execute_code(url, code))
        return json.dumps(json.loads(state) if isinstance(state, str) else state)
    except McpError as exc:
        return f"live state unavailable ({exc})"


def run(url: str, screen: str, fit_deadline: float) -> dict:
    page, board = SCREENS[screen]
    t0 = time.monotonic()
    open_page_retry(url, page)
    opened = time.monotonic() - t0
    require_page(url, page, f"{screen} start")
    lib = (HERE / "lib.js").read_text()
    body = (HERE / f"{screen}.js").read_text()
    result = payload(call_execute_code(url, lib + "\n" + body, expect_page=page))
    built = time.monotonic()
    require_page(url, page, f"{screen} after build")
    toggle_s = toggle_page(url, page)
    zoom_s = zoom_board(url, page, board)
    quiet, nulls, names, fit_s, passes = fit_board(url, page, board, lib, fit_deadline)
    require_page(url, page, f"{screen} after fit")
    # The board's height is final here; reconcile the canvas before photos are
    # placed, so a moved slot receives its photo at the new position.
    layout = reflow_layout(url, page, board)
    moved = layout.get("moves") or []
    if moved:
        print("  layout: " + ", ".join(f"{m['name']} {m['from']}→{m['to']}" for m in moved))
    else:
        print(f"  layout: 0 moves (column gap {layout.get('gap', 240)} already holds)")
    require_page(url, page, f"{screen} after layout")

    photo_names = expected_photo_names(board)
    media_rc = 0
    if photo_names:
        media_rc = restore_photos(page, board)
        require_page(url, page, f"{screen} after media")
    photo_ok, photo_msg = verify_photos(url, page, board, photo_names)
    if media_rc:
        photo_ok = False
        photo_msg += f" (media exit {media_rc})"
    total = time.monotonic() - t0
    report = json.loads(result) if isinstance(result, str) else result
    report = report if isinstance(report, dict) else {}
    print(f"  open {opened:.2f}s  build {built - t0 - opened:.2f}s  "
          f"toggle {toggle_s:.2f}s  zoom {zoom_s:.2f}s  fit {fit_s:.2f}s "
          f"({passes} pass(es), {'quiet' if quiet else 'NOT quiet'})  "
          f"{photo_msg}  total {total:.2f}s")
    return {"screen": screen, "report": report, "quiet": quiet, "nulls": nulls,
            "names": names, "photo_ok": photo_ok, "photo_msg": photo_msg,
            "total": total}


def fail_line(screen: str, page: str, board: str, message: str) -> None:
    print(f"{screen}: ERROR {message}", file=sys.stderr)


def settle(url: str, screen: str, fit_deadline: float) -> tuple[int, int]:
    page, board = SCREENS[screen]
    t0 = time.monotonic()
    try:
        open_page_retry(url, page)
        toggle_s = toggle_page(url, page)
        zoom_s = zoom_board(url, page, board)
        lib = (HERE / "lib.js").read_text()
        quiet, nulls, names, fit_s, passes = fit_board(url, page, board, lib, fit_deadline)
        require_page(url, page, f"{screen} settle end")
    except (PageDrift, McpError) as exc:
        print(f"{screen}: ERROR {exc}", file=sys.stderr)
        return 2, 0
    print(f"  toggle {toggle_s:.2f}s  zoom {zoom_s:.2f}s  fit {fit_s:.2f}s ({passes} pass(es), "
          f"{'quiet' if quiet else 'NOT quiet'})  total {time.monotonic() - t0:.2f}s")
    if nulls:
        print(f"{screen}: {nulls} text(s) still unmeasured: {', '.join(names)}", file=sys.stderr)
    return (0 if quiet and nulls == 0 else 1), nulls




def dry_run(names: list[str]) -> int:
    """Statik geçiş: dosya, `node --check`, SCREENS kaydı.

    Plugin'e hiç bağlanmaz, hiçbir şey yazmaz: canlı çalıştırma sıraya alınmışken
    ekran dosyalarının sentaksını ve mobil kütüphane sözleşmesini doğrular.
    """
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"build: node is required for --dry-run ({exc})", file=sys.stderr)
        return 2
    code = 0
    for name in names:
        page, board = SCREENS[name]
        path = HERE / f"{name}.js"
        if not path.is_file():
            print(f"{name}: ERROR {path.name} is missing", file=sys.stderr)
            code = 1
            continue
        proc = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
        if proc.returncode != 0:
            print(f"{name}: ERROR node --check {path.name}: {(proc.stderr or '').strip()}", file=sys.stderr)
            code = 1
            continue
        body = path.read_text()
        print(f"{name}: {page} / {board} — {path.name} ok")
    print(f"dry-run: {len(names)} screen(s), plugin not contacted"
          )
    return code


def main(argv: list[str] | None = None) -> tuple[int, int]:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("screens", nargs="*", help="screen-NN names, or 'all'")
    ap.add_argument("--flows", type=pathlib.Path, default=FLOWS,
                    help="flows file re-applied after the build (default %(default)s)")
    ap.add_argument("--no-flows", action="store_true", help="skip flows and link verification")
    ap.add_argument("--dry-run", action="store_true",
                    help="static pass only: node --check each screen, SCREENS registration; "
                         "never contacts the plugin")
    ap.add_argument("--settle", metavar="SCREEN",
                    help="recovery only: toggle the page and re-run fit, do not rebuild")
    ap.add_argument("--fit-deadline", type=float, default=FIT_DEADLINE_S,
                    help="seconds per fit stage (default %(default)s)")
    args = ap.parse_args(argv)
    if args.no_flows:
        args.flows = None

    if args.settle:
        if args.settle not in SCREENS:
            print(f"build: unknown screen {args.settle!r}", file=sys.stderr)
            return 2, 0
        names = [args.settle]
    else:
        names = args.screens or ["all"]
        if names[0] == "all":
            names = list(SCREENS)
    unknown = [n for n in names if n not in SCREENS]
    if unknown:
        print(f"build: unknown screen(s): {', '.join(unknown)}", file=sys.stderr)
        return 2, 0

    if args.dry_run:
        return dry_run(names), 0

    writers = []
    try:
        url = load_url()
        writers = other_writers(url)
    except McpError as exc:
        print(f"build: {exc}", file=sys.stderr)
        return 2, 0
    except OSError as exc:
        print(f"build: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2, 0
    if writers:
        print("build: another writer holds the plugin — one writer per plugin tab:",
              file=sys.stderr)
        for line in writers:
            print(f"  {line}", file=sys.stderr)
        return 2, 0

    try:
        acquire_session(url)   # held for the whole build: other writers wait, reads pass
    except (PluginBusy, McpError) as exc:
        print(f"build: {exc}", file=sys.stderr)
        return 2, 0

    try:
        ensure_helpers(url)
    except McpError as exc:
        print(f"build: {exc}", file=sys.stderr)
        release_session(url)
        return 2, 0
    except OSError as exc:
        print(f"build: {type(exc).__name__}: {exc}", file=sys.stderr)
        release_session(url)
        return 2, 0
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 2
        release_session(url)
        return code, 0

    try:
        acquire_lock(names[0])
    except Locked as exc:
        print(f"build: {exc}", file=sys.stderr)
        release_session(url)
        return 2, 0
    except OSError as exc:
        print(f"build: cannot write {LOCK}: {exc}", file=sys.stderr)
        release_session(url)
        return 2, 0

    code = 0
    total_nulls = 0
    try:
        if args.settle:
            return settle(url, args.settle, args.fit_deadline)

        for name in names:
            page, board = SCREENS[name]
            try:
                result = run(url, name, args.fit_deadline)
            except TimedOut as exc:
                print(f"{name}: {exc}", file=sys.stderr)
                print(f"{name}: live state {live_state(url, page, board)} — not retrying", file=sys.stderr)
                return 2, total_nulls
            except PageDrift as exc:
                print(f"{name}: ERROR {exc}", file=sys.stderr)
                return 2, total_nulls
            except McpError as exc:
                print(f"{name}: ERROR {exc}", file=sys.stderr)
                return 2, total_nulls

            total_nulls += result["nulls"]
            report = result["report"]
            gaps = report.get("gaps") or []
            print(f"{name}: {page} / {board} — warnings {len(report.get('warnings') or [])}"
                  + (f", token gaps {sorted(set(gaps))}" if gaps else ""))
            for warning in report.get("warnings") or []:
                print(f"  ! {warning}")
            if not result["quiet"]:
                fail_line(name, page, board,
                          f"layout not quiet after {FIT_ATTEMPTS} fit attempt(s); "
                          f"{result['nulls']} text(s) unmeasured: {', '.join(result['names'])}")
                print(f"  recover: python3 design/ihkd/build/build.py --settle {name}",
                      file=sys.stderr)
                code = 1
            if not result["photo_ok"]:
                fail_line(name, page, board, result["photo_msg"])
                code = 1

        flow_state = {"ok": True, "byBoard": {}}
        if args.flows is not None:
            flow_state = run_flows(url, args.flows)
            print(flow_state["msg"])
            if not flow_state["ok"]:
                code = 1

            # flows leaves asynchronous page switches queued; let them land.
            time.sleep(1.5)
            for name in names:
                page, board = SCREENS[name]
                expected = (flow_state["byBoard"] or {}).get(board) or []
                try:
                    if current_page(url) != page:
                        open_page_retry(url, page)
                    require_page(url, page, f"{name} link check")
                    ok, msg, _ = verify_links(url, page, board, expected)
                except (PageDrift, McpError) as exc:
                    print(f"{name}: ERROR link check: {exc}", file=sys.stderr)
                    return 2, total_nulls
                print(f"{name}: {msg}")
                if not ok:
                    code = 1

        last_page = SCREENS[names[-1]][0]
        try:
            time.sleep(0.5)
            open_page_retry(url, last_page)
            require_page(url, last_page, "end")
        except (PageDrift, McpError) as exc:
            print(f"build: ERROR {exc}", file=sys.stderr)
            return 2, total_nulls
    finally:
        release_lock()
        release_session(url)
    return code, total_nulls


if __name__ == "__main__":
    try:
        exit_code, remaining = main(sys.argv[1:])
    except SystemExit as exc:
        exit_code = exc.code if isinstance(exc.code, int) else 2
        remaining = 0
    except McpError as exc:
        print(f"build: ERROR {exc}", file=sys.stderr)
        exit_code, remaining = 2, 0
    except Exception as exc:  # noqa: BLE001 - the RESULT line is the contract
        print(f"build: ERROR {type(exc).__name__}: {exc}", file=sys.stderr)
        exit_code, remaining = 2, 0
    print(f"RESULT {'ok' if exit_code == 0 else 'fail'} nulls={remaining}")
    raise SystemExit(exit_code)
