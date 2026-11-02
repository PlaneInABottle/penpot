#!/usr/bin/env python3
"""Fixture tests for the audit-driven lint rules and the copy gate.

    python3 -m unittest scripts.test_lint_rules

Every rule gets a failing fixture and a passing one, so a rule that stops
firing fails here instead of passing silently. No network, no Penpot.
"""

from __future__ import annotations

import contextlib
import io
import json
import pathlib
import re
import sys
import tempfile
import unittest
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import design_lint  # noqa: E402
import tokens_sync  # noqa: E402


def _node(**over):
    base = {
        "id": "n", "parentId": None, "name": "shape", "type": "rectangle",
        "parent": None, "x": 0, "y": 0, "w": 100, "h": 40,
        "fill": None, "stroke": False, "img": False, "radius": None,
        "shadows": 0, "fontSize": None, "lineHeight": None, "text": None,
        "align": "left", "inkX": None, "inkY": None, "inkW": None, "inkH": None,
        "inkTop": None, "inkBottom": None,
    }
    base.update(over)
    return base


def _board(**over):
    return _node(id="pg", name="page", type="board", parentId=None,
                 x=0, y=0, w=1440, h=2000, **over)


def _text(node_id, parent="pg", x=120, y=100, w=400, h=22, size=16,
          line="1.5", text="Copy", ink_x=None, ink_y=None, ink_w=None, ink_h=None,
          name=None):
    ink_x = x if ink_x is None else ink_x
    ink_y = y + 1 if ink_y is None else ink_y
    ink_w = (w - 20) if ink_w is None else ink_w
    ink_h = (size * 1.1) if ink_h is None else ink_h
    return _node(id=node_id, name=name or ("label " + node_id), type="text",
                 parentId=parent, parent=parent, x=x, y=y, w=w, h=h,
                 fill="#0E1318", fontSize=size, lineHeight=line,
                 text=text, inkX=ink_x, inkY=ink_y, inkW=ink_w, inkH=ink_h)


def _findings(nodes, needle, rules=None):
    rules = dict(rules or design_lint.DEFAULTS)
    return [f for f in design_lint.lint(nodes, rules) if needle in f["finding"]]


def _rules(nodes, rules=None):
    """(rule id, severity) for every grouped finding."""
    rules = dict(rules or design_lint.DEFAULTS)
    return [(f["rule"], f["severity"]) for f in design_lint.lint(nodes, rules)]


def _run_lint(nodes, argv_extra=(), rules=None, page="Mobil", include_page=True):
    """Run design_lint.main() offline on `nodes`; returns (code, output, json doc)."""
    out, err, doc = io.StringIO(), io.StringIO(), None
    with tempfile.TemporaryDirectory() as tmp:
        dump = pathlib.Path(tmp) / f"{page}.nodes.json"
        dump.write_text(json.dumps(nodes))
        json_out = pathlib.Path(tmp) / "lint.json"
        argv = ["design_lint.py", "--from-nodes", str(dump), "--json", str(json_out), *argv_extra]
        if include_page:
            argv += ["--page", page]
        if rules is not None:
            rules_path = pathlib.Path(tmp) / "craft-rules.json"
            rules_path.write_text(json.dumps(rules))
            argv += ["--rules", str(rules_path)]
        with mock.patch.object(sys, "argv", argv), \
                mock.patch.object(design_lint, "load_url",
                                  lambda: (_ for _ in ()).throw(AssertionError("plugin call"))), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = design_lint.main()
            except SystemExit as exc:
                code = int(exc.code or 0)
        if json_out.exists():
            doc = json.loads(json_out.read_text())
    return code, out.getvalue() + err.getvalue(), doc


class InkVsBoxTest(unittest.TestCase):
    def test_ink_overflows_board_with_no_card(self):
        # the box fits the board, the measured ink does not
        text = _text("t", x=1200, y=100, w=200, ink_x=1200, ink_w=300)
        findings = _findings([_board(), text], "overflows its container page")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "high")
        self.assertIn("right +60px", findings[0]["finding"])

    def test_box_exceeds_its_parent_card(self):
        card = _node(id="card", name="card", type="board", parentId="pg",
                     parent="pg", x=120, y=500, w=400, h=120, fill="#FFFFFF", stroke=True)
        text = _text("t", parent="card", x=130, y=510, w=500, ink_w=200)
        findings = _findings([_board(), card, text], "box (500x22) exceeds its container card")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "high")

    def test_no_container_is_medium(self):
        text = _text("t", x=-50, y=-50, w=100, ink_x=-50, ink_y=-50, ink_w=80)
        findings = _findings([_board(), text], "no enclosing container")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "medium")

    def test_text_inside_board_is_clean(self):
        self.assertEqual(_findings([_board(), _text("t")], "overflows its container"), [])


class MinGapTest(unittest.TestCase):
    def _stack(self, meta_y, rule=True):
        nodes = [_board(),
                 _text("title", x=168, y=100, w=472, h=39, size=30, line="1.2",
                       text="Kalp yetersizliği", ink_h=36, ink_y=100),
                 _text("meta", x=168, y=meta_y, w=472, h=20, size=13, line="1.5",
                       text="412 üye", ink_h=16, ink_y=meta_y + 1)]
        if rule:
            nodes.append(_node(id="rule", name="row rule", type="rectangle", parentId="pg",
                               parent="pg", x=120, y=meta_y + 31, w=560, h=1, fill="#DDE1E4"))
        return nodes

    def test_touching_title_meta_is_high(self):
        # gap 3px, line 19.5px -> 0.15x
        findings = _findings(self._stack(139), "ink gap")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "high")

    def test_five_px_title_meta_is_medium(self):
        # 01 group rows: 5px against the 19.5px meta line
        findings = _findings(self._stack(141), "ink gap")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "medium")

    def test_generous_gap_is_clean(self):
        self.assertEqual(_findings(self._stack(160), "ink gap"), [])

    def test_without_a_row_rule_is_clean(self):
        # the 19-giris logo lockup / 12 progress stat: tight but not a list row
        self.assertEqual(_findings(self._stack(139, rule=False), "ink gap"), [])

    def test_label_above_title_is_clean(self):
        nodes = [_board(),
                 _text("label", x=268, y=100, w=65, h=20, size=13, line="1.2",
                       text="AKADEMİ", ink_h=17, ink_y=100),
                 _text("title", x=268, y=140, w=760, h=56, size=44, line="1.06",
                       text="Kurs", ink_h=54, ink_y=136),
                 _node(id="rule", name="head rule", type="rectangle", parentId="pg",
                       parent="pg", x=120, y=200, w=1200, h=1, fill="#DDE1E4")]
        self.assertEqual(_findings(nodes, "ink gap"), [])


class ListMarkerTest(unittest.TestCase):
    def _dot(self, y=104):
        return _node(id="dot", name="bullets dot 0", type="rectangle", parentId="pg",
                     parent="pg", x=120, y=y, w=6, h=6, fill="#C4122F")

    def _item(self):
        # 16px / 1.4 line: first-line ink centre = 102 + 19.5/2 = 111.75
        return _text("item", x=136, y=100, w=500, h=22, size=16, line="1.4",
                     ink_y=102, ink_h=19.5)

    def test_misaligned_dot_is_high(self):
        findings = _findings([_board(), self._dot(104), self._item()], "list marker")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "high")

    def test_aligned_dot_is_clean(self):
        self.assertEqual(_findings([_board(), self._dot(108), self._item()], "list marker"), [])

    def test_separator_left_edge_must_match(self):
        nodes = [_board(), self._dot(108), self._item(),
                 _node(id="sep", name="row rule", type="rectangle", parentId="pg",
                       parent="pg", x=126, y=140, w=560, h=1, fill="#DDE1E4")]
        findings = _findings(nodes, "separator")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "medium")

    def test_aligned_separator_is_clean(self):
        nodes = [_board(), self._dot(108), self._item(),
                 _node(id="sep", name="row rule", type="rectangle", parentId="pg",
                       parent="pg", x=120, y=140, w=560, h=1, fill="#DDE1E4")]
        self.assertEqual(_findings(nodes, "separator"), [])


class SurfaceRoleTest(unittest.TestCase):
    """surface.role has no shipped palette: every fixture declares one."""

    @staticmethod
    def _rules(alt="#E8EBED"):
        return {**design_lint.DEFAULTS, "surface_white": ["#FFFFFF"], "surface_alt": [alt]}

    def _card(self, node_id, x, fill, w=200, h=100, y=500):
        text = _text(node_id + "t", parent=node_id, x=x + 12, y=y + 12,
                     w=w - 24, h=20, ink_w=80)
        return [_node(id=node_id, name=node_id, type="board", parentId="pg",
                      parent="pg", x=x, y=y, w=w, h=h, fill=fill, stroke=True), text]

    def test_same_size_cards_mixed_surface_is_medium(self):
        nodes = [_board(), *self._card("a", 120, "#FFFFFF"), *self._card("b", 340, "#E8EBED")]
        findings = _findings(nodes, "different surface tokens", rules=self._rules())
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "medium")

    def test_alt_card_grid_beside_white_is_medium(self):
        nodes = [_board()]
        for i, x in enumerate((120, 340, 560)):
            nodes += self._card(f"p{i}", x, "#E8EBED", w=200, h=100)
        nodes += self._card("feat", 120, "#FFFFFF", w=240, h=200, y=700)
        findings = _findings(nodes, "beside a white card", rules=self._rules())
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "medium")

    def test_large_alt_card_with_white_is_medium(self):
        nodes = [_board(), *self._card("wide", 120, "#E8EBED", w=500, h=200),
                 *self._card("small", 700, "#FFFFFF", w=200, h=100)]
        findings = _findings(nodes, "large surface.alt", rules=self._rules())
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "medium")

    def test_all_white_is_clean(self):
        nodes = [_board(), *self._card("a", 120, "#FFFFFF"), *self._card("b", 340, "#FFFFFF")]
        self.assertEqual(_findings(nodes, "surface tokens", rules=self._rules()), [])

    def test_full_width_alt_band_is_clean(self):
        nodes = [_board(), *self._card("band", 0, "#E8EBED", w=1440, h=200),
                 *self._card("card", 120, "#FFFFFF", w=200, h=100)]
        self.assertEqual(_findings(nodes, "large surface.alt", rules=self._rules()), [])

    def test_template_palette_behaves_like_the_explicit_fixture(self):
        nodes = [_board(), *self._card("a", 120, "#FFFFFF"),
                 *self._card("b", 340, "#EAEAE8")]
        findings = _findings(nodes, "different surface tokens", rules=self._rules("#EAEAE8"))
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "medium")

    def test_unconfigured_palette_warns_and_skips(self):
        code, out, _ = _run_lint([_board()], page="Mobil")
        self.assertEqual(code, 0, out)
        self.assertIn("surface.role is not configured", out)
        self.assertNotIn("different surface tokens", out)

    def test_duplicate_token_value_is_flagged(self):
        specs = [
            {"type": "color", "name": "white", "value": "#FFFFFF"},
            {"type": "color", "name": "bone", "value": "#ffffff"},
            {"type": "color", "name": "ink", "value": "#0E1318"},
        ]
        conflicts = tokens_sync.duplicate_values(specs)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0][1], ["bone", "white"])

    def test_live_ihkd_tokens_report_white_bone(self):
        doc = json.loads((HERE.parent / "design" / "ihkd" / "tokens.json").read_text())
        conflicts = tokens_sync.duplicate_values(tokens_sync.to_specs(doc))
        names = [n for _, group in conflicts for n in group]
        self.assertIn("white", names)
        self.assertIn("bone", names)


class FloatingSiblingTest(unittest.TestCase):
    def _button(self, y=400):
        return [_node(id="btn", name="band cta", type="board", parentId="pg",
                      parent="pg", x=120, y=y, w=168, h=52, fill="#FFFFFF", stroke=True),
                _text("btnlabel", parent="btn", x=120, y=y + 16, w=168, h=23,
                      text="Kayıt ol", name="band cta / label", ink_h=19.5)]

    def _link(self, y=352):
        return _text("link", x=312, y=y, w=93, h=22, text="Programı gör",
                     name="band cta 2", ink_y=y + 1, ink_h=19.5)

    def test_floating_link_is_high(self):
        findings = _findings([_board(), *self._button(), self._link()], "CTA group misaligned")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "high")

    def test_small_vertical_drift_is_medium(self):
        # link centre 418.75 vs button centre 426 -> 7.25px
        findings = _findings([_board(), *self._button(), self._link(408)], "CTA group misaligned")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "medium")

    def test_aligned_link_is_clean(self):
        # link centre 426 -> 0px
        self.assertEqual(_findings([_board(), *self._button(), self._link(415.25)],
                                   "CTA group misaligned"), [])

    def test_stacked_pair_is_clean(self):
        link = self._link()
        link["x"] = 120
        link["inkX"] = 120
        self.assertEqual(_findings([_board(), *self._button(), link], "CTA group misaligned"), [])

    def test_far_apart_pair_is_clean(self):
        self.assertEqual(_findings([_board(), *self._button(), self._link(100)],
                                   "CTA group misaligned"), [])


class StatSizeTest(unittest.TestCase):
    def _stat(self, node_id, x, size):
        return [_text(node_id, x=x, y=100, w=120, h=24, size=size, line="1.4",
                      text="6.847", ink_h=size * 1.35),
                _text(node_id + "l", x=x, y=136, w=120, h=20, size=13, line="1.5",
                      text="üye", ink_h=16.5)]

    def test_small_stat_value_is_medium(self):
        nodes = [_board(), *self._stat("v0", 120, 16), *self._stat("v1", 420, 16)]
        findings = _findings(nodes, "stats row")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "medium")
        self.assertIn("16px", findings[0]["finding"])

    def test_large_stat_value_is_clean(self):
        nodes = [_board(), *self._stat("v0", 120, 30), *self._stat("v1", 420, 30)]
        self.assertEqual(_findings(nodes, "stats row"), [])

    def test_numbered_list_is_not_a_stat_row(self):
        nodes = [_board(),
                 *self._stat("v0", 120, 13), *self._stat("v1", 420, 13)]
        # value and label are the same size: a numbered step, not a stat
        self.assertEqual(_findings(nodes, "stats row"), [])


class DeadSpaceTest(unittest.TestCase):
    def _card(self, tiles=False):
        card = _node(id="c", name="plan", type="board", parentId="pg",
                     parent="pg", x=120, y=100, w=460, h=240, fill="#FFFFFF", stroke=True)
        nodes = [_board(), card,
                 _text("t", parent="c", x=140, y=120, w=200, h=39, size=30, line="1.1",
                       text="A", ink_y=120, ink_h=37)]
        if tiles:
            nodes.append(_node(id="tile", name="hall 3", type="rectangle", parentId="c",
                               parent="c", x=140, y=190, w=200, h=120, fill="#E8EBED"))
        return nodes

    def test_card_whose_text_ends_high_is_medium(self):
        findings = _findings(self._card(), "dead space")
        self.assertEqual(len(findings), 1)

    def test_card_ending_in_a_tile_is_clean(self):
        # 10-konaklama: the hall tiles reach 26px from the card edge
        self.assertEqual(_findings(self._card(tiles=True), "dead space"), [])


class FigureOverMetaTest(unittest.TestCase):
    """A 44px figure over its 13px label: textBounds reserves the font's descent
    under digits that have none, so 06-kongre's stat row measured 4px of air
    where the render shows 24px. The rule keeps firing on prose."""

    def _stack(self, figure="96", meta_y=160, rule=True):
        nodes = [_board(),
                 _text("value", x=120, y=100, w=240, h=61, size=44, line="1.1",
                       text=figure, ink_y=100, ink_h=58.5),
                 _text("meta", x=120, y=meta_y, w=240, h=20, size=13, line="1.5",
                       text="oturum", ink_y=meta_y + 1.5, ink_h=16.5)]
        if rule:
            nodes.append(_node(id="rule", name="row rule", type="rectangle", parentId="pg",
                               parent="pg", x=120, y=meta_y + 38, w=1200, h=1, fill="#DDE1E4"))
        return nodes

    def test_figure_without_descenders_is_clean(self):
        # ink gap 3px, but "96" ends at its baseline: 3 + 0.3*44 = 16px of air
        self.assertEqual(_findings(self._stack(), "ink gap"), [])

    def test_figure_with_a_descender_still_fires(self):
        # "9g" really does reach into the gap
        findings = _findings(self._stack(figure="9g"), "ink gap")
        self.assertEqual(len(findings), 1)

    def test_figure_with_a_word_and_no_descender_is_clean(self):
        # 16-makale's "14 saat" cell: the word carries no descender either
        self.assertEqual(_findings(self._stack(figure="14 saat"), "ink gap"), [])


class ColumnBandTest(unittest.TestCase):
    """A hairline is a column band only for a text that has no box of its own.
    11-akademi's 760px lede was measured against the search field's 400px
    underline 128px below it and reported 305px of overflow that the box
    already forbids."""

    def _nodes(self, text_w, ink_w=705):
        return [_board(),
                _text("lede", x=120, y=100, w=text_w, h=62, size=22, line="1.5",
                      text="46 kurs", ink_y=101, ink_h=60, ink_w=ink_w),
                _node(id="line", name="search line", type="rectangle", parentId="pg",
                      parent="pg", x=120, y=289, w=400, h=1, fill="#B9C0C6")]

    def test_declared_width_text_is_not_measured_against_a_lower_rule(self):
        self.assertEqual(_findings(self._nodes(760), "column band"), [])

    def test_autowidth_text_past_a_row_rule_is_high(self):
        findings = _findings(self._nodes(707), "column band")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "high")


class IntraCardGapTest(unittest.TestCase):
    def _card(self, extra=(), meta_text="ikinci satır"):
        card = _node(id="card", name="card", type="board", parentId="pg",
                     parent="pg", x=120, y=100, w=400, h=240, fill="#FFFFFF", stroke=True)
        nodes = [_board(), card,
                 _text("a", parent="card", x=140, y=120, w=360, h=22, size=16, line="1.5",
                       text="Birinci satır", ink_y=122, ink_h=19.5),
                 _text("b", parent="card", x=140, y=220, w=360, h=22, size=16, line="1.5",
                       text=meta_text, ink_y=222, ink_h=19.5)]
        return nodes + list(extra)

    def test_two_texts_with_nothing_between_is_medium(self):
        findings = _findings(self._card(), "intra-card gap")
        self.assertEqual(len(findings), 1)

    def test_hairline_between_the_lines_is_a_divider(self):
        # 20-panel aidat: 2026 / 2025, 36px apart, a 1px rule at their centre
        rule = _node(id="r", name="ai rule 2", type="rectangle", parentId="card",
                     parent="card", x=140, y=175, w=360, h=1, fill="#DDE1E4")
        self.assertEqual(_findings(self._card([rule]), "intra-card gap"), [])

    def test_composite_between_the_lines_is_a_divider(self):
        # 13-kilavuzlar: the ECG strip between the featured body and its meta
        ecg = _node(id="e", name="feat ecg", type="group", parentId="card",
                    parent="card", x=140, y=150, w=360, h=60)
        self.assertEqual(_findings(self._card([ecg]), "intra-card gap"), [])

    def test_all_caps_kicker_starts_a_block(self):
        # 16-makale: p3 over "SAYILARLA PROGRAM"
        nodes = self._card(meta_text="SAYILARLA PROGRAM")
        nodes = [n if n["id"] != "b" else dict(n, fontSize=13) for n in nodes]
        self.assertEqual(_findings(nodes, "intra-card gap"), [])


class CopyLintTest(unittest.TestCase):
    def _find(self, text, terms=("kalp",), allow=()):
        import copy_lint
        return copy_lint.find_typos([text], list(terms), list(allow))

    def test_letter_drop_is_flagged(self):
        findings = self._find("KAP yetersizliği")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0][1], "kap")

    def test_correct_term_is_clean(self):
        self.assertEqual(self._find("KALP yetersizliği"), [])

    def test_allowlisted_word_is_clean(self):
        self.assertEqual(self._find("KAP yetersizliği", allow=("kap",)), [])

    def test_real_dictionary_has_enough_terms(self):
        doc = json.loads((HERE.parent / "design" / "ihkd" / "copy-terms.json").read_text())
        self.assertGreaterEqual(len(doc["terms"]), 40)
        self.assertIn("kalp", doc["terms"])
        self.assertIn("kardiyoloji", doc["terms"])


class InkUnavailableTest(unittest.TestCase):
    """A page that is not open reports `textBounds: null` for every text.

    The ink rules skip unmeasured text, so a lint of a background page used to
    end with "0 high" — a clean verdict about a page it never measured.
    """

    def _run(self, nodes: list[dict], page: str = "Mobil") -> tuple[int, str, dict | None]:
        result = {"result": {"content": [{"type": "text", "text": json.dumps(nodes)}]}}
        out, err = io.StringIO(), io.StringIO()
        doc = None
        with tempfile.TemporaryDirectory() as tmp:
            json_out = pathlib.Path(tmp) / "lint.json"
            argv = ["design_lint.py", "--page", page, "--json", str(json_out)]
            with mock.patch.object(sys, "argv", argv), \
                    mock.patch.object(design_lint, "load_url", lambda: "http://local/mcp?t=x"), \
                    mock.patch.object(design_lint, "ensure_helpers", lambda *a, **k: "1.5.0"), \
                    mock.patch.object(design_lint, "call_execute_code", lambda *a, **k: result), \
                    contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                try:
                    code = design_lint.main()
                except SystemExit as exc:
                    code = int(exc.code or 0)
            if json_out.exists():
                doc = json.loads(json_out.read_text())
        return code, out.getvalue() + err.getvalue(), doc

    def _page(self, measured: int, unmeasured: int) -> list[dict]:
        nodes = [_board(), _text("title", size=56, y=60)]  # keeps the type scale valid
        for i in range(measured):
            nodes.append(_text(f"m{i}", y=140 + 30 * i))
        for i in range(unmeasured):
            node = _text(f"u{i}", y=800 + 30 * i)
            node.update(inkX=None, inkY=None, inkW=None, inkH=None)
            nodes.append(node)
        return nodes

    def test_background_page_exits_2_and_is_not_a_clean_run(self):
        nodes = self._page(measured=2, unmeasured=4)  # 6 texts, 4 unmeasured
        # the defect: the same page lints "clean" because ink checks skip nulls
        self.assertEqual([f for f in design_lint.lint(nodes, dict(design_lint.DEFAULTS))
                          if f["severity"] == "high"], [])
        code, output, doc = self._run(nodes)
        self.assertEqual(code, 2, output)
        self.assertIn("page not active: textBounds unavailable", output)
        self.assertIn("open Mobil", output)
        self.assertIn("findings are NOT valid", output)
        self.assertIs(doc["valid"], False)
        self.assertEqual(doc["findings"], [])

    def test_a_measured_page_stays_valid(self):
        code, output, doc = self._run(self._page(measured=10, unmeasured=0))
        self.assertEqual(code, 0, output)
        self.assertIs(doc["valid"], True)

    def test_five_percent_unmeasured_is_still_valid(self):
        code, _, doc = self._run(self._page(measured=40, unmeasured=2))
        self.assertEqual(code, 0)
        self.assertIs(doc["valid"], True)

    def test_empty_text_carries_no_ink_and_does_not_invalidate(self):
        nodes = self._page(measured=4, unmeasured=0)
        for i in range(6):
            node = _text(f"e{i}", text="", y=900 + 20 * i)
            node.update(inkX=None, inkY=None, inkW=None, inkH=None)
            nodes.append(node)
        code, output, doc = self._run(nodes)
        self.assertEqual(code, 0, output)
        self.assertIs(doc["valid"], True)




class RuleRegistryTest(unittest.TestCase):
    """A rule without an evidence record is a guess: the registry must be total."""

    def test_every_rule_id_in_the_source_is_registered(self):
        source = (HERE / "design_lint.py").read_text()
        used = set(re.findall(r'add\(\s*"([a-z_.]+)"', source))
        self.assertTrue(used, "no add() call found — the scanner broke")
        self.assertEqual(sorted(used - set(design_lint.RULES)), [])

    def test_every_rule_records_its_evidence(self):
        for rule_id, entry in design_lint.RULES.items():
            self.assertTrue(str(entry.get("born_from") or "").strip(), rule_id)
            self.assertEqual(set(entry["corpus"]), {"tp", "fp", "ok"}, rule_id)
            for value in entry["corpus"].values():
                self.assertIsInstance(value, int, rule_id)
            self.assertIn(entry["severity"], {"high", "medium", "low", "retired"}, rule_id)

    def test_a_high_rule_is_a_proven_defect_class(self):
        # HIGH breaks the gate: only a class the museum can reproduce carries it.
        museum = {"board.overflow", "fit.rule", "text.overlap", "marker.centre", "cta.float"}
        for rule_id in museum:
            self.assertEqual(design_lint.RULES[rule_id]["severity"], "high", rule_id)

    def test_a_rule_with_only_wrong_positives_is_retired(self):
        retired = [r for r, e in design_lint.RULES.items() if e["severity"] == "retired"]
        self.assertEqual(retired, ["inline.baseline"])
        self.assertGreater(design_lint.RULES["inline.baseline"]["corpus"]["fp"], 0)

    def test_retired_inline_rule_no_longer_fires(self):
        # the old rule flagged every 13/16 pair; a mixed-size row is not a defect
        nodes = [_board(),
                 _text("num", x=120, y=100, w=40, h=24, size=16, text="58", ink_h=19.5),
                 _text("cap", x=190, y=104, w=80, h=20, size=13, text="MEKTUP", ink_h=17.5)]
        self.assertNotIn("inline.baseline", {rule for rule, _ in _rules(nodes)})


class FromNodesTest(unittest.TestCase):
    """--from-nodes lints a frozen dump: the same snapshot decides before/after."""

    def test_offline_run_needs_no_plugin(self):
        nodes = [_board(), _text("title", size=56, y=60, line="1.1", text="Başlık"),
                 _text("body", y=200, text="Gövde metni")]
        code, output, doc = _run_lint(nodes)
        self.assertEqual(code, 0, output)
        self.assertIs(doc["valid"], True)
        self.assertEqual(doc["page"], "Mobil")

    def test_a_finding_survives_the_offline_path(self):
        nodes = [_board(), _text("title", size=56, y=60, line="1.1", text="Başlık"),
                 _text("body", y=200, text="Gövde metni"),
                 _text("t", x=1200, y=400, w=200, ink_x=1200, ink_w=300)]
        code, output, doc = _run_lint(nodes)
        self.assertEqual(code, 1, output)
        self.assertEqual(len([f for f in doc["findings"] if f["severity"] == "high"]), 1)

    def test_page_comes_from_the_dump_name_when_omitted(self):
        nodes = [_board(), _text("title", size=56, y=60, line="1.1", text="Başlık"),
                 _text("body", y=200, text="Gövde metni")]
        code, output, doc = _run_lint(nodes, include_page=False)
        self.assertEqual(code, 0, output)
        self.assertEqual(doc["page"], "Mobil")


class GroupingTest(unittest.TestCase):
    """One root cause repeated per row is one finding with a count."""

    def _card(self, index, meta_y):
        card = _node(id=f"c{index}", name=f"sess card {index}", type="board", parentId="pg",
                     parent="pg", x=120 + 240 * index, y=100, w=232, h=200, fill="#FFFFFF", stroke=True)
        return [card,
                _text(f"t{index}", parent=f"c{index}", x=136 + 240 * index, y=116, w=200, h=22,
                      size=16, text="Oturum", ink_y=116, ink_h=19.5),
                _text(f"m{index}", parent=f"c{index}", x=136 + 240 * index, y=meta_y, w=200, h=40,
                      size=13, text="13:00 · 30 dk", ink_y=meta_y + 1, ink_h=16.5)]

    def test_same_cause_rows_merge_into_one_group(self):
        nodes = [_board()]
        for i, meta_y in enumerate((180, 190, 186)):
            nodes += self._card(i, meta_y)
        gaps = [f for f in design_lint.lint(nodes, dict(design_lint.DEFAULTS))
                if f["rule"] == "gap.intra_card"]
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0]["count"], 3)
        self.assertEqual(len(gaps[0]["instances"]), 3)

    def test_different_causes_stay_apart(self):
        nodes = [_board(), *self._card(0, 180)]
        nodes.append(_node(id="wide", name="wide card", type="board", parentId="pg", parent="pg",
                           x=800, y=100, w=300, h=200, fill="#FFFFFF", stroke=True))
        nodes.append(_text("wt", parent="wide", x=816, y=116, w=260, h=22, size=16,
                           text="Başlık", ink_y=116, ink_h=19.5))
        nodes.append(_text("wm", parent="wide", x=816, y=190, w=260, h=40, size=13,
                           text="meta", ink_y=191, ink_h=16.5))
        names = {f["group"] for f in design_lint.lint(nodes, dict(design_lint.DEFAULTS))
                 if f["rule"] == "gap.intra_card"}
        self.assertGreaterEqual(len(names), 2)


class AcknowledgeTest(unittest.TestCase):
    """An accepted design decision is declared with a reason and counted apart."""

    def _nodes(self):
        return [_board(),
                _text("title", size=56, y=40, line="1.1", x=120, w=400, h=61,
                      text="Başlık", ink_y=40, ink_h=60),
                _node(id="card", name="form", type="board", parentId="pg", parent="pg",
                      x=120, y=100, w=400, h=160, fill="#FFFFFF", stroke=True),
                _text("a", parent="card", x=140, y=120, w=360, h=22, size=16,
                      text="Birinci satır", ink_y=122, ink_h=19.5),
                _text("b", parent="card", x=140, y=220, w=360, h=22, size=16,
                      text="İkinci satır", ink_y=222, ink_h=19.5)]

    def _rules_with(self, entry):
        rules = dict(design_lint.DEFAULTS)
        rules["acknowledge"] = [entry]
        return rules

    def test_a_reasoned_acknowledgement_is_counted_apart(self):
        rules = self._rules_with({"rule": "gap.intra_card", "board": "page",
                                  "shape-prefix": "form", "reason": "consent row break, 1:1"})
        findings = [f for f in design_lint.lint(self._nodes(), rules)
                    if f["rule"] == "gap.intra_card"]
        self.assertEqual(len(findings), 1)
        self.assertTrue(findings[0]["acknowledged"])
        self.assertIn("consent", findings[0]["ack_reason"])

    def test_an_acknowledgement_without_a_reason_is_ignored(self):
        rules = self._rules_with({"rule": "gap.intra_card", "board": "page", "shape-prefix": "form"})
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            findings = [f for f in design_lint.lint(self._nodes(), rules)
                        if f["rule"] == "gap.intra_card"]
        self.assertFalse(findings[0]["acknowledged"])
        self.assertIn("without a reason", err.getvalue())

    def test_a_narrow_acknowledgement_does_not_cover_another_board(self):
        rules = self._rules_with({"rule": "gap.intra_card", "board": "elsewhere",
                                  "shape-prefix": "form", "reason": "looked at 1:1"})
        findings = [f for f in design_lint.lint(self._nodes(), rules)
                    if f["rule"] == "gap.intra_card"]
        self.assertFalse(findings[0]["acknowledged"])

    def test_acknowledged_findings_stay_in_the_output_and_the_json(self):
        code, output, doc = _run_lint(
            self._nodes(), rules={"min_step_ratio": 1.2,
                                  "acknowledge": [{"rule": "gap.intra_card", "board": "page",
                                                   "shape-prefix": "form", "reason": "consent row"}]})
        self.assertEqual(code, 0, output)
        self.assertIn("acknowledged: 1", output)
        self.assertIn("consent row", output)
        self.assertTrue(any(f["acknowledged"] for f in doc["findings"]))
        self.assertEqual(doc["summary"]["acknowledged"], 1)


class SeverityOutputTest(unittest.TestCase):
    """MEDIUM is reported and never gates; LOW is hidden unless --verbose."""

    def _nodes(self):
        return [_board(),
                _text("title", size=56, y=60, line="1.1", w=400, h=61,
                      text="Başlık", ink_y=60, ink_h=60),
                _text("legal", x=120, y=200, w=600, h=20, size=13,
                      text="Meşrutiyet Cad. 24/7, 06420 Çankaya, Ankara · +90 312 425 18 40", ink_y=200, ink_h=17.5)]

    def test_low_is_hidden_by_default_and_kept_in_the_json(self):
        code, output, doc = _run_lint(self._nodes())
        self.assertEqual(code, 0, output)
        self.assertNotIn("small paragraph", output)
        self.assertTrue(any(f["severity"] == "low" for f in doc["findings"]))
        self.assertEqual(doc["summary"]["low"], 1)

    def test_verbose_shows_low(self):
        code, output, _ = _run_lint(self._nodes(), argv_extra=("--verbose",))
        self.assertEqual(code, 0, output)
        self.assertIn("small paragraph", output)

    def test_medium_is_reported_and_does_not_break_the_gate(self):
        # one text near the top of a 200px card: the void is a leak, not padding
        nodes = [_board(),
                 _text("title", size=56, y=60, line="1.1", w=400, h=61,
                       text="Başlık", ink_y=60, ink_h=60),
                 _node(id="c", name="card", type="board", parentId="pg", parent="pg",
                       x=120, y=200, w=460, h=120, fill="#FFFFFF", stroke=True),
                 _text("t", parent="c", x=140, y=220, w=200, h=22, size=16,
                       text="Tek satır", ink_y=221, ink_h=19.5)]
        code, output, doc = _run_lint(nodes)
        dead = [f for f in doc["findings"] if f["rule"] == "dead_space"]
        self.assertEqual(code, 0, output)
        self.assertEqual(len(dead), 1)
        self.assertEqual(dead[0]["severity"], "medium")
        self.assertIn("dead space", output)


class DeadSpacePaddingTest(unittest.TestCase):
    """A void that matches the container's own entry inset is padding, not a leak."""

    def _band(self, height, text_y):
        return [_board(),
                _node(id="c", name="band", type="board", parentId="pg", parent="pg",
                      x=0, y=100, w=1440, h=height, fill="#E8EBED"),
                _text("t", parent="c", x=120, y=text_y, w=400, h=22, size=16,
                      text="Tek satır", ink_y=text_y + 1, ink_h=19.5)]

    def test_symmetric_padding_is_clean(self):
        # 70px in, 70px out: the band's own inset (the corpus' 4/4 dead-space hits)
        findings = _findings(self._band(160, 169), "dead space")
        self.assertEqual(findings, [])

    def test_a_void_bigger_than_the_entry_inset_is_medium(self):
        findings = _findings(self._band(100, 120), "dead space")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "medium")


class RegressionMuseumTest(unittest.TestCase):
    """The five eye-caught classes, reproduced by moving one coordinate.

    Each class is built clean first (the mutation is the only difference), and
    the mutant must come back HIGH under its own rule id — this is the guard for
    "a rule change did not lose a real defect".
    """

    def test_regression_museum_overflow(self):
        clean = [_board(), _node(id="s", name="cta", parentId="pg", parent="pg",
                                 x=1100, y=100, w=300, h=52)]
        mutant = [_board(), _node(id="s", name="cta", parentId="pg", parent="pg",
                                  x=1300, y=100, w=300, h=52)]
        self.assertNotIn("board.overflow", {r for r, _ in _rules(clean)})
        self.assertIn(("board.overflow", "high"), _rules(mutant))

    def test_regression_museum_rule_crossing(self):
        def nodes(rule_y):
            return [_board(),
                    _text("meta", x=120, y=100, w=400, h=22, size=13, text="412 üye",
                          ink_y=101, ink_h=16.5),
                    _node(id="r", name="row rule", parentId="pg", parent="pg",
                          x=120, y=rule_y, w=600, h=1, fill="#DDE1E4")]

        self.assertNotIn("fit.rule", {r for r, _ in _rules(nodes(200))})
        self.assertIn(("fit.rule", "high"), _rules(nodes(108)))

    def test_regression_museum_collision(self):
        def nodes(dy):
            return [_board(),
                    _text("a", x=120, y=100, w=400, h=22, size=16, text="Birinci başlık",
                          ink_y=101, ink_h=19.5),
                    _text("b", x=160, y=100 + dy, w=400, h=22, size=16, text="İkinci başlık",
                          ink_y=101 + dy, ink_h=19.5)]

        self.assertNotIn("text.overlap", {r for r, _ in _rules(nodes(60))})
        self.assertIn(("text.overlap", "high"), _rules(nodes(4)))

    def test_regression_museum_bullet_drift(self):
        def nodes(dot_y):
            return [_board(),
                    _node(id="dot", name="bullets dot 0", parentId="pg", parent="pg",
                          x=120, y=dot_y, w=6, h=6, fill="#C4122F"),
                    _text("item", x=136, y=100, w=500, h=22, size=16, line="1.4",
                          text="Kalp yetersizliği", ink_y=102, ink_h=19.5)]

        self.assertNotIn("marker.centre", {r for r, _ in _rules(nodes(108))})
        self.assertIn(("marker.centre", "high"), _rules(nodes(104)))

    def test_regression_museum_floating_cta(self):
        def nodes(link_y):
            return [_board(),
                    _node(id="btn", name="band cta", type="board", parentId="pg", parent="pg",
                          x=120, y=400, w=168, h=52, fill="#FFFFFF", stroke=True),
                    _text("label", parent="btn", x=120, y=416, w=168, h=23, text="Kayıt ol",
                          name="band cta / label", ink_h=19.5),
                    _text("link", x=312, y=link_y, w=93, h=22, text="Programı gör",
                          name="band cta 2", ink_y=link_y + 1, ink_h=19.5)]

        self.assertNotIn("cta.float", {r for r, _ in _rules(nodes(415.25))})
        self.assertIn(("cta.float", "high"), _rules(nodes(352)))


if __name__ == "__main__":
    unittest.main()
