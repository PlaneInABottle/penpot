#!/usr/bin/env python3
"""Sync W3C DTCG tokens between a JSON file and a Penpot token set.

    tokens_sync.py --file design/tokens.json            # JSON -> Penpot (additive)
    tokens_sync.py --file design/tokens.json --check    # compare only, no writes
    tokens_sync.py --file design/tokens.json --export   # Penpot -> JSON (overwrites)
    tokens_sync.py --repaint --file F --set S --page P [--dry-run]
        # repaint literals bound to color tokens of set S on page P
        # (--dry-run lists what would change, changes nothing)

Sync is additive: it adds missing tokens and updates changed values, never
deletes. `--check` therefore reports tokens that exist only in Penpot as
informational, and `--strict` turns them into a failure.

Name mapping (group -> Penpot token name) keeps Penpot's path-style names:
    color.ink     -> "ink"        spacing.md -> "space.md"
    radius.md     -> "radius.md"  fontSize.body -> "fs.body"

The Penpot side needs `storage.H` from the penpot-design-system skill's
assets/helpers.js and a connected browser plugin; every call fails otherwise.

Exit codes: 0 clean, 1 drift/findings or an invalid token file, 2 environment,
transport or plugin failure.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import re
import sys
import tempfile
import urllib.error

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from penpot_exec import McpError, call_execute_code, ensure_helpers, fail, load_url, payload  # noqa: E402

GROUPS = {
    "color": ("color", ""),
    "spacing": ("spacing", "space."),
    "radius": ("borderRadius", "radius."),
    "fontSize": ("fontSizes", "fs."),
}
NUMBER = re.compile(r"^\d+(?:\.\d+)?$")
PIXELS = re.compile(r"^(\d+(?:\.\d+)?)px$")


def flatten(node: dict, prefix: str = "") -> list[tuple[str, dict]]:
    out = []
    for key, value in node.items():
        if key.startswith("$"):
            continue
        path = f"{prefix}{key}"
        if isinstance(value, dict) and "$value" in value:
            out.append((path, value))
        elif isinstance(value, dict):
            out.extend(flatten(value, path + "."))
    return out


def normalize_value(group: str, path: str, value):
    """A colour string, or a bare number / `<number>px`; anything else is a file error."""
    where = f"{group}.{path}"
    if group == "color":
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{where}: colour must be a non-empty string, got {value!r}")
        return value.strip()
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"{where}: expected a number or '<number>px', got {value!r}")
    text = str(value).strip()
    match = PIXELS.match(text)
    if match:
        return match.group(1)
    if NUMBER.match(text):
        return text
    hint = ""
    if "rem" in text.lower():
        hint = " (rem is not supported, use px)"
    elif "{" in text:
        hint = " (token aliases are not supported, use a literal value)"
    raise ValueError(f"{where}: expected a number or '<number>px', got {value!r}{hint}")


def to_specs(doc: dict) -> list[dict]:
    specs: list[dict] = []
    origin: dict[str, str] = {}
    for group, (token_type, name_prefix) in GROUPS.items():
        for path, node in flatten(doc.get(group, {}), ""):
            name = name_prefix + path
            if name in origin:
                raise ValueError(
                    f"token name {name!r} comes from both {origin[name]} and {group}.{path}; rename one"
                )
            origin[name] = f"{group}.{path}"
            specs.append(
                {"type": token_type, "name": name, "value": normalize_value(group, path, node["$value"])}
            )
    return specs


def to_dtcg(tokens: list[dict]) -> tuple[dict, list[str]]:
    """Penpot tokens -> DTCG document, plus the token names that could not be mapped."""
    by_type = {token_type: (group, name_prefix) for group, (token_type, name_prefix) in GROUPS.items()}
    doc: dict = {}
    skipped: list[str] = []
    for token in tokens:
        token_type = token.get("type")
        name = str(token.get("name", ""))
        entry = by_type.get(token_type)
        if entry is None:
            skipped.append(name)
            continue
        group, name_prefix = entry
        if name_prefix and not name.startswith(name_prefix):
            skipped.append(name)
            continue
        leaf = name[len(name_prefix):]
        values = doc.setdefault(group, {"$type": "color" if token_type == "color" else "dimension"})
        value = str(token.get("value", ""))
        values[leaf] = {"$value": value if token_type == "color" else f"{value}px"}
    return doc, skipped


def same_value(spec: dict, have: dict) -> bool:
    if spec["type"] == "color":
        return str(spec["value"]).upper() == str(have.get("value", "")).upper()
    return str(spec["value"]) == str(have.get("value", ""))


def compare(specs: list[dict], current: dict[str, dict]) -> tuple[list[str], list[str]]:
    """Returns (drift, extras); extras are informational unless --strict."""
    drift: list[str] = []
    wanted = {spec["name"] for spec in specs}
    for spec in specs:
        have = current.get(spec["name"])
        if not have:
            drift.append(f"missing  {spec['name']} ({spec['value']})")
        elif have.get("type") != spec["type"]:
            drift.append(f"type     {spec['name']}: file={spec['type']} penpot={have.get('type')}")
        elif not same_value(spec, have):
            drift.append(f"differs  {spec['name']}: file={spec['value']} penpot={have.get('value')}")
    extras = [
        f"extra    {name}={current[name].get('value')} (in Penpot, not in file)"
        for name in sorted(set(current) - wanted)
    ]
    return drift, extras


def write_atomic(path: pathlib.Path, text: str) -> None:
    """Write through a temp file in the same directory.

    The previous file is kept as `<file>.<UTC timestamp>.bak`, so repeated exports
    never overwrite the only backup.
    """
    path = pathlib.Path(path)
    mode = None
    if path.exists():
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        pathlib.Path(f"{path}.{stamp}.bak").write_text(path.read_text())
        mode = path.stat().st_mode & 0o777
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        if mode is not None:
            os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load_specs(path: pathlib.Path) -> list[dict]:
    try:
        doc = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(doc, dict):
        raise ValueError(f"{path}: expected a JSON object of token groups")
    specs = to_specs(doc)
    if not specs:
        raise ValueError(f"no tokens found in {path}")
    return specs


def read_set(url: str, name: str) -> dict | None:
    data = payload(call_execute_code(url, f"return JSON.stringify(storage.H.readSet({json.dumps(name)}));"))
    if data is None:
        return None
    if not isinstance(data, dict) or "tokens" not in data:
        raise McpError(f"unexpected readSet result for {name!r}: {data!r}")
    return data


def export(args, url: str) -> int:
    data = read_set(url, args.set)
    if data is None:
        fail(f"token set {args.set!r} not found in the file")
    doc, skipped = to_dtcg(data["tokens"])
    write_atomic(args.file, json.dumps(doc, indent=2) + "\n")
    print(f"exported {len(data['tokens']) - len(skipped)} tokens -> {args.file}")
    if skipped:
        print(f"skipped {len(skipped)} token(s) of unknown type: {', '.join(skipped)}")
    return 0


def check(args, url: str, specs: list[dict]) -> int:
    data = read_set(url, args.set)
    current = {token["name"]: token for token in (data or {}).get("tokens", [])}
    drift, extras = compare(specs, current)
    print("\n".join(drift + extras) if drift or extras else "no drift")
    if drift:
        return 1
    if extras:
        if args.strict:
            return 1
        print(f"({len(extras)} token(s) exist only in Penpot; sync is additive, pass --strict to fail)")
    return 0


def sync(args, url: str, specs: list[dict]) -> int:
    summary = payload(
        call_execute_code(
            url,
            f"return JSON.stringify(storage.H.syncTokens({json.dumps(args.set)}, {json.dumps(specs)}));",
        )
    )
    if not isinstance(summary, dict):
        fail(f"unexpected sync result: {summary!r}")
    print(json.dumps(summary, indent=2))
    return 1 if summary.get("conflicts") else 0


REPAINT_JS = """
const pageName = __PAGE__;
const live = __LIVE__;
const dryRun = __DRY__;
const file = penpot.currentFile;
const pg = file.pages.filter((p) => p.name === pageName)[0];
if (!pg) throw new Error("page not found: " + pageName);
const set = penpot.library.local.tokens.sets.filter((s) => s.name === __SET__)[0];
if (!set) throw new Error("token set not found: " + __SET__);
const byName = {};
set.tokens.forEach((t) => { byName[t.name] = t; });
const fixed = [];
const unknown = [];
let bound = 0, repainted = 0, skippedImage = 0, skippedCurrent = 0;
const walk = (s) => {
  const tokName = s.tokens && s.tokens.fill;
  if (tokName !== undefined && tokName !== null) {
    const want = live[tokName];
    const tok = byName[tokName];
    const f = s.fills && s.fills[0];
    if (f && f.fillImage) {
      skippedImage++;
    } else if (want === undefined || !tok || tok.type !== "color") {
      if (unknown.indexOf(String(tokName)) === -1) unknown.push(String(tokName));
    } else {
      bound++;
      const actual = f && f.fillColor ? String(f.fillColor).toUpperCase() : null;
      if (actual === String(want).toUpperCase()) {
        skippedCurrent++;
      } else {
        const detail = s.name + ": " + tokName + " renders " + actual + " not " + String(want).toUpperCase();
        if (dryRun) {
          fixed.push(detail);
        } else {
          if (f) {
            // explicit keys only: enumerating a live fill object can hit
            // read-only members (e.g. "constructor"); opacity is preserved
            s.fills = [{ fillColor: String(want),
              fillOpacity: (f.fillOpacity === undefined || f.fillOpacity === null) ? 1 : f.fillOpacity,
              fillColorGradient: null, fillColorRefFile: null, fillColorRefId: null, fillImage: null }];
          } else {
            s.fills = [{ fillColor: String(want), fillOpacity: 1 }];
          }
          // rewriting fills clears the binding; restore it (bind touches nothing else)
          const live_tok = set.tokens.filter((t) => t.name === tokName)[0];
          if (live_tok) s.applyToken(live_tok, ["fill"]);
          fixed.push(detail);
        }
        repainted++;
      }
    }
  }
  (s.children || []).forEach(walk);
};
(pg.root.children || []).forEach(walk);
return JSON.stringify({ page: pageName, bound: bound, repainted: repainted,
  skippedImage: skippedImage, skippedCurrent: skippedCurrent,
  unknown: unknown, fixed: fixed.slice(0, 20), dryRun: dryRun });
"""


def repaint(args, url: str, specs: list[dict]) -> int:
    file_colors = {spec["name"]: spec["value"] for spec in specs if spec["type"] == "color"}
    if not file_colors:
        print(f"repaint: no color tokens in {args.file}, nothing to do")
        return 1
    data = read_set(url, args.set)
    if data is None:
        fail(f"token set {args.set!r} not found in the file")
    live_all = {token["name"]: token for token in data["tokens"]}
    live_colors = {
        name: str(token.get("value", ""))
        for name, token in live_all.items()
        if token.get("type") == "color" and name in file_colors
    }
    if not live_colors:
        print(f"repaint: no file color tokens present in set {args.set!r}, nothing to do")
        return 1
    for name, value in sorted(live_colors.items()):
        if str(file_colors[name]).upper() != str(value).upper():
            print(f"warning: {name}: file={file_colors[name]} penpot={value} (repainting to the Penpot value)")
    code = (
        REPAINT_JS.replace("__PAGE__", json.dumps(args.page))
        .replace("__LIVE__", json.dumps(live_colors))
        .replace("__DRY__", "true" if args.dry_run else "false")
        .replace("__SET__", json.dumps(args.set))
    )
    try:
        summary = payload(call_execute_code(url, code))
    except McpError as exc:
        fail(str(exc))
    if not isinstance(summary, dict):
        fail(f"unexpected repaint result: {summary!r}")
    verb = "would repaint" if summary.get("dryRun") else "repainted"
    print(
        f"repaint {summary.get('page')}: bound-found {summary.get('bound')}, "
        f"{verb} {summary.get('repainted')}, skipped-image {summary.get('skippedImage')}, "
        f"skipped-current {summary.get('skippedCurrent')}"
    )
    for line in summary.get("fixed") or []:
        print(f"  {'would fix' if summary.get('dryRun') else 'fixed'} {line}")
    if summary.get("unknown"):
        print(f"  skipped-unknown {len(summary['unknown'])}: {', '.join(sorted(summary['unknown']))}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", type=pathlib.Path, required=True)
    ap.add_argument("--set", default="core")
    ap.add_argument("--check", action="store_true", help="report drift without writing, exit 1 on drift")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="with --check: also exit 1 for tokens that exist only in Penpot",
    )
    ap.add_argument("--export", action="store_true", help="write Penpot state back to the file")
    ap.add_argument(
        "--repaint",
        action="store_true",
        help="rewrite stale fill literals bound to color tokens of --set (requires --page)",
    )
    ap.add_argument("--page", help="with --repaint: the single page to walk")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="with --repaint: list what would change, change nothing",
    )
    args = ap.parse_args(argv)
    if args.check and args.export:
        ap.error("--check and --export are mutually exclusive")
    if args.repaint and (args.check or args.export):
        ap.error("--repaint is mutually exclusive with --check and --export")
    if args.dry_run and not args.repaint:
        ap.error("--dry-run requires --repaint")
    if args.repaint and not args.page:
        ap.error("--repaint requires --page (one page at a time)")

    try:
        url = load_url()
        ensure_helpers(url)
        if args.export:
            return export(args, url)
        specs = load_specs(args.file)
        if args.repaint:
            return repaint(args, url, specs)
        return check(args, url, specs) if args.check else sync(args, url, specs)
    except ValueError as exc:
        fail(str(exc), code=1)
    except McpError as exc:
        fail(str(exc))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        fail(f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    sys.exit(main())
