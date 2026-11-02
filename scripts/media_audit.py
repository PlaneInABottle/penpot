#!/usr/bin/env python3
"""Cross-check photo slots before importing: build files vs media table vs live boards.

Catches the two failure modes that each waste a full build+import cycle:
a missing slot (import fails with `slot not found`) and a nested slot (the
importer only looks at direct board children, so it never finds it).

    media-audit.py --build design/ihkd/build --media design/ihkd/tools/media.py
    media-audit.py --build design/ihkd/build --media design/ihkd/tools/media.py --live --provenance design/ihkd/media/provenance.json

Conventions (ihkd-style, but the script only assumes them, it does not hard-code
them): build files call `S.photo(<parent>, "<img-name>", ...)`; the media tool
exposes a module-level `IMAGES = {name: (query, page, board), ...}` dict;
a placed photo keeps the slot name and carries an image fill, an empty slot does not.

Exit codes: 0 all consistent, 1 mismatch found, 2 environment problem.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import pathlib
import re
import sys
import urllib.error

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from penpot_exec import McpError, call_execute_code, ensure_helpers, fail, load_url, payload  # noqa: E402

SLOT_RE = re.compile(r"""S\.photo\(\s*[A-Za-z_$][\w$]*\s*,\s*"([^"]+)"|S\.photo\(\s*"([^"]+)\"""")

LIVE = """
const out = {};
__PAGES__.forEach(pg => {
  const page = penpot.currentFile.pages.find(p => p.name === pg);
  if (!page) { out[pg] = { error: "page not found" }; return; }
  (page.root.children || []).forEach(b => {
    if (b.type !== "board") return;
    (b.children || []).forEach(s => {
      if (/^img-/.test(s.name || "")) {
        const hasImage = !!((s.fills || []).find(f => f.fillImage));
        (out[b.name] = out[b.name] || []).push({ name: s.name, image: hasImage });
      }
    });
  });
});
return JSON.stringify(out);
"""


def load_table(path: pathlib.Path) -> dict:
    spec = importlib.util.spec_from_file_location("media_table", path)
    if spec is None or spec.loader is None:
        fail(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except Exception as exc:
        fail(f"{path}: {exc!r}")
    table = getattr(module, "IMAGES", None)
    if not isinstance(table, dict):
        fail(f"{path} exposes no IMAGES dict")
    return table


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", required=True, type=pathlib.Path, help="directory with screen-*.js files")
    ap.add_argument("--media", required=True, type=pathlib.Path, help="media tool python file exposing IMAGES")
    ap.add_argument("--live", action="store_true", help="also check live boards (read-only)")
    ap.add_argument("--provenance", type=pathlib.Path, help="provenance.json to check for placement records")
    ap.add_argument("--screens", type=pathlib.Path, help="build.py holding the SCREENS map (default: <build>/build.py)",
                      default=None)
    args = ap.parse_args(argv)

    files = sorted(args.build.glob("screen-*.js"))
    if not files:
        fail(f"no screen files in {args.build}")
    runner = args.screens or (args.build / "build.py")
    screen_board: dict[str, tuple[str, str]] = {}
    try:
        for m in re.finditer(r'"(screen-\d+)":\s*\("([^"]+)",\s*"([^"]+)"\)', runner.read_text()):
            screen_board[m.group(1)] = (m.group(2), m.group(3))
    except OSError:
        pass
    slots: dict[str, list[str]] = {}
    nested: list[tuple[str, str]] = []
    slot_boards: dict[str, set[tuple[str, str]]] = {}
    for f in files:
        text = f.read_text()
        screen = f.stem
        for m in re.finditer(r'S\.photo\(\s*([A-Za-z_$][\w$]*)?\s*,?\s*"([^"]+)"', text):
            parent, name = m.group(1), m.group(2)
            slots.setdefault(name, []).append(f.name)
            if screen in screen_board:
                slot_boards.setdefault(name, set()).add(screen_board[screen])
            if parent and parent != "pb":
                nested.append((name, f"{f.name}:{parent}"))

    table = load_table(args.media)

    problems = 0
    print(f"slots in build files: {len(slots)}  table entries: {len(table)}")
    for name, where in sorted(slots.items()):
        if name not in table:
            print(f"  MISSING-TABLE  {name} (in {', '.join(where)}): no IMAGES entry, import impossible")
            problems += 1
    for name, spec in sorted(table.items()):
        page, board = spec[1], spec[2]
        if name not in slots:
            print(f"  MISSING-SLOT   {name} (table -> {page} / {board}): no S.photo in any build file")
            problems += 1
    for name, where in sorted(set(nested)):
        print(f"  NESTED-SLOT    {name} ({where}): parent is not the page board — importer only sees direct board children")
        problems += 1

    if args.live:
        try:
            url = load_url()
            ensure_helpers(url)
        except McpError as exc:
            fail(str(exc))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            fail(f"{type(exc).__name__}: {exc}")
        pages = sorted({spec[1] for spec in table.values()} | {pg for boards in slot_boards.values() for pg, _ in boards})
        try:
            live = payload(call_execute_code(url, LIVE.replace("__PAGES__", json.dumps(pages))))
        except McpError as exc:
            fail(str(exc))
        live = json.loads(live) if isinstance(live, str) else live
        placed = {s["name"] for shapes in live.values() if isinstance(shapes, list) for s in shapes if s.get("image")}
        empty = {s["name"] for shapes in live.values() if isinstance(shapes, list) for s in shapes if not s.get("image")}
        want: dict[str, set[tuple[str, str]]] = {}
        for name, spec in table.items():
            want.setdefault(name, set()).add((spec[1], spec[2]))
        for name, boards in slot_boards.items():
            want.setdefault(name, set()).update(boards)
        for name in sorted(want):
            for page, board in sorted(want[name]):
                key = (page, board, name)
                if name in placed:
                    print(f"  live: {name} on {board} — photo placed")
                elif name in empty:
                    print(f"  live: {name} on {board} — EMPTY SLOT (import it)")
                    problems += 1
                else:
                    print(f"  live: {name} on {board} — NOT ON BOARD (slot never built or misnamed)")
                    problems += 1
            if name in table:
                used = slot_boards.get(name, set())
                if used and (table[name][1], table[name][2]) not in used:
                    print(f"  NOTE: {name} table points at {table[name][1]}/{table[name][2]} but files place it on {sorted(used)} — use --board override")
        for name in sorted(table):
            if name not in want:
                print(f"  live: {name} — unused anywhere (table-only entry)")
                problems += 1

    if args.provenance:
        try:
            prov = json.loads(args.provenance.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"{args.provenance}: {exc}")
        names = {str(v.get("board", "")) + "/" + str(k).split("@")[0] for k, v in prov.items() if isinstance(v, dict)}
        for name, spec in sorted(table.items()):
            if f"{spec[2]}/{name}" not in names and name not in {str(k).split("@")[0] for k in prov}:
                print(f"  NO-PROVENANCE  {name} on {spec[2]}: placed but unrecorded (or never placed)")
                problems += 1

    print("inconsistent" if problems else "consistent")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
