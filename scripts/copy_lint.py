#!/usr/bin/env python3
"""Typo gate: a letter drop inside a domain term is a copy defect.

    copy_lint.py --page Kurumsal
    copy_lint.py --page Kurumsal --project design/ihkd --json /tmp/copy.json

Reads `design/<project>/copy-terms.json` (the correct vocabulary plus an
allowlist of real words that sit one edit away) and walks the live page's text
nodes. A word shorter than a dictionary term by exactly one letter — the
`KAP`/`KALP` class — is a finding. Inflected forms (a correct word longer than
its lemma) are never flagged, so Turkish suffixes do not produce noise.

An absent file or an empty `terms` list means the project declares no
dictionary: exit 0 before any plugin call. A malformed schema is an error.

Exit codes: 0 clean or no terms declared, 1 findings or bad schema, 2 environment
or transport.
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
from design_lint import COLLECT  # noqa: E402

WORDS = re.compile(r"[^\W\d_]+", re.UNICODE)


def fold(text: str) -> str:
    """Turkish-aware case fold: İ -> i, I -> ı, then lower()."""
    return text.replace("İ", "i").replace("I", "ı").lower()


def within_one_edit(short: str, term: str) -> bool:
    """True when `short` is one insertion/deletion/substitution from `term`.

    Only called with len(short) <= len(term), so a correct suffixed form such
    as "kılavuzu" can never look like a typo of "kılavuz".
    """
    if short == term:
        return False
    if len(short) == len(term):
        return sum(a != b for a, b in zip(short, term)) == 1
    if len(short) + 1 != len(term):
        return False
    i = 0
    while i < len(short) and short[i] == term[i]:
        i += 1
    return short[i:] == term[i + 1:]


def find_typos(texts: list[str], terms: list[str], allow: list[str],
               min_term_len: int = 4, min_word_len: int = 3) -> list[tuple[str, str, str]]:
    """Return (source text, wrong word, dictionary term), one per wrong word."""
    allowed = {fold(word) for word in allow}
    known = {fold(term) for term in terms}
    long_terms = sorted((fold(term) for term in terms if len(term) >= min_term_len),
                        key=len, reverse=True)
    findings: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    for text in texts:
        for raw in WORDS.findall(text or ""):
            word = fold(raw)
            if len(word) < min_word_len or word in known or word in allowed:
                continue
            if (text, word) in seen:
                continue
            for term in long_terms:
                if len(word) > len(term):
                    continue
                if within_one_edit(word, term):
                    findings.append((text, word, term))
                    seen.add((text, word))
                    break
    return findings


def load_terms(path: pathlib.Path) -> tuple[list[str], list[str], int, int]:
    """Vocabulary file -> (terms, allow, min_term_len, min_word_len).

    An absent or empty `terms` list is valid: the project declares no dictionary
    and the caller exits 0 before any plugin call. A malformed schema is an
    error, never silently read as "no terms".
    """
    try:
        doc = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: {exc}") from exc
    if not isinstance(doc, dict):
        raise ValueError(f"{path}: expected a JSON object")
    for key in ("terms", "allow"):
        value = doc.get(key, [])
        if not isinstance(value, list) or any(
                not isinstance(item, str) or not item.strip() for item in value):
            raise ValueError(f"{path}: {key} must be a list of non-empty strings")
    min_term_len = doc.get("min_term_len", 4)
    min_word_len = doc.get("min_word_len", 3)
    for key, value in (("min_term_len", min_term_len), ("min_word_len", min_word_len)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError(f"{path}: {key} must be a positive integer")
    terms = [term.strip() for term in doc.get("terms", [])]
    allow = [word.strip() for word in doc.get("allow", [])]
    return terms, allow, min_term_len, min_word_len


def lint_texts(nodes: list[dict], terms: list[str], allow: list[str],
               min_term_len: int, min_word_len: int) -> list[dict]:
    by_id = {node["id"]: node for node in nodes}

    def board_of(node: dict) -> str:
        current, seen = node, set()
        while current.get("parentId") and current["id"] not in seen:
            seen.add(current["id"])
            current = by_id.get(current["parentId"], current)
        return current.get("name") or "?"

    findings: list[dict] = []
    for node in nodes:
        if node.get("type") != "text" or not (node.get("text") or "").strip():
            continue
        for text, wrong, term in find_typos([node["text"]], terms, allow,
                                            min_term_len, min_word_len):
            findings.append({
                "board": board_of(node),
                "node": node["name"],
                "severity": "medium",
                "finding": f"{node['name']} says {wrong!r} — likely {term!r} ({text[:48]!r})",
            })
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--page", required=True)
    parser.add_argument("--project", type=pathlib.Path, default=pathlib.Path("design/ihkd"))
    parser.add_argument("--json", type=pathlib.Path)
    args = parser.parse_args(argv)

    terms_file = args.project / "copy-terms.json"
    if not terms_file.is_file():
        print(f"copy_lint: no {terms_file}; nothing to check")
        return 0
    try:
        terms, allow, min_term_len, min_word_len = load_terms(terms_file)
    except ValueError as exc:
        fail(str(exc), code=1)
    if not terms:
        print(f"copy_lint: no terms declared in {terms_file}; nothing to check")
        return 0

    try:
        url = load_url()
        nodes = payload(call_execute_code(
            url, COLLECT.replace("__PAGE__", json.dumps(args.page)), write=False))
        if not isinstance(nodes, list):
            fail("collector returned no node list")
    except McpError as exc:
        fail(str(exc))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        fail(f"{type(exc).__name__}: {exc}")

    findings = lint_texts(nodes, terms, allow, min_term_len, min_word_len)
    print(f"page: {args.page}  terms: {len(terms)}  findings: {len(findings)}")
    for finding in findings:
        print(f"  [{finding['severity']:<6}] {finding['board']}: {finding['finding']}")
    if not findings:
        print("  clean on the copy dictionary — that proves the dictionary covered the page, not the copy")

    if args.json:
        args.json.write_text(json.dumps({"page": args.page, "findings": findings}, indent=2) + "\n")
        print(f"wrote {args.json}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
