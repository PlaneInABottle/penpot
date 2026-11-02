#!/usr/bin/env python3
"""Offline tests for docs_check: ceilings, links, vocabulary, repetition.

    python3 -m unittest scripts.test_docs_check

Each fixture builds a throwaway root, so the real tree's line counts never
decide a test outcome.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import pathlib
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import docs_check  # noqa: E402

SHORT = "# skill\n\nA rule that fits.\n"


def build_root(base: pathlib.Path, agents: str = SHORT, overrides: dict[str, str] | None = None) -> pathlib.Path:
    """Write a minimal tree: AGENTS.md, every manifest file, then overrides."""
    (base / "AGENTS.md").write_text(agents, encoding="utf-8")
    for rel, ceiling in docs_check.MANIFEST.items():
        if rel == "AGENTS.md":
            continue
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(SHORT, encoding="utf-8")
    for rel, text in (overrides or {}).items():
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return base


def run(root: pathlib.Path, *extra: str) -> tuple[int, str]:
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        code = docs_check.main(["--root", str(root), *extra])
    return code, stream.getvalue()


class DocsCheck(unittest.TestCase):
    def test_clean_tree_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = build_root(pathlib.Path(tmp))
            code, out = run(root)
            self.assertEqual(code, 0, out)
            self.assertIn("findings: 0", out)

    def test_line_ceiling_and_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = build_root(pathlib.Path(tmp), agents="# agents\n" + "line\n" * 200)
            code, out = run(root)
            self.assertEqual(code, 1, out)
            self.assertIn("201 lines > 120", out)

        with tempfile.TemporaryDirectory() as tmp:
            root = build_root(pathlib.Path(tmp))
            (root / "AGENTS.md").unlink()
            code, out = run(root)
            self.assertEqual(code, 2, out)
            self.assertIn("missing", out)

    def test_unresolved_link_is_a_finding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = build_root(
                pathlib.Path(tmp),
                agents="# agents\n\nSee [craft](.agents/skills/penpot-design-system/references/craft.md).\n\n"
                "Also [gone](missing.md) and [web](https://example.com/x.md).\n",
            )
            code, out = run(root)
            self.assertEqual(code, 1, out)
            self.assertIn("unresolved link: missing.md", out)
            self.assertNotIn("example.com", out)

    def test_bullet_and_table_repeats_are_visible(self) -> None:
        sentence = "A screen is finished only when every gate below holds on the final built state today."
        with tempfile.TemporaryDirectory() as tmp:
            root = build_root(
                pathlib.Path(tmp),
                agents=f"# agents\n\n- {sentence}\n\n| {sentence} | note |\n",
                overrides={
                    ".agents/skills/ux-design-process/SKILL.md": f"# ux\n\n- {sentence}\n",
                    ".agents/skills/design-verification/SKILL.md":
                        f"# done\n\n| concern | rule |\n|---|---|\n| {sentence} | note |\n",
                },
            )
            code, out = run(root)
            self.assertEqual(code, 1, out)
            self.assertIn("repeat: .agents/skills/ux-design-process/SKILL.md", out)
            self.assertIn("repeat: .agents/skills/design-verification/SKILL.md", out)

    def test_fences_and_table_separators_are_not_prose(self) -> None:
        sentence = "A screen is finished only when every gate below holds on the final built state today."
        with tempfile.TemporaryDirectory() as tmp:
            root = build_root(
                pathlib.Path(tmp),
                agents=f"# agents\n\n```sh\n{sentence}\n{sentence}\n```\n\n"
                       "| a | b |\n|---|---|\n| one | two |\n",
            )
            code, out = run(root)
            self.assertEqual(code, 0, out)

    def test_readme_and_template_links_and_repeats_are_checked(self) -> None:
        sentence = "A screen is finished only when every gate below holds on the final built state today."
        with tempfile.TemporaryDirectory() as tmp:
            root = build_root(
                pathlib.Path(tmp),
                agents=f"# agents\n\n{sentence}\n",
                overrides={
                    "README.md": "# readme\n\nSee [gone](missing-runtime.md).\n",
                    "design/_template/brief.md": f"# brief\n\n{sentence}\n",
                },
            )
            code, out = run(root)
            self.assertEqual(code, 1, out)
            self.assertIn("link: README.md: unresolved link: missing-runtime.md", out)
            self.assertIn("repeat: design/_template/brief.md", out)

    def test_template_placeholders_are_not_banned_vocabulary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = build_root(
                pathlib.Path(tmp),
                overrides={
                    "design/_template/build/README.md":
                        "# build\n\nRun `screen-NN.js` for the `<board>` on `<page>`.\n",
                },
            )
            code, out = run(root)
            self.assertEqual(code, 0, out)

    def test_banned_tokens_and_repeated_sentences(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sentence = "A screen is finished only when every gate below holds on the final built state today."
            root = build_root(
                pathlib.Path(tmp),
                agents=f"# agents\n\n{sentence}\n\nIncident: a board edge was off by 120px.\n",
                overrides={
                    ".agents/skills/ux-design-process/SKILL.md": f"# ux\n\n{sentence}\n\nVersions 2.18.5 are fine.\n",
                    ".agents/skills/penpot-design-system/references/craft.md": "# craft\n\nscreen-01 is banned.\n",
                },
            )
            code, out = run(root)
            self.assertEqual(code, 1, out)
            self.assertIn("banned: AGENTS.md: line 5: Incident", out)
            self.assertIn("banned: .agents/skills/penpot-design-system/references/craft.md: line 3: screen-01", out)
            self.assertIn("repeat: .agents/skills/ux-design-process/SKILL.md", out)
            self.assertNotIn("2.18.5", out)

            code, raw = run(root, "--json")
            report = json.loads(raw)
            kinds = {item["kind"] for item in report["findings"]}
            self.assertEqual(code, 1)
            self.assertEqual(kinds, {"banned", "repeat"})


if __name__ == "__main__":
    unittest.main()
