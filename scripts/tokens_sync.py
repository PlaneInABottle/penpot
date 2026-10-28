#!/usr/bin/env python3
"""Sync W3C DTCG tokens between a JSON file and a Penpot token set.

    tokens_sync.py --file design/tokens.json            # JSON -> Penpot (additive)
    tokens_sync.py --file design/tokens.json --check    # compare only, no writes
    tokens_sync.py --file design/tokens.json --export   # Penpot -> JSON (overwrites)

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
    args = ap.parse_args(argv)
    if args.check and args.export:
        ap.error("--check and --export are mutually exclusive")

    try:
        url = load_url()
        ensure_helpers(url)
        if args.export:
            return export(args, url)
        specs = load_specs(args.file)
        return check(args, url, specs) if args.check else sync(args, url, specs)
    except ValueError as exc:
        fail(str(exc), code=1)
    except McpError as exc:
        fail(str(exc))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        fail(f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    sys.exit(main())
