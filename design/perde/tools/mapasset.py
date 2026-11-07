"""Upload a block-map placeholder once, in chunks, and keep it as a page asset.

The MCP endpoints reject bodies over ~100 KB, so the JPEG cannot ride inside a screen
snippet. The base64 is split across calls, parked in page plugin data, and assembled
once into a named rect on the off-canvas `__assets` board. Screens copy that fill.

    python3 design/perde/tools/mapasset.py /tmp/map.jpg
    python3 design/perde/tools/mapasset.py /tmp/map-pixel.jpg --name __map-pixel --slot map-pixel
    python3 design/perde/tools/mapasset.py --status
"""

from __future__ import annotations

import argparse
import base64
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXEC = ROOT / "scripts" / "penpot_exec.py"
CHUNK = 42000


def run(code: str) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
        fh.write(code)
        path = fh.name
    out = subprocess.run([sys.executable, str(EXEC), "--file", path],
                         capture_output=True, text=True)
    if out.returncode != 0:
        sys.stderr.write(out.stderr or out.stdout)
        raise SystemExit(out.returncode)
    return json.loads(out.stdout or "{}").get("result") or {}


FINAL = """
const page = penpot.currentPage;
const count = {count};
let b64 = "";
for (let i = 0; i < count; i++) b64 += page.getPluginData("mapb64_" + i);
if (b64.length !== {length}) throw new Error("chunk assembly mismatch: " + b64.length);
for (let i = 0; i < count; i++) page.setPluginData("mapb64_" + i, "");

const raw = atob(b64);
const bytes = new Uint8Array(raw.length);
for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
const media = await penpot.uploadMediaData({slot}, bytes, "image/jpeg");

let assets = page.findShapes({{name: "__assets"}})[0];
if (!assets) {{
  assets = penpot.createBoard();
  assets.name = "__assets";
  assets.x = 0;
  assets.y = 1600;
  assets.resize(1440, 900);
  assets.fills = [{{fillColor: "#FFFFFF"}}];
}}
for (const old of assets.children.filter((c) => c.name === {name})) old.remove();
const rect = penpot.createRectangle();
rect.name = {name};
assets.appendChild(rect);
rect.resize(1440, 900);
rect.x = assets.x;
rect.y = assets.y;
rect.fills = [{{fillOpacity: 1, fillImage: media}}];
return JSON.stringify({{ mediaId: media && media.id, bytes: bytes.length }});
"""


def status() -> dict:
    return run("""
const page = penpot.currentPage;
const assets = page.findShapes({name: "__assets"})[0];
return JSON.stringify({ assets: !!assets, items: assets ? assets.children.map(c => c.name) : [] });
""")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("image", nargs="?")
    ap.add_argument("--name", default="__map-src")
    ap.add_argument("--slot", default="map-bosphorus")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    if args.status:
        print(json.dumps(status()))
        return 0
    if not args.image:
        ap.error("image path required")

    b64 = base64.b64encode(pathlib.Path(args.image).read_bytes()).decode()
    chunks = [b64[i:i + CHUNK] for i in range(0, len(b64), CHUNK)]
    print(f"{len(b64)} chars in {len(chunks)} chunks")

    for i, chunk in enumerate(chunks):
        run(f"""
penpot.currentPage.setPluginData("mapb64_{i}", {json.dumps(chunk)});
return JSON.stringify({{ i: {i} }});
""")
        print(f"  chunk {i + 1}/{len(chunks)}", flush=True)

    print("ready:", json.dumps(run(FINAL.format(
        count=len(chunks), length=len(b64),
        slot=json.dumps(args.slot), name=json.dumps(args.name),
    ))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
