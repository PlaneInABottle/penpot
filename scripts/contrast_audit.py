#!/usr/bin/env python3
"""Runtime contrast audit for a Penpot page: real text color vs real background.

`check_contrast.py` verifies token pairs you list by hand; this walks every text
shape on the page, resolves the topmost painted layer under the ink centre
inside the text's own top-level board, and reports the WCAG ratio. Catches the
class hand-picked lists miss (a secondary token used on a background nobody
listed, or a dark title that actually sits on a photo).

    contrast_audit.py --page Kurumsal [--min 4.5]

Read-only (named page, never switches the view) and does not inject helpers.
Resolution is paint-order and board scoped: an ancestor board fill counts, a
sibling card painted before the text counts, and a layer in another board never
does. Shape opacity multiplies ancestor, shape and fill opacity; image,
gradient, alpha-colour, translucent and unknown paints are reported as
MANUAL/unknown, never as a fabricated solid ratio. Those items are not a pass:
the printed verdict says so, and the definition of done requires an eye check.

Large text (>=24px, or >=19px semibold+) is held to 3.0, everything else to
--min (default 4.5).

Exit codes: 0 no automatic failure (manual items may remain — read the verdict),
1 failing pair, 2 environment problem.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import urllib.error

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from penpot_exec import McpError, call_execute_code, fail, load_url, payload  # noqa: E402

COLLECT = """
const page = penpot.currentFile.pages.find(p => p.name === __PAGE__);
if (!page) throw new Error("page not found: " + __PAGE__);
const out = { texts: [], layers: [] };
let seq = 0;
const num = (value, fallback) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};
const kindOf = (fill, paints) => {
  if (paints > 1) return "unsupported";
  if (fill.fillImage) return "image";
  if (fill.fillColorGradient) return "gradient";
  if (fill.fillColor) return "solid";
  return "unsupported";
};
const walk = (s, boardId, boardName, ancestorOpacity) => {
  const order = seq++;
  // Scope is the TOP-LEVEL board, so a nested panel shares its ancestor's
  // background while a neighbouring board can never leak into this one.
  const bid = boardId !== null ? boardId
    : (s.type === "board" ? s.id : "root:" + s.id);
  const bname = boardId !== null ? boardName
    : (s.type === "board" ? s.name : null);
  // Penpot's shape.opacity multiplies every fill and every descendant; a
  // collector that reads fillOpacity alone reports a fabricated solid ratio.
  const inherited = ancestorOpacity * num(s.opacity, 1);
  const paints = (s.fills || []).filter(f => num(f.fillOpacity, 1) > 0);
  const fill = paints[0] || null;
  const opacity = inherited * (fill ? num(fill.fillOpacity, 1) : 1);
  const kind = fill ? kindOf(fill, paints.length) : null;
  // Any non-text shape with a visible fill paints a layer; dropping an
  // unfamiliar shape type would let a text resolve against the wrong ancestor.
  if (s.type !== "text" && fill) {
    out.layers.push({ order, boardId: bid, board: bname, name: s.name,
      kind, fill: fill.fillColor || null,
      opacity, x: s.x, y: s.y, w: s.width, h: s.height });
  }
  if (s.type === "text") {
    const tb = s.textBounds;
    const cx = tb ? tb.x + tb.width / 2 : s.x + s.width / 2;
    const cy = tb ? tb.y + tb.height / 2 : s.y + s.height / 2;
    out.texts.push({ order, boardId: bid, board: bname, name: s.name,
      size: Number(s.fontSize) || 0, variant: String(s.fontVariantId || ""),
      fg: fill && fill.fillColor ? fill.fillColor : null,
      fgKind: kind, fgPaints: paints.length,
      fgOpacity: opacity, cx, cy });
  }
  (s.children || []).forEach(c => walk(c, bid, bname, inherited));
};
(page.root.children || []).forEach(s => walk(s, null, null, 1));
return JSON.stringify(out);
"""

ALPHA_HEX = re.compile(r"^#[0-9A-Fa-f]{8}$")
SOLID_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def lum(hex_color: str) -> float:
    c = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [(v / 12.92 if v <= 0.0405 else ((v + 0.055) / 1.055) ** 2.4) for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(fg: str, bg: str) -> float:
    light, dark = sorted([lum(fg), lum(bg)], reverse=True)
    return round((light + 0.05) / (dark + 0.05), 2)


def contains(layer: dict, x: float, y: float) -> bool:
    return (layer["x"] <= x <= layer["x"] + layer["w"]
            and layer["y"] <= y <= layer["y"] + layer["h"])


def resolve(data: dict, min_ratio: float = 4.5, ignore: tuple[str, ...] = ()) -> dict:
    """Pure resolution: paint-order + board-scoped, no plugin. Returns counts and rows."""
    texts = data.get("texts") or []
    layers = data.get("layers") or []
    by_scope: dict[object, list[dict]] = {}
    for layer in layers:
        by_scope.setdefault(layer.get("boardId"), []).append(layer)
    checked, ignored = 0, 0
    fails: list[dict] = []
    manual: list[dict] = []
    for text in texts:
        name = text.get("name", "?")
        board = text.get("board")
        if any(name.startswith(prefix) for prefix in ignore):
            ignored += 1
            continue
        def note(reason: str) -> None:
            manual.append({"board": board, "name": name, "reason": reason})
        if text.get("fgPaints", 1) != 1:
            note("text has multiple/unknown fills")
            continue
        if text.get("fgKind") == "image":
            note("text fill is an image")
            continue
        if text.get("fgKind") == "gradient":
            note("text fill is a gradient")
            continue
        if text.get("fgKind") == "unsupported":
            note("text fill has an unsupported paint")
            continue
        if not text.get("fg"):
            note("no solid text fill")
            continue
        if ALPHA_HEX.match(str(text["fg"])):
            note(f"text fill carries alpha {text['fg']!r} (unsupported compositing)")
            continue
        if not SOLID_HEX.match(str(text["fg"])):
            note(f"unsupported text colour {text['fg']!r}")
            continue
        if float(text.get("fgOpacity", 1)) < 0.99:
            note(f"translucent text fill (opacity {float(text.get('fgOpacity', 1)):g})")
            continue
        under = [layer for layer in by_scope.get(text.get("boardId"), [])
                 if layer.get("order", 0) < text.get("order", 0)
                 and contains(layer, text.get("cx", 0), text.get("cy", 0))]
        if not under:
            note("no painted shape under the ink centre")
            continue
        top = max(under, key=lambda layer: layer.get("order", 0))
        if top.get("kind") == "image":
            note(f"over image fill {top.get('name', '?')}")
            continue
        if top.get("kind") == "gradient":
            note(f"over gradient fill {top.get('name', '?')}")
            continue
        if top.get("kind") == "unsupported":
            note(f"over unsupported painted layer {top.get('name', '?')}")
            continue
        if ALPHA_HEX.match(str(top.get("fill") or "")):
            note(f"over alpha colour {top.get('fill')!r} (unsupported compositing)")
            continue
        if not SOLID_HEX.match(str(top.get("fill") or "")):
            note(f"unsupported background colour {top.get('fill')!r}")
            continue
        if float(top.get("opacity", 1)) < 0.99:
            note(f"over translucent layer {top.get('name', '?')} "
                 f"(opacity {float(top.get('opacity', 1)):g})")
            continue
        try:
            got = ratio(text["fg"], top["fill"])
        except (ValueError, TypeError, IndexError):
            note(f"unsupported colour {text['fg']!r} on {top.get('fill')!r}")
            continue
        checked += 1
        size = float(text.get("size") or 0)
        large = size >= 24 or (size >= 19 and text.get("variant") in ("500", "600", "700"))
        need = 3.0 if large else min_ratio
        if got < need:
            fails.append({"board": board, "name": name, "fg": text["fg"],
                          "bg": top["fill"], "ratio": got, "need": need})
    return {"checked": checked, "ignored": ignored, "fails": fails, "manual": manual,
            "total": len(texts)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--page", required=True)
    ap.add_argument("--min", type=float, default=4.5)
    ap.add_argument("--ignore", action="append", default=[],
                    help="skip shapes whose name starts with this prefix (documented decorative only); repeatable")
    args = ap.parse_args(argv)

    try:
        url = load_url()
        data = payload(call_execute_code(
            url, COLLECT.replace("__PAGE__", json.dumps(args.page)), write=False))
        if not isinstance(data, dict) or not isinstance(data.get("texts"), list):
            fail("collector returned no text/layer report")
    except McpError as exc:
        fail(str(exc))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        fail(f"{type(exc).__name__}: {exc}")

    report = resolve(data, args.min, tuple(args.ignore or []))
    fails, manual = report["fails"], report["manual"]
    print(f"page: {args.page}  texts: {report['total']}  checked: {report['checked']}  "
          f"failing: {len(fails)}  manual/unknown: {len(manual)}  ignored: {report['ignored']}")
    for row in fails[:30]:
        print(f"  FAIL {row['board']} / {row['name']}: {row['fg']} on {row['bg']} = "
              f"{row['ratio']} (needs {row['need']})")
    if len(fails) > 30:
        print(f"  ... and {len(fails) - 30} more")
    for row in manual[:10]:
        print(f"  MANUAL {row['board']} / {row['name']}: {row['reason']}")
    if len(manual) > 10:
        print(f"  ... and {len(manual) - 10} more manual item(s)")
    if fails:
        print("verdict: FAIL — automatic contrast failures above")
    elif manual:
        print(f"verdict: MANUAL ({len(manual)}) — not a pass; check each item by eye")
    elif report["checked"] == 0:
        print("verdict: NOTHING CHECKED — no automatic pair resolved; not a pass")
    else:
        print("verdict: PASS — every checked text resolved to an opaque solid background")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
