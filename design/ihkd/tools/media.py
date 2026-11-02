#!/usr/bin/env python3
"""Fetch, grade and place Pexels photography for the İHKD boards.

    python3 design/ihkd/tools/media.py --list
    python3 design/ihkd/tools/media.py --only img-echo --board 01-ana-sayfa --page Kurumsal
    python3 design/ihkd/tools/media.py --all
    python3 design/ihkd/tools/media.py --restore --board 13-kilavuzlar --page Akademi

Each image is downloaded at 2x the placement size, cropped to the slot's aspect, graded to
the project's cool clinical look (light desaturation, +contrast, neutral shadows) and
uploaded into the board, replacing the placeholder with the same name. Provenance is
written to design/ihkd/media/provenance.json. Needs `PEXELS_API_KEY` and a connected
plugin; a graded JPEG is cached per name/size/source, so a rebuild does not need the
network.

`--restore` re-places exactly the photos recorded for one board in provenance
(`name@board` keys), using the pinned source URL — the lossless-rebuild path called by
build.py. Provenance keys are `name@board`; the bare `board` key is not a placement
record.

Exit codes: 0 placed, 1 board/slot missing or placement failed, 2 environment or transport.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from penpot_exec import McpError, call_execute_code, ensure_helpers, fail, load_url, payload  # noqa: E402

PEXELS = "https://api.pexels.com/v1/search"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

# name -> (query or pinned URL, page, board, credit)
IMAGES = {
    "img-echo": ("https://images.pexels.com/photos/6129683/pexels-photo-6129683.jpeg", "Kurumsal", "01-ana-sayfa", "https://www.pexels.com/photo/6129683/ by RDNE Stock project"),
    "img-hero": ("https://images.pexels.com/photos/20733081/pexels-photo-20733081.jpeg", "Kurumsal", "01-ana-sayfa", "https://www.pexels.com/photo/20733081/ by BBSO"),
    "img-journal": ("https://images.pexels.com/photos/3860983/pexels-photo-3860983.jpeg", "Kurumsal", "01-ana-sayfa", "https://www.pexels.com/photo/3860983/ by Robert Munteanu"),
    "img-round": ("internal medicine ward round doctors", "İçerik", "15-haberler"),
    "img-cath": ("catheterization laboratory angiography", "Kongre", "06-kongre"),
    "img-hall": ("medical conference audience lecture hall", "Kongre", "06-kongre"),
    "img-desk": ("stethoscope electrocardiogram paper desk", "Akademi", "13-kilavuzlar"),
    "img-issue": ("https://images.pexels.com/photos/3860983/pexels-photo-3860983.jpeg", "Akademi", "14-dergi", "https://www.pexels.com/photo/3860983/ by Robert Munteanu"),
    "img-lab": ("https://images.pexels.com/photos/28585011/pexels-photo-28585011.jpeg", "Akademi", "12-kurs-detay", "https://www.pexels.com/photo/28585011/ by Marta Branco"),
    "img-angio": ("https://images.pexels.com/photos/39459346/pexels-photo-39459346.jpeg", "Kurumsal", "05-grup-detay", "https://www.pexels.com/photo/39459346/ by Stéf -b."),
    "img-corridor": ("hospital corridor morning light", "Kongre", "10-konaklama"),
    "img-seminar": ("doctors small group seminar meeting", "Akademi", "11-akademi"),
    "img-team": ("two doctors reviewing images screen", "İçerik", "16-makale"),
    "img-auth": ("cardiology monitor hospital equipment", "Üyelik", "19-giris"),
    "img-venue": ("convention center exterior modern", "Kongre", "10-konaklama"),
}


class PlaceError(Exception):
    """A finding: board, slot or placement failed (exit 1), not transport."""


def key_for(name: str, board: str) -> str:
    return f"{name}@{board}"


def entries_for_board(provenance: dict, board: str) -> list[str]:
    """Photo names recorded for one board. Only `name@board` keys are placements."""
    names: list[str] = []
    for key, record in provenance.items():
        if "@" not in key or not isinstance(record, dict) or record.get("board") != board:
            continue
        name = key.split("@", 1)[0]
        if name not in names:
            names.append(name)
    return sorted(names)


def pexels(query: str) -> tuple[str, str]:
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        fail("PEXELS_API_KEY is not set")
    url = f"{PEXELS}?{urllib.parse.urlencode({'query': query, 'per_page': 5, 'orientation': 'landscape'})}"
    req = urllib.request.Request(url, headers={"Authorization": key, "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = json.loads(r.read())
    except urllib.error.HTTPError as exc:
        fail(f"Pexels HTTP {exc.code}")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        fail(f"{type(exc).__name__}: {exc}")
    photos = body.get("photos") or []
    if not photos:
        fail(f"no Pexels result for {query!r}")
    p = photos[0]
    return p["src"]["original"], f"https://www.pexels.com/photo/{p['id']}/ by {p['photographer']}"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        fail(f"image fetch {type(exc).__name__}: {exc}")


def grade(data: bytes, w: int, h: int, quality: int = 58, limit: int = 88000) -> bytes:
    """Crop to the slot's aspect and apply the project's cool clinical grade."""
    from io import BytesIO

    from PIL import Image, ImageEnhance

    im = Image.open(BytesIO(data)).convert("RGB")
    target = min(1000, max(720, round(1.5 * max(w, h))))
    if max(im.size) > target:
        im = im.resize((round(im.width * target / max(im.size)), round(im.height * target / max(im.size))), Image.LANCZOS)
    want = w / h
    have = im.width / im.height
    if have > want:
        nw = round(im.height * want)
        im = im.crop(((im.width - nw) // 2, 0, (im.width - nw) // 2 + nw, im.height))
    else:
        nh = round(im.width / want)
        im = im.crop((0, max(0, (im.height - nh) // 3), im.width, max(0, (im.height - nh) // 3) + nh))
    im = ImageEnhance.Color(im).enhance(0.62)
    im = ImageEnhance.Contrast(im).enhance(1.12)
    im = ImageEnhance.Brightness(im).enhance(0.97)
    # lift the shadow end toward the canvas so photos sit on the same surface
    r, g, b = im.split()
    def lift(ch):
        return ch.point(lambda v: min(255, round(v * 0.96 + 5)))
    im = Image.merge("RGB", (lift(r), lift(g), lift(b)))
    # the MCP request body tops out near 100 KB of base64; step down until it fits
    q = quality
    while True:
        out = BytesIO()
        im.save(out, "JPEG", quality=q, optimize=True, progressive=True)
        blob = out.getvalue()
        if len(blob) * 4 / 3 < limit or q <= 30:
            return blob
        q -= 8


def cached_path(name: str, w: int, h: int, src: str) -> pathlib.Path:
    digest = hashlib.sha1(src.encode()).hexdigest()[:10]
    return HERE.parent / "media" / "cache" / f"{name}-{w}x{h}-{digest}.jpg"


def graded_bytes(name: str, w: int, h: int, src: str, refresh: bool = False) -> bytes:
    """The graded JPEG. Cache key carries the source, so a new photo is not masked."""
    path = cached_path(name, w, h, src)
    if path.is_file() and path.stat().st_size and not refresh:
        return path.read_bytes()
    data = grade(fetch(src), w, h)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data


FIND_SLOT = """
const findSlot = (root, name) => {
  if (root.name === name) return root;
  for (const c of (root.children || [])) {
    const hit = findSlot(c, name);
    if (hit) return hit;
  }
  return null;
};
"""

MEASURE = FIND_SLOT + """
const page = penpot.currentFile.pages.find(p => p.name === __PAGE__);
if (!page) throw new Error("page not found: " + __PAGE__);
const board = page.root.children.find(s => s.name === __BOARD__);
if (!board) throw new Error("board not found: " + __BOARD__);
const slot = findSlot(board, __NAME__);
if (!slot) throw new Error("slot not found: " + __NAME__);
return JSON.stringify({ w: slot.width, h: slot.height });
"""

PLACE = FIND_SLOT + """
const page = penpot.currentFile.pages.find(p => p.name === __PAGE__);
if (!page) throw new Error("page not found: " + __PAGE__);
if (penpot.currentPage.id !== page.id) throw new Error("page not active: " + __PAGE__);
const board = page.root.children.find(s => s.name === __BOARD__);
if (!board) throw new Error("board not found: " + __BOARD__);
const collect = (root, name, out) => {
  if (root.name === name) out.push(root.id);
  (root.children || []).forEach(c => collect(c, name, out));
  return out;
};
const existing = findSlot(board, __NAME__);
if (!existing) throw new Error("slot not found: " + __NAME__);
const host = existing.parent;
const x = existing.x, y = existing.y, w = existing.width, h = existing.height;
// ids, not object identity: the bridge may hand back a different wrapper for the same
// shape, so `s !== shape` is true even for the shape just created. Collect the ids to
// drop BEFORE placing, then remove by id afterwards.
const doomed = collect(board, __NAME__, []);
const raw = atob(__B64__);
const bytes = new Uint8Array(raw.length);
for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
const media = await penpot.uploadMediaData(__NAME__, bytes, "image/jpeg");
const shape = penpot.createRectangle();
shape.name = __NAME__;
shape.resize(w, h);
host.appendChild(shape);
// Replace the slot where it sits, not on top of the stack: a photo appended
// last paints over every sibling the slot used to sit under (01 hero: white
// type on a scene board vanished behind its own photo).
shape.setParentIndex(existing.parentIndex);
shape.x = x;
shape.y = y;
shape.fills = [{ fillOpacity: 1, fillImage: media }];
shape.borderRadius = 8;
// remove by id (see above): everything that had this name before the place, i.e. the
// placeholder slot and any older duplicate. The fresh photo has a new id and survives.
const drop = (root) => {
  (root.children || []).slice().forEach(c => {
    if (doomed.indexOf(c.id) >= 0) c.remove(); else drop(c);
  });
};
drop(board);
const left = collect(board, __NAME__, []).length;
if (left !== 1) throw new Error("expected exactly 1 placed shape, found " + left);
return JSON.stringify({ w: shape.width, h: shape.height, x: shape.x, y: shape.y, left: left });
"""


def activate(url: str, page: str) -> None:
    call_execute_code(url, f"""
const p = penpot.currentFile.pages.find(x => x.name === {json.dumps(page)});
if (!p) throw new Error("page not found: " + {json.dumps(page)});
if (penpot.currentPage.name !== {json.dumps(page)}) penpot.openPage(p);
return JSON.stringify({{ page: p.name }});
""")
    until = time.monotonic() + 2.0
    while time.monotonic() < until:
        state = payload(call_execute_code(
            url, "return JSON.stringify({ page: penpot.currentPage.name });"))
        if isinstance(state, dict) and state.get("page") == page:
            return
        time.sleep(0.25)
    raise McpError(f"page {page!r} did not become current within 2s")


def place(url: str, name: str, page: str, board: str, src: str, credit: str) -> dict:
    activate(url, page)
    slot = payload(call_execute_code(url, MEASURE.replace("__PAGE__", json.dumps(page))
                                     .replace("__BOARD__", json.dumps(board))
                                     .replace("__NAME__", json.dumps(name))))
    w, h = int(slot["w"]), int(slot["h"])
    data = graded_bytes(name, w, h, src)
    print(f"{name}: {len(data)//1024} KB at {w}x{h}", file=sys.stderr)
    code = (PLACE.replace("__PAGE__", json.dumps(page))
            .replace("__BOARD__", json.dumps(board))
            .replace("__NAME__", json.dumps(name))
            .replace("__B64__", json.dumps(base64.b64encode(data).decode())))
    # A shared plugin has one active page, and another session can switch
    # it between our open and our write ("Cannot modify a page that is not
    # currently active"). That is a lost race, not a bad photo: re-open and
    # place once more before calling it an error.
    for attempt in (1, 2):
        try:
            res = payload(call_execute_code(url, code))
            if not isinstance(res, dict) or res.get("left") != 1:
                raise PlaceError(f"photo verify failed on {name}: {res} (expected exactly 1 shape)")
            break
        except McpError as exc:
            if attempt == 1 and ("not currently active" in str(exc) or "page not active" in str(exc)):
                activate(url, page)
                continue
            raise
    time.sleep(0.4)
    return res


def placement_code(exc: Exception) -> int:
    message = str(exc)
    if isinstance(exc, PlaceError):
        return 1
    if any(marker in message for marker in ("slot not found", "board not found", "page not found")):
        return 1
    return 2


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--board")
    ap.add_argument("--page")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--restore", action="store_true",
                    help="re-place the photos provenance records for --board, from pinned URLs")
    ap.add_argument("--refresh", action="store_true",
                    help="ignore the graded-JPEG cache and fetch the source again")
    args = ap.parse_args(argv)

    if args.list:
        for k, v in IMAGES.items():
            print(f"{k:14} {v[1]:12} {v[2]}")
        return 0

    prov_path = HERE.parent / "media" / "provenance.json"
    prov_path.parent.mkdir(parents=True, exist_ok=True)
    provenance = json.loads(prov_path.read_text()) if prov_path.is_file() else {}

    try:
        url = load_url()
        ensure_helpers(url)
    except McpError as exc:
        fail(str(exc))

    if args.restore:
        if not args.board:
            fail("--restore needs --board")
        names = entries_for_board(provenance, args.board)
        if not names:
            print(f"{args.board}: no photos in provenance")
            return 0
        for name in names:
            record = provenance[key_for(name, args.board)]
            page = args.page or record.get("page")
            src = record.get("source") or ""
            credit = record.get("credit") or src
            if not page or not src.startswith("http"):
                fail(f"{name}: provenance has no pinned page/source ({page!r}, {src!r})", 1)
            print(f"restore {name} -> {args.board}")
            try:
                res = place(url, name, page, args.board, src, credit)
            except (McpError, PlaceError) as exc:
                print(f"{name}: ERROR {exc}", file=sys.stderr)
                return placement_code(exc)
            print(f"{name}: placed {res.get('w')}x{res.get('h')} on {args.board} — {credit}")
        return 0

    names = list(IMAGES) if (args.all or not args.only) else [n for n in args.only.split(",")]
    unknown = [n for n in names if n not in IMAGES]
    if unknown:
        fail(f"unknown image(s): {', '.join(unknown)}")

    for name in names:
        spec = IMAGES[name]
        query, page, board = spec[0], spec[1], spec[2]
        if args.board:
            board = args.board
        if args.page:
            page = args.page
        if key_for(name, board) in provenance and not args.force:
            print(f"{name}: already placed on {board}, skip (--force to replace)")
            continue
        if query.startswith("http"):
            src = query
            credit = spec[3] if len(spec) > 3 else query
        else:
            src, credit = pexels(query)
        try:
            res = place(url, name, page, board, src, credit)
        except (McpError, PlaceError) as exc:
            print(f"{name}: ERROR {exc}", file=sys.stderr)
            return placement_code(exc)
        provenance[key_for(name, board)] = {"board": board, "page": page, "source": src, "credit": credit}
        provenance[name] = provenance[key_for(name, board)]
        prov_path.write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n")
        print(f"{name}: placed {res.get('w')}x{res.get('h')} on {board} — {credit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
