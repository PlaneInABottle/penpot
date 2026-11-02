#!/usr/bin/env python3
"""Runtime contrast audit for a Penpot page: real text color vs real background.

`check_contrast.py` verifies token pairs you list by hand; this walks every text
shape on the page, resolves its painted fill against the nearest opaque ancestor
fill, and reports the WCAG ratio. Catches the class hand-picked lists miss (a
secondary token used on a background nobody listed).

    contrast_audit.py --page Kurumsal [--min 4.5]

Read-only (named page, never switches the view). Text over image fills is
reported as manual-check, not a number. Large text (>=24px, or >=19px semibold+)
is held to 3.0, everything else to --min (default 4.5).

Exit codes: 0 no failing pairs, 1 failures found, 2 environment problem.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.error

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from penpot_exec import McpError, call_execute_code, ensure_helpers, fail, load_url, payload  # noqa: E402

COLLECT = """
const page = penpot.currentFile.pages.find(p => p.name === __PAGE__);
if (!page) throw new Error("page not found: " + __PAGE__);
const out = [];
const solids = [];
let seq = 0;
const walk = (s, chain, boardName) => {
  const order = seq++;
  const fills = (s.fills || []).filter(f => (f.fillOpacity || 0) > 0.5 && f.fillColor);
  if ((s.type === "rectangle" || s.type === "board") && fills.length && !fills[0].fillImage) {
    solids.push({ order, board: boardName, fill: fills[0].fillColor,
      x: s.x, y: s.y, w: s.width, h: s.height });
  }
  const kids = s.children || [];
  if (s.type === "text") {
    // true background = topmost opaque rect under the ink centre, regardless of
    // nesting (a sibling pill paints exactly like an ancestor panel)
    const cx = s.textBounds ? s.textBounds.x + s.textBounds.width / 2 : s.x + s.width / 2;
    const cy = s.textBounds ? s.textBounds.y + s.textBounds.height / 2 : s.y + s.height / 2;
    let bg = null, bgImage = false;
    solids.forEach(r => {
      if (r.board === boardName && cx >= r.x && cx <= r.x + r.w && cy >= r.y && cy <= r.y + r.h) bg = r.fill;
    });
    out.push({
      name: s.name, board: chain.length ? chain[0].name : null,
      size: Number(s.fontSize) || 0, variant: String(s.fontVariantId || ""),
      fg: (s.fills && s.fills[0] && s.fills[0].fillColor) || null,
      overImage: !!((s.fills || []).find(f => f.fillImage)),
      bg: bg, bgImage: bgImage,
    });
  }
  kids.forEach(c => walk(c, chain.concat([s]), boardName));
};
(page.root.children || []).forEach(s => walk(s, [], null));

return JSON.stringify(out);
"""


def lum(hex_color: str) -> float:
    c = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [(v / 12.92 if v <= 0.0405 else ((v + 0.055) / 1.055) ** 2.4) for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(fg: str, bg: str) -> float:
    light, dark = sorted([lum(fg), lum(bg)], reverse=True)
    return round((light + 0.05) / (dark + 0.05), 2)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--page", required=True)
    ap.add_argument("--min", type=float, default=4.5)
    ap.add_argument("--ignore", action="append", default=[],
                    help="skip shapes whose name starts with this prefix (documented decorative only); repeatable")
    args = ap.parse_args(argv)

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

    fails, manual, total, skipped = [], [], 0, 0
    for n in nodes:
        if not n.get("fg") or not n.get("bg"):
            continue
        if any(n.get("name", "").startswith(p) for p in (args.ignore or [])):
            skipped += 1
            continue
        if n.get("overImage") or n.get("bgImage"):
            manual.append(n)
            continue
        total += 1
        large = n["size"] >= 24 or (n["size"] >= 19 and n["variant"] in ("500", "600", "700"))
        need = 3.0 if large else args.min
        got = ratio(n["fg"], n["bg"])
        if got < need:
            fails.append((n["board"], n["name"], n["fg"], n["bg"], got, need))

    print(f"page: {args.page}  texts checked: {total}  failing: {len(fails)}  over-image (manual): {len(manual)}  ignored: {skipped}")
    for board, name, fg, bg, got, need in fails[:30]:
        print(f"  FAIL {board} / {name}: {fg} on {bg} = {got} (needs {need})")
    if len(fails) > 30:
        print(f"  ... and {len(fails) - 30} more")
    for n in manual[:10]:
        print(f"  MANUAL {n['board']} / {n['name']}: over image fill, check by eye")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
