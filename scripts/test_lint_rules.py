#!/usr/bin/env python3
"""Fixture tests for the audit-driven lint rules and the copy gate.

    python3 -m unittest scripts.test_lint_rules

Every rule gets a failing fixture and a passing one, so a rule that stops
firing fails here instead of passing silently. No network, no Penpot.
"""

from __future__ import annotations

import json
import pathlib
import sys
import unittest

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


def _findings(nodes, needle):
    return [f for f in design_lint.lint(nodes, dict(design_lint.DEFAULTS))
            if needle in f["finding"]]


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
    def _card(self, node_id, x, fill, w=200, h=100, y=500):
        text = _text(node_id + "t", parent=node_id, x=x + 12, y=y + 12,
                     w=w - 24, h=20, ink_w=80)
        return [_node(id=node_id, name=node_id, type="board", parentId="pg",
                      parent="pg", x=x, y=y, w=w, h=h, fill=fill, stroke=True), text]

    def test_same_size_cards_mixed_surface_is_medium(self):
        nodes = [_board(), *self._card("a", 120, "#FFFFFF"), *self._card("b", 340, "#E8EBED")]
        findings = _findings(nodes, "different surface tokens")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "medium")

    def test_alt_card_grid_beside_white_is_medium(self):
        nodes = [_board()]
        for i, x in enumerate((120, 340, 560)):
            nodes += self._card(f"p{i}", x, "#E8EBED", w=200, h=100)
        nodes += self._card("feat", 120, "#FFFFFF", w=240, h=200, y=700)
        findings = _findings(nodes, "beside a white card")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "medium")

    def test_large_alt_card_with_white_is_medium(self):
        nodes = [_board(), *self._card("wide", 120, "#E8EBED", w=500, h=200),
                 *self._card("small", 700, "#FFFFFF", w=200, h=100)]
        findings = _findings(nodes, "large surface.alt")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "medium")

    def test_all_white_is_clean(self):
        nodes = [_board(), *self._card("a", 120, "#FFFFFF"), *self._card("b", 340, "#FFFFFF")]
        self.assertEqual(_findings(nodes, "surface tokens"), [])

    def test_full_width_alt_band_is_clean(self):
        nodes = [_board(), *self._card("band", 0, "#E8EBED", w=1440, h=200),
                 *self._card("card", 120, "#FFFFFF", w=200, h=100)]
        self.assertEqual(_findings(nodes, "large surface.alt"), [])

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


if __name__ == "__main__":
    unittest.main()
