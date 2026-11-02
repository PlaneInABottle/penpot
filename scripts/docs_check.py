#!/usr/bin/env python3
"""Docs check: the instruction tree stays short, linked and project-neutral.

    docs_check.py [--root .] [--json]

Four checks over `AGENTS.md`, `README.md`, `.agents/skills/**/*.md` and the
`design/_template/**/*.md` recipe:

1. **Line ceiling** — every manifest file stays within its hard limit. A skill that
   grows past it is either duplicating another skill or telling a story.
2. **Relative links** — a `[text](path)` link must resolve on disk. Anchors,
   `http(s)` and `mailto` targets are skipped.
3. **Banned tokens** — incident vocabulary (project names, screen numbers, pinned
   dates, "Incident") has no place in a reusable rule. Version numbers are fine.
4. **Repeated prose** — a normalized sentence of 10 words or more appears once.
   Bullets and table cells are inspected; markers and table pipes are stripped
   first, and fenced code and table separator rows are skipped.

The repeat check is exact normalized-sentence equality, not a semantic proof:
two differently worded rules can still own the same concern. The limit is
deliberate — a fuzzy detector would flag distinct rules that share vocabulary.
Collapse an ownership duplicate in the prose instead of teaching this script an
algorithm.

Exit codes: 0 clean, 1 finding(s), 2 environment (root or a manifest file missing).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import urllib.parse

# path -> maximum lines. Raise a limit deliberately, never to silence a finding.
MANIFEST = {
    "AGENTS.md": 120,
    "README.md": 50,
    ".agents/skills/design-verification/SKILL.md": 140,
    ".agents/skills/penpot-design-system/SKILL.md": 150,
    ".agents/skills/penpot-design-system/references/craft.md": 180,
    ".agents/skills/penpot-mcp-operations/SKILL.md": 105,
    ".agents/skills/penpot-mcp-operations/references/mcp-failures.md": 110,
    ".agents/skills/ux-design-process/SKILL.md": 120,
    "design/_template/brief.md": 70,
    "design/_template/principles.md": 30,
    "design/_template/build/README.md": 45,
    "design/_template/media/README.md": 45,
}

SCAN = ("AGENTS.md", "README.md", ".agents/skills", "design/_template")
BANNED = re.compile(r"İHKD|ihkd|screen-\d\d|hero photo|20\d\d-\d\d-\d\d|Incident")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)")
SENTENCE = re.compile(r"(?<=[.!?])\s+")
FENCE = re.compile(r"^\s*(```|~~~)")
SEPARATOR = re.compile(r"^\s*\|?\s*:?-{3,}")
MARKER = re.compile(r"^\s*(?:#{1,6}\s+|>\s?|(?:[-*+]|\d+[.)])\s+)")
MIN_WORDS = 10


def markdown_files(root: pathlib.Path) -> list[pathlib.Path]:
    found: list[pathlib.Path] = []
    for entry in SCAN:
        target = root / entry
        if target.is_file():
            found.append(target)
        elif target.is_dir():
            found.extend(sorted(target.rglob("*.md")))
    return found


def normalize(sentence: str) -> str:
    text = re.sub(r"[`*_\[\]()]", "", sentence.lower())
    return re.sub(r"\s+", " ", text).strip(" .,:;—–-|")


def prose_segments(line: str) -> list[str]:
    """One markdown line -> the prose it actually carries."""
    text = MARKER.sub("", line).strip()
    if not text:
        return []
    if text.startswith("|") or " | " in text:
        return [cell.strip() for cell in text.strip("|").split("|") if cell.strip()]
    return [text]


def check_lines(root: pathlib.Path) -> list[dict]:
    findings = []
    for rel, ceiling in MANIFEST.items():
        path = root / rel
        if not path.is_file():
            findings.append({"kind": "missing", "path": rel, "detail": "manifest file does not exist"})
            continue
        count = len(path.read_text(encoding="utf-8").splitlines())
        if count > ceiling:
            findings.append({"kind": "lines", "path": rel, "detail": f"{count} lines > {ceiling}"})
    return findings


def check_links(root: pathlib.Path, files: list[pathlib.Path]) -> list[dict]:
    findings = []
    for path in files:
        for target in LINK.findall(path.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean = urllib.parse.unquote(target.split("#", 1)[0].split("?", 1)[0])
            if not clean:
                continue
            if not (path.parent / clean).exists():
                rel = str(path.relative_to(root))
                findings.append({"kind": "link", "path": rel, "detail": f"unresolved link: {target}"})
    return findings


def check_banned(root: pathlib.Path, files: list[pathlib.Path]) -> list[dict]:
    findings = []
    for path in files:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in BANNED.findall(line):
                rel = str(path.relative_to(root))
                findings.append({"kind": "banned", "path": rel, "detail": f"line {number}: {match}"})
    return findings


def check_repeats(root: pathlib.Path, files: list[pathlib.Path]) -> list[dict]:
    seen: dict[str, str] = {}
    findings = []
    for path in files:
        rel = str(path.relative_to(root))
        fenced = False
        for line in path.read_text(encoding="utf-8").splitlines():
            if FENCE.match(line):
                fenced = not fenced
                continue
            if fenced or SEPARATOR.match(line):
                continue
            for segment in prose_segments(line):
                for sentence in SENTENCE.split(segment):
                    if len(sentence.split()) < MIN_WORDS:
                        continue
                    key = normalize(sentence)
                    if not key:
                        continue
                    if key in seen:
                        findings.append({"kind": "repeat", "path": rel,
                                         "detail": f"also in {seen[key]}: {sentence[:70]}…"})
                    else:
                        seen[key] = rel
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the instruction tree: length, links, vocabulary.")
    parser.add_argument("--root", default=str(pathlib.Path(__file__).resolve().parent.parent))
    parser.add_argument("--json", action="store_true", help="machine-readable report")
    args = parser.parse_args(argv)

    root = pathlib.Path(args.root).resolve()
    if not root.is_dir():
        print(f"root not found: {root}", file=sys.stderr)
        return 2
    files = markdown_files(root)
    if not files:
        print(f"nothing to check under {root} (AGENTS.md, README.md, skills, template)", file=sys.stderr)
        return 2

    findings = check_lines(root) + check_links(root, files) + check_banned(root, files) + check_repeats(root, files)
    missing = any(item["kind"] == "missing" for item in findings)

    if args.json:
        print(json.dumps({"root": str(root), "files": len(files), "manifest": MANIFEST, "findings": findings}, indent=2))
    else:
        for rel, ceiling in MANIFEST.items():
            path = root / rel
            count = len(path.read_text(encoding="utf-8").splitlines()) if path.is_file() else -1
            print(f"  {count:>4}/{ceiling:<4} {rel}")
        print(f"files: {len(files)}  findings: {len(findings)}")
        for item in findings:
            print(f"  - {item['kind']}: {item['path']}: {item['detail']}")
        if not findings:
            print("  docs hold: ceilings, links, vocabulary and exact-sentence uniqueness")

    if missing:
        return 2
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
