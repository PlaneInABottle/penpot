#!/usr/bin/env python3
"""Import a stock photograph into a Penpot board.

    import_media.py --search "neuroscience laboratory" --name hero-photo \
        --page <page> --board 01-home --x 840 --y 120 --w 480 --h 480

    import_media.py --url https://images.pexels.com/photos/… --name venue …

`--search` queries the Pexels API with `PEXELS_API_KEY` (exported in the shell profile) and
picks the first landscape result; `--url` takes any public image. The image is uploaded to the
file and placed as a rectangle with an image fill, so the board keeps a real asset rather than
a placeholder. Prints the chosen photo URL so provenance can be recorded.

Exit codes: 0 imported, 1 board not found, 2 environment, transport or plugin failure.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import pathlib
import subprocess
import tempfile
import time
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from penpot_exec import McpError, call_execute_code, fail, load_url, payload  # noqa: E402

PEXELS_SEARCH = "https://api.pexels.com/v1/search"

OPEN = """
const page = penpot.currentFile.pages.find(p => p.name === __PAGE__);
if (!page) throw new Error("page not found: " + __PAGE__);
penpot.openPage(page);
return JSON.stringify({ opening: page.name });
"""

PLACE = """
const page = penpot.currentFile.pages.find(p => p.name === __PAGE__);
if (!page) throw new Error("page not found: " + __PAGE__);
if (penpot.currentPage.id !== page.id) throw new Error("page not active: " + page.name);
const board = page.root.children.find(s => s.name === __BOARD__);
if (!board) throw new Error("board not found: " + __BOARD__);
const existing = board.children.find(s => s.name === __NAME__);
if (existing) existing.remove();
const raw = atob(__B64__);
const bytes = new Uint8Array(raw.length);
for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
const media = await penpot.uploadMediaData(__NAME__, bytes, __MIME__);
const shape = penpot.createRectangle();
shape.name = __NAME__;
shape.resize(__W__, __H__);
board.appendChild(shape);
// shape coords are page-absolute even inside a board, but --x/--y are board-local:
shape.x = __X__ + board.x;
shape.y = __Y__ + board.y;
shape.fills = [{ fillOpacity: 1, fillImage: media }];
return JSON.stringify({ mediaId: media && media.id, width: shape.width, height: shape.height });
"""


def pexels(query: str) -> tuple[str, str]:
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        fail("PEXELS_API_KEY is not set (export it in the shell profile)")
    url = f"{PEXELS_SEARCH}?{urllib.parse.urlencode({'query': query, 'per_page': 1, 'orientation': 'landscape'})}"
    request = urllib.request.Request(url, headers={"Authorization": key, "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        fail(f"Pexels HTTP {exc.code}: {exc.read()[:200]!r}")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        fail(f"{type(exc).__name__}: {exc}")
    photos = body.get("photos") or []
    if not photos:
        fail(f"no Pexels result for {query!r}")
    photo = photos[0]
    return photo["src"]["large2x"], f"https://www.pexels.com/photo/{photo['id']}/ by {photo['photographer']}"


UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def fetch_image(url: str, max_px: int = 700, quality: int = 55) -> tuple[bytes, str]:
    """Download the image locally; the plugin sandbox cannot fetch cross-origin."""
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read()
            mime = response.headers.get_content_type() or "image/jpeg"
    except urllib.error.HTTPError as exc:
        fail(f"image HTTP {exc.code}: {url[:80]}")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        fail(f"{type(exc).__name__}: {exc}")
    if len(data) < 2048:
        fail(f"downloaded {len(data)} bytes, that is not an image")
    return shrink(data, mime, max_px, quality)


def shrink(data: bytes, mime: str, max_px: int = 700, quality: int = 55) -> tuple[bytes, str]:
    """Cap the pixel size and re-encode; the MCP request body rejects large payloads (HTTP 413)."""
    with tempfile.TemporaryDirectory() as tmp:
        source = pathlib.Path(tmp) / "in"
        target = pathlib.Path(tmp) / "out.jpg"
        source.write_bytes(data)
        result = subprocess.run(
            ["sips", "-Z", str(max_px), "-s", "format", "jpeg", "-s", "formatOptions", str(quality),
             str(source), "--out", str(target)],
            capture_output=True,
        )
        if result.returncode != 0 or not target.is_file():
            return data, mime
        shrunk = target.read_bytes()
    return (shrunk, "image/jpeg") if len(shrunk) < len(data) else (data, mime)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url")
    source.add_argument("--search")
    parser.add_argument("--name", required=True)
    parser.add_argument("--page", required=True)
    parser.add_argument("--board", required=True)
    parser.add_argument("--x", type=int, default=0)
    parser.add_argument("--y", type=int, default=0)
    parser.add_argument("--w", type=int, required=True)
    parser.add_argument("--h", type=int, required=True)
    parser.add_argument("--max-px", type=int, default=700, help="longest image side after resize")
    parser.add_argument("--quality", type=int, default=55, help="jpeg quality after resize")
    args = parser.parse_args()

    image_url, provenance = args.url, "explicit url"
    if args.search:
        image_url, provenance = pexels(args.search)

    data, mime = fetch_image(image_url, args.max_px, args.quality)
    encoded = base64.b64encode(data).decode()
    print(f"payload: {len(data) // 1024} KB image, {len(encoded) // 1024} KB base64", file=sys.stderr)

    code = (
        PLACE.replace("__PAGE__", json.dumps(args.page))
        .replace("__BOARD__", json.dumps(args.board))
        .replace("__NAME__", json.dumps(args.name))
        .replace("__B64__", json.dumps(encoded))
        .replace("__MIME__", json.dumps(mime))
        .replace("__W__", str(args.w))
        .replace("__H__", str(args.h))
        .replace("__X__", str(args.x))
        .replace("__Y__", str(args.y))
    )

    try:
        url = load_url()
        payload(call_execute_code(url, OPEN.replace("__PAGE__", json.dumps(args.page))))
        time.sleep(1.2)
        try:
            result = payload(call_execute_code(url, code))
        except McpError as exc:
            if "413" not in str(exc):
                raise
            # the MCP request body has a hard limit; re-encode smaller and retry once
            data, mime = shrink(data, mime, 420, 45)
            smaller = base64.b64encode(data).decode()
            print(f"retry at {len(smaller) // 1024} KB base64", file=sys.stderr)
            result = payload(call_execute_code(url, code.replace(json.dumps(encoded), json.dumps(smaller))))
    except McpError as exc:
        message = str(exc)
        if "board not found" in message or "page not found" in message:
            fail(message, 1)
        fail(message)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        fail(f"{type(exc).__name__}: {exc}")

    print(f"placed {args.name} {result['width']}x{result['height']} on {args.board}")
    print(f"source: {image_url}")
    print(f"provenance: {provenance}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
