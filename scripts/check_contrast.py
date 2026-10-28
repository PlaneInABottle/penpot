#!/usr/bin/env python3
"""Check WCAG contrast for colour pairs in a DTCG token file.

    check_contrast.py --file design/<project>/tokens.json \
        --pair ink.900:paper.50 --pair muted.500:paper.50 --large ink.900:vermilion.500

Each `--pair` is `<foreground>:<background>`, names as they appear in the token file
(dotted paths without the `color.` prefix, e.g. `ink.900`, `white`). `--large` marks pairs
that are only used at >= 18.66px bold or >= 24px, where WCAG AA needs 3.0 instead of 4.5.

Exit codes: 0 every pair passes, 1 a pair fails, 2 bad input (missing file, unknown token,
malformed pair). No network, no Penpot, stdlib only.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

AA_NORMAL = 4.5
AA_LARGE = 3.0


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def load_colours(path: pathlib.Path) -> dict[str, str]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing {path}")
    except json.JSONDecodeError as error:
        fail(f"{path}: {error}")

    colours: dict[str, str] = {}

    def walk(node, prefix: str) -> None:
        for key, value in node.items():
            if key.startswith("$"):
                continue
            path_key = f"{prefix}{key}"
            if isinstance(value, dict) and "$value" in value:
                if value.get("$type") == "color" or str(value["$value"]).startswith("#"):
                    colours[path_key] = str(value["$value"])
            elif isinstance(value, dict):
                walk(value, f"{path_key}.")

    walk(document, "")
    return {name.removeprefix("color."): value for name, value in colours.items()}


def rgb(value: str) -> tuple[float, float, float]:
    text = value.strip().lstrip("#")
    if len(text) == 3:
        text = "".join(char * 2 for char in text)
    if len(text) == 8:  # #rrggbbaa — Penpot writes alpha last
        text = text[:6]
    if len(text) != 6:
        fail(f"unsupported colour {value!r}")
    return tuple(int(text[i : i + 2], 16) / 255 for i in (0, 2, 4))  # type: ignore[return-value]


def luminance(value: str) -> float:
    def channel(raw: float) -> float:
        return raw / 12.92 if raw <= 0.03928 else ((raw + 0.055) / 1.055) ** 2.4

    red, green, blue = (channel(part) for part in rgb(value))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def ratio(first: str, second: str) -> float:
    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", required=True, type=pathlib.Path)
    parser.add_argument("--pair", action="append", default=[], metavar="FG:BG")
    parser.add_argument("--large", action="append", default=[], metavar="FG:BG")
    arguments = parser.parse_args()

    colours = load_colours(arguments.file)
    if not colours:
        fail(f"{arguments.file}: no colour tokens found")
    if not arguments.pair and not arguments.large:
        fail("no pairs given; pass --pair fg:bg (see --help)")

    rows: list[tuple[str, str, float, float, bool]] = []
    for spec, is_large in [(item, False) for item in arguments.pair] + [(item, True) for item in arguments.large]:
        if ":" not in spec:
            fail(f"malformed pair {spec!r}, expected fg:bg")
        foreground, background = spec.split(":", 1)
        for name in (foreground, background):
            if name not in colours:
                fail(f"unknown colour token {name!r}; known: {', '.join(sorted(colours))}")
        rows.append(
            (foreground, background, ratio(colours[foreground], colours[background]),
             AA_LARGE if is_large else AA_NORMAL, is_large)
        )

    failures = 0
    print(f"{'foreground':<16} {'background':<16} {'ratio':>6}  {'min':>4}  result")
    for foreground, background, value, minimum, is_large in rows:
        ok = value >= minimum
        failures += 0 if ok else 1
        tag = "large" if is_large else "text"
        print(f"{foreground:<16} {background:<16} {value:>6.2f}  {minimum:>4.1f}  {'pass' if ok else 'FAIL'} ({tag})")

    print(f"\n{len(rows) - failures}/{len(rows)} pairs pass")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
