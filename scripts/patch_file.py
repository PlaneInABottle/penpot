#!/usr/bin/env python3
"""Surgical edit: one exact `old` block becomes `new`, backed up and re-validated.

    patch_file.py FILE --old-file a.txt --new-file b.txt
    patch_file.py FILE --old 'version: "1.4.0"' --new 'version: "1.5.0"'
    cat new-block.txt | patch_file.py FILE --old-file old-block.txt

Written for the edit path that keeps failing on big JS/Python files: `old` must
occur exactly once (0 or 2+ matches is a hard FAIL, never a guess), the original
is copied to `FILE.bak`, and the result is checked according to the extension —
.py → py_compile, .js/.mjs/.cjs → `node --check`, .json → json.load. A failed
check restores the original bytes and exits 1, so a bad patch cannot leave a
half-edited file behind.

Exit codes: 0 patched and valid, 1 no/multiple match or validation failure (the
file is unchanged), 2 environment (missing file, unreadable input, no node).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import py_compile
import shutil
import subprocess
import sys

JS_SUFFIXES = {".js", ".mjs", ".cjs"}


def fail(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def read_text_arg(value: str | None, path: pathlib.Path | None, label: str) -> str:
    if path is not None:
        try:
            return path.read_text()
        except OSError as exc:
            fail(f"cannot read {label} file {path}: {exc}", 2)
    if value is not None:
        return value
    if label == "new":
        if sys.stdin.isatty():
            fail("no new text: pass --new, --new-file or pipe it on stdin", 2)
        return sys.stdin.read()
    fail("no old text: pass --old or --old-file", 2)
    return ""  # unreachable, keeps type checkers quiet


def match_lines(text: str, needle: str) -> list[int]:
    lines, start = [], 0
    while True:
        found = text.find(needle, start)
        if found < 0:
            return lines
        lines.append(text.count("\n", 0, found) + 1)
        start = found + 1


def squeeze(text: str) -> str:
    return " ".join(text.split())


def validate(path: pathlib.Path) -> str:
    """Raises ValueError with one line of detail when the patched file is not parseable."""
    suffix = path.suffix.lower()
    if suffix == ".py":
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            raise ValueError(str(exc).replace(str(path), path.name).strip().splitlines()[0]) from None
        return "py_compile"
    if suffix in JS_SUFFIXES:
        try:
            proc = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
        except FileNotFoundError:
            raise OSError("node is not installed; cannot validate a JS patch") from None
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout).strip().splitlines()
            raise ValueError(f"node --check: {detail[0] if detail else f'exit {proc.returncode}'}")
        return "node --check"
    if suffix == ".json":
        try:
            json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise ValueError(f"{exc.msg} at line {exc.lineno} column {exc.colno}") from None
        return "json.load"
    return "none"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=pathlib.Path)
    ap.add_argument("--old", help="exact text to replace")
    ap.add_argument("--new", help="replacement text")
    ap.add_argument("--old-file", type=pathlib.Path)
    ap.add_argument("--new-file", type=pathlib.Path)
    args = ap.parse_args(argv)

    if not args.file.is_file():
        fail(f"no such file: {args.file}", 2)
    old = read_text_arg(args.old, args.old_file, "old")
    new = read_text_arg(args.new, args.new_file, "new")
    if old == "":
        fail("--old is empty; an empty block matches everywhere", 2)

    try:
        with open(args.file, newline="") as fh:
            original = fh.read()
    except OSError as exc:
        fail(f"cannot read {args.file}: {exc}", 2)

    hits = match_lines(original, old)
    if not hits:
        hint = ""
        index = squeeze(original).find(squeeze(old))
        if index >= 0:
            hint = " (the block exists only after whitespace is normalised — check indentation/line endings)"
        fail(f"{args.file}: --old occurs 0 times{hint}", 1)
    if len(hits) > 1:
        fail(f"{args.file}: --old occurs {len(hits)} times (lines {', '.join(map(str, hits[:8]))}); "
             "make it unique", 1)

    backup = args.file.with_name(args.file.name + ".bak")
    shutil.copy2(args.file, backup)
    patched = original.replace(old, new, 1)
    try:
        with open(args.file, "w", newline="") as fh:
            fh.write(patched)
        checked = validate(args.file)
    except OSError as exc:
        shutil.copy2(backup, args.file)
        fail(f"{args.file}: {exc} — restored", 2)
    except ValueError as exc:
        shutil.copy2(backup, args.file)
        fail(f"{args.file}: {exc} — restored from {backup.name}", 1)

    print(f"patched {args.file} (line {hits[0]})  validation: {checked}  backup: {backup.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
