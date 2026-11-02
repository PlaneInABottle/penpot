#!/usr/bin/env python3
"""Offline unit tests for the Penpot automation scripts.

    python3 -m unittest scripts/test_penpot_scripts.py

No network and no Penpot: the MCP responses are fixtures shaped like the ones the
plugin returns.
"""

from __future__ import annotations

import base64
import contextlib
import io
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "design" / "ihkd" / "tools"))
sys.path.insert(0, str(HERE.parent / "design" / "ihkd" / "build"))

import design_qa  # noqa: E402
import penpot_exec  # noqa: E402
import tokens_sync  # noqa: E402
import design_lint  # noqa: E402
import rhythm  # noqa: E402
import media  # noqa: E402

TOKENS_FILE = HERE.parent / "design" / "tokens.json"


def content_result(text: str, is_error: bool = False) -> dict:
    """A tools/call result the way the MCP server returns it."""
    return {
        "jsonrpc": "2.0",
        "id": 2,
        "result": {"content": [{"type": "text", "text": text}], "isError": is_error},
    }


class FlattenTest(unittest.TestCase):
    def test_nested_and_dollar_keys(self):
        doc = {
            "$type": "color",
            "ink": {"$value": "#000"},
            "brand": {"$type": "color", "strong": {"$value": "#111"}},
        }
        self.assertEqual(
            tokens_sync.flatten(doc),
            [("ink", {"$value": "#000"}), ("brand.strong", {"$value": "#111"})],
        )


class ToSpecsTest(unittest.TestCase):
    def test_real_tokens_file(self):
        doc = json.loads(TOKENS_FILE.read_text())
        specs = tokens_sync.to_specs(doc)
        self.assertEqual(len(specs), 18)
        by_name = {spec["name"]: spec for spec in specs}
        self.assertEqual(by_name["ink"], {"type": "color", "name": "ink", "value": "#0F172A"})
        self.assertEqual(by_name["space.4"]["value"], "4")
        self.assertEqual(by_name["radius.8"]["type"], "borderRadius")
        self.assertEqual(by_name["fs.body"]["value"], "16")

    def test_round_trip_through_to_dtcg(self):
        specs = tokens_sync.to_specs(json.loads(TOKENS_FILE.read_text()))
        doc, skipped = tokens_sync.to_dtcg(specs)
        self.assertEqual(skipped, [])
        self.assertEqual(tokens_sync.to_specs(doc), specs)

    def test_duplicate_name_across_groups_is_rejected(self):
        doc = {
            "color": {"space": {"4": {"$value": "#FFFFFF"}}},
            "spacing": {"4": {"$value": "4px"}},
        }
        with self.assertRaises(ValueError) as caught:
            tokens_sync.to_specs(doc)
        self.assertIn("'space.4'", str(caught.exception))
        self.assertIn("color.space.4", str(caught.exception))

    def test_units(self):
        def spacings(value):
            return tokens_sync.to_specs({"spacing": {"md": {"$value": value}}})[0]["value"]

        self.assertEqual(spacings("16px"), "16")
        self.assertEqual(spacings("1.5px"), "1.5")
        self.assertEqual(spacings("16"), "16")
        self.assertEqual(spacings(16), "16")
        for bad in ("1.5rem", "{space.4}px", "16pt", "px", "", True):
            with self.subTest(value=bad), self.assertRaises(ValueError):
                spacings(bad)

    def test_rem_hint(self):
        with self.assertRaises(ValueError) as caught:
            tokens_sync.to_specs({"spacing": {"md": {"$value": "1.5rem"}}})
        self.assertIn("rem is not supported", str(caught.exception))

    def test_colour_must_be_a_string(self):
        with self.assertRaises(ValueError) as caught:
            tokens_sync.to_specs({"color": {"ink": {"$value": {"hex": "#0F172A"}}}})
        self.assertIn("colour must be a non-empty string", str(caught.exception))


class ToDtcgTest(unittest.TestCase):
    def test_unknown_types_and_prefixes_are_skipped(self):
        tokens = [
            {"type": "color", "name": "ink", "value": "#0F172A"},
            {"type": "rotation", "name": "spin", "value": "45"},
            {"type": "spacing", "name": "space.4", "value": "4"},
            {"type": "spacing", "name": "loose", "value": "5"},
        ]
        doc, skipped = tokens_sync.to_dtcg(tokens)
        self.assertEqual(skipped, ["spin", "loose"])
        self.assertEqual(len(skipped), 2)
        self.assertEqual(set(doc), {"color", "spacing"})
        self.assertEqual(doc["color"]["$type"], "color")
        self.assertEqual(doc["color"]["ink"], {"$value": "#0F172A"})
        self.assertEqual(doc["spacing"]["$type"], "dimension")
        self.assertEqual(doc["spacing"]["4"], {"$value": "4px"})


class PayloadTest(unittest.TestCase):
    def test_double_encoded_result(self):
        text = json.dumps({"result": json.dumps({"page": "Showcase"}), "log": ""})
        self.assertEqual(penpot_exec.payload(content_result(text)), {"page": "Showcase"})

    def test_object_result(self):
        self.assertEqual(penpot_exec.payload(content_result('{"loaded": "1.1.0"}')), {"loaded": "1.1.0"})

    def test_empty_content(self):
        self.assertIsNone(penpot_exec.payload({"result": {"content": []}}))
        self.assertIsNone(penpot_exec.payload({"result": {}}))

    def test_plain_text_error_raises(self):
        with self.assertRaises(penpot_exec.McpError) as caught:
            penpot_exec.payload(content_result("Tool execution failed: ReferenceError: storage is not defined"))
        self.assertIn("storage is not defined", str(caught.exception))

    def test_is_error_raises(self):
        with self.assertRaises(penpot_exec.McpError) as caught:
            penpot_exec.payload(content_result("No Penpot instance connected for user token.", is_error=True))
        self.assertIn("No Penpot instance connected", str(caught.exception))

    def test_jsonrpc_error_raises(self):
        with self.assertRaises(penpot_exec.McpError):
            penpot_exec.payload({"jsonrpc": "2.0", "id": 2, "error": {"code": -32603}})

    def test_plain_text_is_returned(self):
        self.assertEqual(penpot_exec.payload(content_result("ok")), "ok")


class ParseSseTest(unittest.TestCase):
    def test_with_space(self):
        raw = 'event: message\ndata: {"jsonrpc":"2.0","id":2,"result":{"ok":true}}\n\n'
        self.assertEqual(penpot_exec.parse_sse(raw, 2), {"jsonrpc": "2.0", "id": 2, "result": {"ok": True}})

    def test_without_space(self):
        raw = 'data:{"jsonrpc":"2.0","id":2,"result":{"ok":true}}\n\n'
        self.assertEqual(penpot_exec.parse_sse(raw, 2)["result"], {"ok": True})

    def test_multi_line_data(self):
        raw = 'data: {"jsonrpc":"2.0",\ndata: "id":2,\ndata: "result":{"a":1}}\n\n'
        self.assertEqual(penpot_exec.parse_sse(raw, 2)["result"], {"a": 1})

    def test_notification_before_result(self):
        raw = (
            'event: message\ndata: {"jsonrpc":"2.0","method":"notifications/progress","params":{}}\n\n'
            'event: message\ndata: {"jsonrpc":"2.0","id":2,"result":{"ok":true}}\n\n'
        )
        self.assertEqual(penpot_exec.parse_sse(raw, 2)["id"], 2)
        self.assertEqual(penpot_exec.parse_sse(raw, 2)["result"], {"ok": True})

    def test_plain_json_body(self):
        self.assertEqual(penpot_exec.parse_sse('{"jsonrpc":"2.0","id":2,"result":{}}', 2)["id"], 2)

    def test_empty_body_raises_mcp_error(self):
        with self.assertRaises(penpot_exec.McpError):
            penpot_exec.parse_sse("   ", 2)

    def test_missing_id_raises_mcp_error(self):
        raw = 'data: {"jsonrpc":"2.0","method":"notifications/progress"}\n\n'
        with self.assertRaises(penpot_exec.McpError):
            penpot_exec.parse_sse(raw, 2)


class ExitCodeTest(unittest.TestCase):
    def test_fail_defaults_to_environment_exit(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            penpot_exec.fail("boom")
        self.assertEqual(caught.exception.code, 2)

    def test_fail_keeps_finding_exit(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            penpot_exec.fail("drift", code=1)
        self.assertEqual(caught.exception.code, 1)

    def test_empty_code_is_rejected_before_any_request(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            penpot_exec.main(["--code", ""])
        self.assertEqual(caught.exception.code, 2)


class CompareTest(unittest.TestCase):
    SPECS = [{"type": "color", "name": "ink", "value": "#0F172A"}, {"type": "spacing", "name": "space.4", "value": "4"}]

    def test_colours_compare_case_insensitively(self):
        drift, extras = tokens_sync.compare(
            self.SPECS,
            {"ink": {"type": "color", "value": "#0f172a"}, "space.4": {"type": "spacing", "value": "4"}},
        )
        self.assertEqual((drift, extras), ([], []))

    def test_type_mismatch_is_drift(self):
        drift, _ = tokens_sync.compare(
            self.SPECS,
            {"ink": {"type": "color", "value": "#0F172A"}, "space.4": {"type": "borderRadius", "value": "4"}},
        )
        self.assertEqual(len(drift), 1)
        self.assertIn("type     space.4", drift[0])

    def test_value_and_missing_drift(self):
        drift, extras = tokens_sync.compare(self.SPECS, {"ink": {"type": "color", "value": "#000000"}})
        self.assertEqual([line.split()[0] for line in drift], ["differs", "missing"])
        self.assertEqual(extras, [])

    def test_extras_are_reported_separately(self):
        extra = {"type": "color", "name": "legacy", "value": "#FF0000"}
        drift, extras = tokens_sync.compare(
            self.SPECS,
            {
                "ink": {"type": "color", "value": "#0F172A"},
                "space.4": {"type": "spacing", "value": "4"},
                "legacy": extra,
            },
        )
        self.assertEqual(drift, [])
        self.assertEqual(len(extras), 1)
        self.assertIn("extra    legacy", extras[0])

    def test_write_atomic_keeps_mode_and_timestamped_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = pathlib.Path(tmp)
            target = directory / "tokens.json"
            target.write_text('{"old": 1}\n')
            os.chmod(target, 0o644)

            tokens_sync.write_atomic(target, '{"new": 2}\n')
            self.assertEqual(target.read_text(), '{"new": 2}\n')
            self.assertEqual(target.stat().st_mode & 0o777, 0o644)
            backups = sorted(directory.glob("tokens.json.*.bak"))
            self.assertEqual([b.read_text() for b in backups], ['{"old": 1}\n'])

            tokens_sync.write_atomic(target, '{"new": 3}\n')
            self.assertEqual(len(list(directory.glob("tokens.json.*.bak"))), 2)
            self.assertEqual([p for p in directory.iterdir() if p.name.endswith(".tmp")], [])


class CoverageTest(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(design_qa.coverage_counts("6/56"), (6, 56))
        self.assertEqual(design_qa.coverage_counts(""), (0, 0))
        self.assertEqual(design_qa.coverage_counts("nonsense"), (0, 0))

    def test_percent(self):
        self.assertEqual(design_qa.coverage_percent("6/56"), 11)
        self.assertEqual(design_qa.coverage_percent("56/56"), 100)
        self.assertEqual(design_qa.coverage_percent("0/0"), 100)

    def test_duplicate_set_names(self):
        self.assertEqual(
            design_qa.duplicate_set_names([{"name": "core"}, {"name": "core"}, {"name": "brand"}]),
            ["core"],
        )
        self.assertEqual(design_qa.duplicate_set_names([{"name": "core"}, {"name": "brand"}]), [])


class LintBridgeTest(unittest.TestCase):
    def test_high_only(self):
        doc = {"page": "Kongre", "findings": [
            {"board": "07-program", "severity": "high", "finding": "text x enters sibling"},
            {"board": "07-program", "severity": "medium", "finding": "inline pair"},
        ]}
        high = design_qa.lint_high_findings(doc)
        self.assertEqual(len(high), 1)
        self.assertIn("enters sibling", high[0]["finding"])

    def test_bad_shape_is_empty(self):
        self.assertEqual(design_qa.lint_high_findings(None), [])
        self.assertEqual(design_qa.lint_high_findings({"page": "Kongre"}), [])

    def test_an_invalid_lint_document_stops_the_qa_verdict(self):
        """lint `valid:false` means the page was never measured; QA must not pass it."""
        report = {"page": "Mobil", "shapes": 3, "boards": 1, "texts": 1,
                  "tokenSets": [{"name": "ihkd", "tokens": 4, "active": True}],
                  "components": [], "unnamed": 0, "flows": [{"name": "f"}],
                  "interactiveShapes": 1,
                  "tokenCoverage": {"fills": "2/2", "textSizes": "1/1", "renderMismatches": 0,
                                    "hardColors": []}}
        with tempfile.TemporaryDirectory() as tmp:
            lint = pathlib.Path(tmp) / "lint.json"
            lint.write_text(json.dumps({"page": "Mobil", "valid": False, "findings": []}))
            with mock.patch.object(design_qa, "load_url", lambda: "u"), \
                    mock.patch.object(design_qa, "ensure_helpers", lambda *a, **k: "1.5.0"), \
                    mock.patch.object(design_qa, "audit", lambda url, page: report), \
                    contextlib.redirect_stderr(io.StringIO()) as err:
                with self.assertRaises(SystemExit) as ctx:
                    design_qa.main(["--page", "Mobil", "--lint-json", str(lint)])
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("page not active: textBounds unavailable", err.getvalue())


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


def _page_board(board_id="pg"):
    return _node(id=board_id, name="page", type="board", parentId=None,
                 x=0, y=0, w=1440, h=2000)


def _panel(board_id="panel", x=120, y=500, w=1200, h=200, fill="#FFFFFF", stroke=True):
    return _node(id=board_id, name="panel", type="board", parentId="pg",
                 x=x, y=y, w=w, h=h, fill=fill, stroke=stroke)


def _text(node_id="t", parent="panel", x=120, y=540, text="Panel label here", inkX=None):
    return _node(id=node_id, name="label " + node_id, type="text", parentId=parent,
                 parent="panel", x=x, y=y, w=300, h=19, fill="#0E1318",
                 fontSize=16, lineHeight="1.5", text=text,
                 inkX=x if inkX is None else inkX, inkY=y, inkW=120, inkH=17)


def _collision_findings(nodes):
    return [f for f in design_lint.lint(nodes, dict(design_lint.DEFAULTS))
            if "collides with text" in f["finding"]]


class TextCollisionTest(unittest.TestCase):
    def test_flags_overlapping_inks(self):
        nodes = [_page_board(),
                 _text(node_id="a", parent="pg", x=120, y=540),
                 _text(node_id="b", parent="pg", x=200, y=540)]
        findings = _collision_findings(nodes)
        self.assertEqual(len(findings), 1)
        self.assertIn("collides", findings[0]["finding"])

    def test_ok_stacked_pair_with_gap(self):
        nodes = [_page_board(),
                 _text(node_id="a", parent="pg", x=120, y=540),
                 _text(node_id="b", parent="pg", x=120, y=600)]
        self.assertEqual(_collision_findings(nodes), [])

    def test_ok_inline_adjacent_pair(self):
        nodes = [_page_board(),
                 _text(node_id="a", parent="pg", x=120, y=540),
                 _text(node_id="b", parent="pg", x=240, y=540)]
        self.assertEqual(_collision_findings(nodes), [])

    def test_ok_unmeasured_ink_is_skipped(self):
        a = _text(node_id="a", parent="pg", x=120, y=540)
        b = _node(id="b", name="label b", type="text", parentId="pg",
                  parent="pg", x=150, y=540, w=300, h=19, fill="#0E1318",
                  fontSize=16, lineHeight="1.5", text="unlaid",
                  inkX=None, inkY=None, inkW=None, inkH=None)
        nodes = [_page_board(), a, b]
        self.assertEqual(_collision_findings(nodes), [])


def _padding_findings(nodes):
    return [f for f in design_lint.lint(nodes, dict(design_lint.DEFAULTS))
            if "panel padding" in f["finding"]]


class CardPaddingTest(unittest.TestCase):
    def test_flags_flush_text_in_stroked_panel(self):
        nodes = [_page_board(), _panel(), _text(x=120, inkX=120)]
        findings = _padding_findings(nodes)
        self.assertEqual(len(findings), 1)
        self.assertIn("0px", findings[0]["finding"])

    def test_flags_flush_text_in_surface_panel_without_stroke(self):
        nodes = [_page_board(), _panel(stroke=False, fill="#E8EBED"), _text(x=130, inkX=130)]
        findings = _padding_findings(nodes)
        self.assertEqual(len(findings), 1)
        self.assertIn("10px", findings[0]["finding"])

    def test_ok_with_enough_padding(self):
        nodes = [_page_board(), _panel(), _text(x=144, inkX=144)]
        self.assertEqual(_padding_findings(nodes), [])

    def test_ok_full_bleed_board_is_edge_to_edge_by_design(self):
        nodes = [_page_board(), _panel(board_id="band", x=0, y=500), _text(parent="band", x=0, inkX=0)]
        self.assertEqual(_padding_findings(nodes), [])

    def test_ok_single_label_chip_is_not_a_panel(self):
        nodes = [_page_board(), _panel(board_id="chip", x=360, y=500, w=92, h=32),
                 _text(node_id="c", parent="chip", x=372, inkX=372, text="Chip")]
        self.assertEqual(_padding_findings(nodes), [])

    def test_ok_label_on_nested_pill(self):
        pill = _node(id="pill", name="pill", type="board", parentId="panel",
                     parent="panel", x=120, y=540, w=120, h=36, fill="#FFFFFF", stroke=True)
        label = _text(node_id="p", parent="panel", x=120, inkX=122, y=548, text="Pill")
        label.update({"inkY": 548, "inkW": 60, "inkH": 17})
        nodes = [_page_board(), _panel(), pill, label]
        self.assertEqual(_padding_findings(nodes), [])

    def test_unlaid_text_falls_back_to_box_edge(self):
        bad = _text(node_id="u", parent="panel", x=120, y=560, text="Unlaid")
        bad.update({"inkX": 0, "inkY": 0, "inkW": 0, "inkH": 0})
        findings = _padding_findings([_page_board(), _panel(), bad])
        self.assertEqual(len(findings), 1)
        self.assertIn("0px", findings[0]["finding"])


def _fit_findings(nodes):
    return [f for f in design_lint.lint(nodes, dict(design_lint.DEFAULTS))
            if "overflows its container" in f["finding"]
            or "enters sibling container" in f["finding"]
            or "crosses rule" in f["finding"]
            or f["finding"].startswith("bar ")]

def _ink_text(node_id="t", parent="pg", x=140, y=520, w=200, h=40,
              inkX=None, inkY=None, inkW=120, inkH=20):
    return _node(id=node_id, name="fit " + node_id, type="text", parentId=parent,
                 parent=parent, x=x, y=y, w=w, h=h, fill="#0E1318",
                 fontSize=16, lineHeight="1.5", text="Fit check copy",
                 inkX=x if inkX is None else inkX, inkY=y if inkY is None else inkY,
                 inkW=inkW, inkH=inkH)


class FitOverflowTest(unittest.TestCase):
    def test_flags_ink_leaving_its_card(self):
        card = _node(id="card", name="card", type="board", parentId="pg",
                     parent="pg", x=120, y=500, w=400, h=120, fill="#FFFFFF", stroke=True)
        text = _ink_text(parent="card", inkW=400)  # ink runs to x=540, card ends at 520
        findings = _fit_findings([_page_board(), card, text])
        self.assertEqual(len(findings), 1)
        self.assertIn("overflows its container card", findings[0]["finding"])
        self.assertIn("right +20px", findings[0]["finding"])

    def test_ok_ink_inside_its_card(self):
        card = _node(id="card", name="card", type="board", parentId="pg",
                     parent="pg", x=120, y=500, w=400, h=120, fill="#FFFFFF", stroke=True)
        self.assertEqual(_fit_findings([_page_board(), card, _ink_text(parent="card")]), [])

    def test_ok_board_level_text_has_no_card_to_overflow(self):
        self.assertEqual(_fit_findings([_page_board(), _ink_text()]), [])


class FitBoundaryTest(unittest.TestCase):
    def _zebra(self):
        return _node(id="zebra", name="row zebra 1", type="rectangle", parentId="pg",
                     parent="pg", x=120, y=600, w=1200, h=92, fill="#F4F5F6")

    def test_flags_ink_entering_next_row_band(self):
        findings = _fit_findings([_page_board(), self._zebra(),
                                  _ink_text(inkY=580, inkH=40)])  # 580-620 straddles y=600
        self.assertEqual(len(findings), 1)
        self.assertIn("enters sibling container row zebra 1", findings[0]["finding"])

    def test_ok_ink_resting_on_its_band(self):
        self.assertEqual(_fit_findings([_page_board(), self._zebra(),
                                        _ink_text(inkY=610, inkH=40)]), [])

    def test_flags_ink_crossing_a_hairline(self):
        rule = _node(id="rule", name="row rule 0", type="rectangle", parentId="pg",
                     parent="pg", x=120, y=700, w=1200, h=1, fill="#E8EBED")
        findings = _fit_findings([_page_board(), rule, _ink_text(inkY=690, inkH=20)])
        self.assertEqual(len(findings), 1)
        self.assertIn("crosses rule row rule 0", findings[0]["finding"])

    def test_ok_ink_clear_of_the_hairline(self):
        rule = _node(id="rule", name="row rule 0", type="rectangle", parentId="pg",
                     parent="pg", x=120, y=700, w=1200, h=1, fill="#E8EBED")
        self.assertEqual(_fit_findings([_page_board(), rule, _ink_text(inkY=660, inkH=20)]), [])


class FitColumnBandTest(unittest.TestCase):
    """A row rule's length is the column band its texts must stay inside."""

    def _band(self, w=560, name="group rule 0"):
        return _node(id="rule", name=name, type="rectangle", parentId="pg",
                     parent="pg", x=120, y=700, w=w, h=1, fill="#E8EBED")

    def _band_findings(self, nodes):
        return [f for f in design_lint.lint(nodes, dict(design_lint.DEFAULTS))
                if "column band" in f["finding"]]

    def test_flags_title_running_past_the_column_band(self):
        findings = self._band_findings([_page_board(), self._band(),
                                        _ink_text(x=140, y=640, inkW=640)])  # ink 140-780
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "high")
        self.assertIn("100px past its 560px column band", findings[0]["finding"])

    def test_title_inside_the_band_stays_clean(self):
        self.assertEqual(self._band_findings([_page_board(), self._band(),
                                              _ink_text(x=140, y=640, inkW=500)]), [])

    def test_link_underline_is_not_a_column_band(self):
        # link() draws "<name> under" 1px; it marks the text span, not a column
        self.assertEqual(self._band_findings([_page_board(), self._band(w=117, name="cta under"),
                                              _ink_text(x=140, y=640, inkW=1100)]), [])

    def test_a_rule_far_below_does_not_bind_the_text(self):
        rule = self._band()
        rule["y"] = 900
        self.assertEqual(self._band_findings([_page_board(), rule,
                                              _ink_text(x=140, y=640, inkW=640)]), [])


class FitBarTest(unittest.TestCase):
    def _bar(self, fill="#E0364B"):
        return _node(id="bar", name="sess bar 0", type="rectangle", parentId="pg",
                     parent="pg", x=240, y=500, w=2, h=160, fill=fill)

    def test_flags_bar_taller_than_its_column(self):
        nodes = [_page_board(), self._bar(),
                 _ink_text(node_id="a", x=256, y=500, inkX=256, inkY=500, inkH=20),
                 _ink_text(node_id="b", x=256, y=530, inkX=256, inkY=530, inkH=36)]
        findings = [f for f in design_lint.lint(nodes, dict(design_lint.DEFAULTS))
                    if f["finding"].startswith("bar ")]
        self.assertEqual(len(findings), 1)
        self.assertIn("Δ94px", findings[0]["finding"])

    def test_ok_matching_bar(self):
        bar = self._bar()
        bar["h"] = 66
        nodes = [_page_board(), bar,
                 _ink_text(node_id="a", x=256, y=500, inkX=256, inkY=500, inkH=20),
                 _ink_text(node_id="b", x=256, y=530, inkX=256, inkY=530, inkH=36)]
        self.assertEqual([f for f in design_lint.lint(nodes, dict(design_lint.DEFAULTS))
                          if f["finding"].startswith("bar ")], [])

    def test_ok_unsaturated_divider_is_exempt(self):
        nodes = [_page_board(), self._bar(fill="#E8EBED"),
                 _ink_text(node_id="a", x=256, y=500, inkX=256, inkY=500, inkH=20)]
        self.assertEqual([f for f in design_lint.lint(nodes, dict(design_lint.DEFAULTS))
                          if f["finding"].startswith("bar ")], [])


class CropBoardTest(unittest.TestCase):
    def _png(self, tmp, w=300, h=200):
        from PIL import Image as PILImage
        path = pathlib.Path(tmp) / "shot.png"
        PILImage.new("RGB", (w, h), "white").save(path)
        return path

    def test_tiles_cover_the_image(self):
        import crop_board
        boxes = crop_board.tile_boxes(300, 200, 200, 100, 0.0)
        self.assertEqual(len(boxes), 4)
        self.assertIn((0, 0, 200, 100), boxes)
        self.assertIn((100, 100, 200, 100), boxes)
        for x, y, w, h in boxes:
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(x + w, 300)
            self.assertLessEqual(y + h, 200)

    def test_overlap_adds_tiles(self):
        import crop_board
        plain = crop_board.tile_boxes(1000, 1000, 600, 600, 0.0)
        overlapped = crop_board.tile_boxes(1000, 1000, 600, 600, 0.5)
        self.assertEqual(len(plain), 4)
        self.assertGreater(len(overlapped), len(plain))

    def test_pick_regions(self):
        import crop_board
        nodes = [_page_board(),
                 _ink_text(node_id="big", y=100, inkH=40),
                 _node(id="cta1", name="masthead cta label", type="text", parentId="pg",
                       parent="pg", x=1100, y=30, w=120, h=30, fill="#FFF",
                       fontSize=16, lineHeight="1.5", text="Join",
                       inkX=1100, inkY=30, inkW=60, inkH=20)]
        regions = crop_board.pick_regions(nodes)
        slugs = [r["slug"] for r in regions]
        self.assertIn("smallest-text", slugs)
        self.assertIn("densest", slugs)
        self.assertIn("primary-action", slugs)

    def test_attest_requires_every_tile(self):
        import crop_board
        with tempfile.TemporaryDirectory() as tmp:
            manifest = pathlib.Path(tmp) / "manifest.json"
            manifest.write_text(json.dumps({
                "tiles": [{"file": "tile-01.png", "reviewed": True, "note": "margins even"},
                          {"file": "tile-02.png", "reviewed": False, "note": ""}],
                "regions": []}))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(crop_board.attest_manifest(manifest), 1)
            self.assertIn("tile-02.png", buf.getvalue())
            manifest.write_text(json.dumps({
                "tiles": [{"file": "tile-01.png", "reviewed": True, "note": "ok"},
                          {"file": "tile-02.png", "reviewed": True, "note": "ok"}],
                "regions": []}))
            with contextlib.redirect_stdout(buf):
                self.assertEqual(crop_board.attest_manifest(manifest), 0)

    def test_crop_writes_tiles(self):
        import crop_board
        with tempfile.TemporaryDirectory() as tmp:
            src = self._png(tmp)
            out = pathlib.Path(tmp) / "tiles"
            out.mkdir()
            cropper = crop_board.Cropper(src)
            self.assertEqual(cropper.size, (300, 200))
            cropper.crop((0, 0, 200, 100), out / "tile-01.png")
            self.assertTrue((out / "tile-01.png").stat().st_size > 0)


class UxGateTest(unittest.TestCase):
    def _screen_nodes(self):
        board = _node(id="b1", name="01-home", type="board", parentId=None,
                      x=0, y=0, w=1440, h=2000)
        cta = _node(id="c1", name="hero cta", type="board", parentId="b1",
                    parent="01-home", x=120, y=392, w=200, h=48, fill="#E0364B")
        title = _node(id="t1", name="hero title", type="text", parentId="b1",
                      parent="01-home", x=120, y=188, w=700, h=56, fill="#0E1318",
                      fontSize=44, lineHeight="1.1", text="Hero",
                      inkX=120, inkY=188, inkW=400, inkH=50)
        return [board, cta, title]

    def _screen_spec(self, **over):
        spec = {"project": "demo", "defaults": {"accentMaxRatio": 0.3, "viewportH": 900},
                "screens": [{"board": "01-home", "page": "Web",
                             "task": "Join the program.",
                             "primaryCta": "hero cta",
                             "story": {"hook": "h", "proof": "p", "path": "pa", "action": "a"},
                             "states": [],
                             "mobile": "n/a: mobile ships in M4",
                             "firstViewport": ["hero title", "hero cta"],
                             "claims": []}]}
        spec["screens"][0].update(over)
        return spec

    def test_clean_screen_passes(self):
        import ux_gate
        self.assertEqual(ux_gate.evaluate(self._screen_spec(), {"Web": self._screen_nodes()}), [])

    def test_missing_cta_and_double_primary_and_fold_and_claim(self):
        import ux_gate
        nodes = self._screen_nodes()
        nodes.append(_node(id="c2", name="footer primary", type="board", parentId="b1",
                           parent="01-home", x=120, y=1800, w=200, h=48, fill="#E0364B"))
        low = _node(id="t2", name="late note", type="text", parentId="b1",
                    parent="01-home", x=120, y=1200, w=300, h=20, fill="#0E1318",
                    fontSize=16, lineHeight="1.5", text="Late",
                    inkX=120, inkY=1200, inkW=100, inkH=17)
        nodes.append(low)
        spec = self._screen_spec(primaryCta="hero cta 2",
                                 firstViewport=["hero title", "late note"],
                                 mobile="someday",
                                 states=[{"state": "empty", "board": "01-empty"}],
                                 claims=[{"pattern": "sess title", "count": 96, "label": "sessions"}])
        findings = ux_gate.evaluate(spec, {"Web": nodes})
        texts = [f["finding"] for f in findings]
        self.assertTrue(any("primaryCta" in t for t in texts), texts)
        self.assertTrue(any("2 primary actions" in t for t in texts), texts)
        self.assertTrue(any("below the fold" in t for t in texts), texts)
        self.assertTrue(any("neither an existing board" in t for t in texts), texts)
        self.assertTrue(any("state 'empty'" in t for t in texts), texts)
        self.assertTrue(any("matched 0, spec says 96" in t for t in texts), texts)

    def test_accent_ceiling(self):
        import ux_gate
        nodes = self._screen_nodes()
        nodes.append(_node(id="band", name="hero band", type="rectangle", parentId="b1",
                           parent="01-home", x=0, y=0, w=1440, h=400, fill="#E0364B"))
        findings = ux_gate.evaluate(self._screen_spec(), {"Web": nodes})
        self.assertTrue(any("accent fills" in f["finding"] for f in findings), findings)


class OverlapBlindSpotTest(unittest.TestCase):
    def _side(self):
        return _node(id="side", name="side", type="board", parentId="pg",
                     parent="pg", x=944, y=400, w=376, h=500, fill="#FFFFFF", stroke=True)

    def _button(self):
        return _node(id="cta", name="s cta", type="board", parentId="side",
                     parent="side", x=992, y=672, w=296, h=48, fill="#E0364B")

    def test_text_inside_sibling_button_is_high(self):
        # DAHİL/Devam-et sınıfı: butonun kendi etiketine ek olarak, ebeveyni
        # olmayan doygun bir kardeş kutunun tamamen içinde kalan metinler.
        lab = _node(id="l", name="s cta / label", type="text", parentId="cta",
                    parent="s cta", x=992, y=688, w=120, h=23, fill="#FFF",
                    fontSize=16, lineHeight="1.5", text="Devam et",
                    inkX=1106, inkY=689, inkW=66.9, inkH=19.5)
        inc = _ink_text(node_id="i0", parent="side", x=992, y=696, w=81, h=19,
                        inkX=992, inkY=698, inkW=78.6, inkH=16.5)
        findings = design_lint.lint([_page_board(), self._side(), self._button(), lab, inc],
                                    dict(design_lint.DEFAULTS))
        self.assertTrue(any("sibling control" in f["finding"] and f["severity"] == "high"
                            for f in findings),
                        [f["finding"] for f in findings])

    def test_text_inside_muted_band_stays_clean(self):
        band = _node(id="zebra", name="row zebra 1", type="rectangle", parentId="pg",
                     parent="pg", x=120, y=600, w=1200, h=92, fill="#F4F5F6")
        findings = design_lint.lint([_page_board(), band, _ink_text(inkY=610, inkH=40)],
                                    dict(design_lint.DEFAULTS))
        self.assertEqual([f for f in findings if "sibling control" in f["finding"] or
                          "overflows its container" in f["finding"]], [])

    def test_lone_label_on_active_pill_stays_clean(self):
        pill = _node(id="pill", name="sidebar active", type="rectangle", parentId="pg",
                     parent="pg", x=0, y=186, w=264, h=36, fill="#E0364B")
        label = _ink_text(node_id="nav", parent="pg", x=28, y=192, w=120, h=22,
                          inkX=28, inkY=193, inkW=80, inkH=17)
        findings = design_lint.lint([_page_board(), pill, label], dict(design_lint.DEFAULTS))
        self.assertEqual([f for f in findings if "sibling control" in f["finding"] or
                          "paints over shape" in f["finding"]], [])

    def test_touching_siblings_flag_medium(self):
        panel = _node(id="panel", name="side", type="board", parentId="pg",
                      parent="pg", x=960, y=412, w=360, h=439, fill="#F4F5F6")
        photo = _node(id="photo", name="img-lab", type="rectangle", parentId="pg",
                      parent="pg", x=992, y=851, w=296, h=160, fill="#F4F5F6", img=True)
        findings = design_lint.lint([_page_board(), panel, photo], dict(design_lint.DEFAULTS))
        self.assertTrue(any("touch" in f["finding"] and f["severity"] == "medium"
                            for f in findings),
                        [f["finding"] for f in findings])

    def test_unlaid_box_is_high(self):
        bad = _node(id="u", name="nav X", type="text", parentId="pg",
                    parent="pg", x=120, y=32, w=1, h=1, fill="#0E1318",
                    fontSize=16, lineHeight="1.5", text="Missing",
                    inkX=None, inkY=None, inkW=None, inkH=None)
        findings = design_lint.lint([_page_board(), bad], dict(design_lint.DEFAULTS))
        self.assertTrue(any("unlaid-out" in f["finding"] and f["severity"] == "high"
                            for f in findings),
                        [f["finding"] for f in findings])

    def test_dead_space_flags_hollow_card(self):
        card = _node(id="card", name="sess card 0", type="board", parentId="pg",
                     parent="pg", x=240, y=480, w=232, h=280, fill="#FFFFFF", stroke=True)
        title = _ink_text(node_id="t", parent="card", x=254, y=490, w=204, h=26,
                          inkX=254, inkY=492, inkW=150, inkH=20)
        meta = _ink_text(node_id="m", parent="card", x=254, y=524, w=204, h=40,
                         inkX=254, inkY=526, inkW=180, inkH=36)
        findings = design_lint.lint([_page_board(), card, title, meta],
                                    dict(design_lint.DEFAULTS))
        self.assertTrue(any("dead space" in f["finding"] and f["severity"] == "high"
                            for f in findings),
                        [f["finding"] for f in findings])

    def test_snug_card_stays_clean(self):
        card = _node(id="card", name="sess card 0", type="board", parentId="pg",
                     parent="pg", x=240, y=480, w=232, h=120, fill="#FFFFFF", stroke=True)
        title = _ink_text(node_id="t", parent="card", x=254, y=490, w=204, h=26,
                          inkX=254, inkY=492, inkW=150, inkH=20)
        meta = _ink_text(node_id="m", parent="card", x=254, y=524, w=204, h=60,
                         inkX=254, inkY=526, inkW=180, inkH=56)
        findings = design_lint.lint([_page_board(), card, title, meta],
                                    dict(design_lint.DEFAULTS))
        self.assertEqual([f for f in findings if "dead space" in f["finding"]], [])

    def test_empty_corridor_flags_missing_row(self):
        head = _node(id="h", name="head", type="rectangle", parentId="pg",
                     parent="pg", x=0, y=0, w=1440, h=996, fill="#F4F5F6")
        top = _node(id="a", name="band", type="rectangle", parentId="pg",
                    parent="pg", x=240, y=1000, w=1080, h=48, fill="#FFFFFF")
        mid = _node(id="m", name="sess card 0", type="board", parentId="pg",
                    parent="pg", x=240, y=880, w=232, h=120, fill="#FFFFFF", stroke=True)
        bottom = _node(id="b", name="sess card 1", type="board", parentId="pg",
                       parent="pg", x=240, y=1240, w=232, h=120, fill="#FFFFFF", stroke=True)
        foot = _node(id="f", name="foot", type="rectangle", parentId="pg",
                     parent="pg", x=0, y=1360, w=1440, h=640, fill="#F4F5F6")
        findings = design_lint.lint([_page_board(), head, top, mid, bottom, foot], dict(design_lint.DEFAULTS))
        self.assertTrue(any("empty corridor" in f["finding"] and f["severity"] == "high"
                            for f in findings),
                        [f["finding"] for f in findings])

    def test_one_sided_air_stays_clean(self):
        head = _node(id="h", name="head", type="rectangle", parentId="pg",
                     parent="pg", x=0, y=0, w=1440, h=996, fill="#F4F5F6")
        top = _node(id="a", name="band", type="rectangle", parentId="pg",
                    parent="pg", x=240, y=1000, w=1080, h=48, fill="#FFFFFF")
        foot = _node(id="f", name="foot", type="rectangle", parentId="pg",
                     parent="pg", x=0, y=1200, w=1440, h=800, fill="#F4F5F6")
        findings = design_lint.lint([_page_board(), head, top, foot], dict(design_lint.DEFAULTS))
        self.assertEqual([f for f in findings if "empty corridor" in f["finding"]], [])

    def test_intra_card_gap_flags_pushed_meta(self):
        card = _node(id="card", name="sess card 0", type="board", parentId="pg",
                     parent="pg", x=240, y=480, w=232, h=140, fill="#FFFFFF", stroke=True)
        title = _ink_text(node_id="t", parent="card", x=254, y=490, w=204, h=26,
                          inkX=254, inkY=492, inkW=150, inkH=20)
        meta = _ink_text(node_id="m", parent="card", x=254, y=570, w=204, h=40,
                         inkX=254, inkY=572, inkW=180, inkH=36)
        findings = design_lint.lint([_page_board(), card, title, meta],
                                    dict(design_lint.DEFAULTS))
        self.assertTrue(any("intra-card gap" in f["finding"] and f["severity"] == "medium"
                            for f in findings),
                        [f["finding"] for f in findings])

    def test_docked_footer_is_exempt(self):
        card = _node(id="card", name="sidebar", type="board", parentId="pg",
                     parent="pg", x=0, y=0, w=264, h=600, fill="#FFFFFF", stroke=True)
        nav = _ink_text(node_id="a", parent="card", x=28, y=100, w=200, h=22,
                        inkX=28, inkY=102, inkW=120, inkH=17)
        out = _ink_text(node_id="b", parent="card", x=28, y=556, w=200, h=22,
                        inkX=28, inkY=558, inkW=60, inkH=17)
        findings = design_lint.lint([_page_board(), card, nav, out],
                                    dict(design_lint.DEFAULTS))
        self.assertEqual([f for f in findings if "intra-card gap" in f["finding"]], [])

    def test_snug_stack_stays_clean(self):
        card = _node(id="card", name="sess card 0", type="board", parentId="pg",
                     parent="pg", x=240, y=480, w=232, h=140, fill="#FFFFFF", stroke=True)
        title = _ink_text(node_id="t", parent="card", x=254, y=490, w=204, h=26,
                          inkX=254, inkY=492, inkW=150, inkH=20)
        meta = _ink_text(node_id="m", parent="card", x=254, y=522, w=204, h=40,
                         inkX=254, inkY=524, inkW=180, inkH=36)
        findings = design_lint.lint([_page_board(), card, title, meta],
                                    dict(design_lint.DEFAULTS))
        self.assertEqual([f for f in findings if "intra-card gap" in f["finding"]], [])

    def test_photo_between_texts_breaks_the_chain(self):
        card = _node(id="card", name="side", type="board", parentId="pg",
                     parent="pg", x=960, y=412, w=360, h=500, fill="#F4F5F6", stroke=True)
        a = _ink_text(node_id="a", parent="card", x=992, y=700, w=200, h=20,
                      inkX=992, inkY=702, inkW=120, inkH=16)
        photo = _node(id="p", name="img", type="rectangle", parentId="card",
                      parent="card", x=992, y=730, w=200, h=100, fill=None, img=True)
        b = _ink_text(node_id="b", parent="card", x=992, y=850, w=200, h=20,
                      inkX=992, inkY=852, inkW=120, inkH=16)
        findings = design_lint.lint([_page_board(), card, a, photo, b],
                                    dict(design_lint.DEFAULTS))
        self.assertEqual([f for f in findings if "intra-card gap" in f["finding"]], [])

    def test_bridged_gap_stays_clean(self):
        head = _node(id="h", name="head", type="rectangle", parentId="pg",
                     parent="pg", x=0, y=0, w=1440, h=996, fill="#F4F5F6")
        top = _node(id="a", name="band", type="rectangle", parentId="pg",
                    parent="pg", x=240, y=1000, w=1080, h=48, fill="#FFFFFF")
        band2 = _node(id="r", name="section band", type="rectangle", parentId="pg",
                     parent="pg", x=0, y=1100, w=1440, h=48, fill="#F4F5F6")
        bottom = _node(id="b", name="sess card 1", type="board", parentId="pg",
                       parent="pg", x=240, y=1240, w=232, h=120, fill="#FFFFFF", stroke=True)
        foot = _node(id="f", name="foot", type="rectangle", parentId="pg",
                     parent="pg", x=0, y=1360, w=1440, h=640, fill="#F4F5F6")
        findings = design_lint.lint([_page_board(), head, top, band2, bottom, foot], dict(design_lint.DEFAULTS))
        self.assertEqual([f for f in findings if "empty corridor" in f["finding"]], [])

    def test_gapped_siblings_stay_clean(self):
        panel = _node(id="panel", name="side", type="board", parentId="pg",
                      parent="pg", x=960, y=412, w=360, h=439, fill="#F4F5F6")
        photo = _node(id="photo", name="img-lab", type="rectangle", parentId="pg",
                      parent="pg", x=992, y=875, w=296, h=160, fill="#F4F5F6", img=True)
        findings = design_lint.lint([_page_board(), panel, photo], dict(design_lint.DEFAULTS))
        self.assertEqual([f for f in findings if "touch" in f["finding"]], [])

    def test_same_surface_touch_stays_clean(self):
        a = _node(id="a", name="band a", type="rectangle", parentId="pg",
                  parent="pg", x=0, y=0, w=1440, h=100, fill="#FFFFFF")
        b = _node(id="b", name="band b", type="rectangle", parentId="pg",
                  parent="pg", x=0, y=100, w=1440, h=100, fill="#FFFFFF")
        findings = design_lint.lint([_page_board(), a, b], dict(design_lint.DEFAULTS))
        self.assertEqual([f for f in findings if "touch" in f["finding"]], [])

    def test_cross_parent_text_overlap_still_flags(self):
        a = _ink_text(node_id="a", parent="pg", x=120, y=540, inkX=120, inkY=540)
        b = _ink_text(node_id="b", parent="side", x=200, y=540, inkX=200, inkY=540)
        side = _node(id="side", name="side", type="board", parentId="pg",
                     parent="pg", x=100, y=400, w=400, h=300, fill="#FFFFFF", stroke=True)
        findings = design_lint.lint([_page_board(), side, a, b], dict(design_lint.DEFAULTS))
        self.assertTrue(any("collides with text" in f["finding"] for f in findings))


class TopVoidTest(unittest.TestCase):
    def _report(self, first_y):
        board = _node(id="b", name="board", type="board", parentId=None,
                      x=0, y=400, w=1440, h=2000)
        rule = _node(id="r", name="masthead rule", parentId="b", parent="board",
                     x=0, y=484, w=1440, h=1, fill="#E8EBED")
        head = _node(id="h", name="ph label", type="text", parentId="b", parent="board",
                     x=120, y=400 + first_y, w=300, h=17, fill="#8F0F24",
                     fontSize=12, lineHeight="1.2", text="Label",
                     inkX=120, inkY=400 + first_y, inkW=120, inkH=14)
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "nodes.json"
            path.write_text(json.dumps([board, rule, head]))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = rhythm.main([str(path)])
        return code, buf.getvalue()

    def test_flags_large_void(self):
        code, out = self._report(236)
        self.assertEqual(code, 0)
        self.assertIn("TOP-VOID", out)
        self.assertIn("151px", out)

    def test_ok_small_void(self):
        code, out = self._report(156)
        self.assertEqual(code, 0)
        self.assertNotIn("TOP-VOID", out)
        self.assertIn("top-void ok", out)


class ExportRescueTest(unittest.TestCase):
    """The export must survive the MCP task limit by taking the exporter's render.

    Docker is mocked: `compose` is replaced, so these tests prove the decision
    logic (which file is accepted, what happens on mismatch or silence), not
    that this machine's compose file is right.
    """

    def setUp(self):
        import export_board
        self.eb = export_board
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.info = {"id": "s1", "name": "01-ana-sayfa", "width": 1440.0, "height": 4464.0}
        self.target = self.tmp / "01-ana-sayfa.png"
        self.listing: list[str] = []
        self.src = self.tmp / "render.png"
        self.calls: list[tuple] = []

    def _fake_compose(self):
        def run(*args):
            self.calls.append(args)
            if args and args[0] == "exec":
                return "".join(f"{name}\n" for name in self.listing)
            if args and args[0] == "cp":
                pathlib.Path(args[2]).write_bytes(self.src.read_bytes())
                return ""
            return ""
        return run

    def _write_png(self, w, h):
        from PIL import Image as PILImage
        PILImage.new("RGB", (w, h), "white").save(self.src)
        return self.src.read_bytes()

    def _timeout_result(self):
        return {"jsonrpc": "2.0", "id": 2, "result": {"content": [
            {"type": "text", "text": "Tool execution failed: Error: Task abc timed out after 120 seconds"}]}}

    def test_png_size_reads_the_header(self):
        self._write_png(1440, 4464)
        self.assertEqual(self.eb.png_size(self.src), (1440, 4464))
        not_png = self.tmp / "x.png"
        not_png.write_bytes(b"nope")
        with self.assertRaises(self.eb.McpError):
            self.eb.png_size(not_png)

    def test_bridge_result_is_used_when_it_arrives(self):
        data = self._write_png(1440, 4464)
        result = {"result": {"content": [{"type": "image", "data": base64.b64encode(data).decode()}]}}
        with mock.patch.object(self.eb, "call_tool", lambda *a, **k: result), \
                mock.patch.object(self.eb, "exporter_renders", lambda: []):
            note: list[str] = []
            self.eb.export_png("u", self.info, self.target, wait=1, poll=0.01, provenance=note)
        self.assertEqual(self.eb.png_size(self.target), (1440, 4464))
        self.assertTrue(note[0].startswith("bridge "), note)

    def test_task_timeout_is_recovered_from_the_exporter(self):
        self._write_png(1440, 4464)

        def fire(*_a, **_k):
            self.listing = ["penpot.resource.png.fresh"]  # lands after the export fires
            return self._timeout_result()

        with mock.patch.object(self.eb, "call_tool", fire), \
                mock.patch.object(self.eb, "exporter_renders", lambda: list(self.listing)), \
                mock.patch.object(self.eb, "compose", self._fake_compose()):
            note: list[str] = []
            self.eb.export_png("u", self.info, self.target, wait=2, poll=0.01, provenance=note)
        self.assertEqual(self.eb.png_size(self.target), (1440, 4464))
        self.assertIn("cp", [c[0] for c in self.calls])
        self.assertTrue(note[0].startswith("exporter penpot.resource.png.fresh "), note)

    def test_a_neighbouring_board_render_is_rejected(self):
        """Every board is 1440 wide, so only the height tells them apart."""
        self._write_png(1440, 2296)

        def fire(*_a, **_k):
            self.listing = ["penpot.resource.png.other"]
            return self._timeout_result()

        with mock.patch.object(self.eb, "call_tool", fire), \
                mock.patch.object(self.eb, "exporter_renders", lambda: list(self.listing)), \
                mock.patch.object(self.eb, "compose", self._fake_compose()):
            with self.assertRaises(self.eb.McpError) as ctx:
                self.eb.export_png("u", self.info, self.target, wait=0.2, poll=0.01)
        self.assertIn("1440x4464", str(ctx.exception))
        self.assertIn("timed out after 120 seconds", str(ctx.exception))
        self.assertFalse(self.target.exists(), "a wrong-sized render must not be written")

    def test_export_rescue_uses_the_same_verifier(self):
        """The entry point must not re-implement "newest file": same verify path."""
        import export_rescue
        self.assertIs(export_rescue.export_png, self.eb.export_png)
        self.assertIs(export_rescue.png_size, self.eb.png_size)

    def test_export_rescue_rejects_a_neighbour_render_end_to_end(self):
        import export_rescue

        out = self.tmp / "out"

        def execute(_url, _code):
            return content_result(json.dumps(self.info))

        def fire(*_a, **_k):
            self.listing = ["neighbour"]  # lands after the export fires
            return self._timeout_result()

        with mock.patch.object(export_rescue, "load_url", lambda: "u"), \
                mock.patch.object(export_rescue, "call_execute_code", execute), \
                mock.patch.object(self.eb, "call_tool", fire), \
                mock.patch.object(self.eb, "exporter_renders", lambda: list(self.listing)), \
                mock.patch.object(self.eb, "compose", self._fake_compose()):
            self._write_png(1440, 2296)
            with self.assertRaises(SystemExit) as ctx:
                export_rescue.main(["--board", "01-ana-sayfa", "--out", str(out),
                                    "--wait", "0.2", "--poll", "0.01"])
        self.assertEqual(ctx.exception.code, 2)
        self.assertFalse((out / "01-ana-sayfa.png").exists(),
                         "a neighbouring board's render must never be written")

    def test_export_rescue_writes_only_a_matching_render(self):
        import export_rescue

        out = self.tmp / "out"

        def execute(_url, _code):
            return content_result(json.dumps(self.info))

        def fire(*_a, **_k):
            self.listing = ["fresh"]  # lands after the export fires
            return self._timeout_result()

        with mock.patch.object(export_rescue, "load_url", lambda: "u"), \
                mock.patch.object(export_rescue, "call_execute_code", execute), \
                mock.patch.object(self.eb, "call_tool", fire), \
                mock.patch.object(self.eb, "exporter_renders", lambda: list(self.listing)), \
                mock.patch.object(self.eb, "compose", self._fake_compose()):
            self._write_png(1440, 4464)
            self.assertEqual(export_rescue.main(["--board", "01-ana-sayfa", "--out", str(out),
                                                 "--wait", "1", "--poll", "0.01"]), 0)
        self.assertEqual(self.eb.png_size(out / "01-ana-sayfa.png"), (1440, 4464))

    def test_silence_ends_with_the_measured_wait(self):
        with mock.patch.object(self.eb, "call_tool",
                               lambda *a, **k: (_ for _ in ()).throw(self.eb.McpError("bridge down"))), \
                mock.patch.object(self.eb, "exporter_renders", lambda: []), \
                mock.patch.object(self.eb, "compose", lambda *a: ""):
            with self.assertRaises(self.eb.McpError) as ctx:
                self.eb.export_png("u", self.info, self.target, wait=0.15, poll=0.01)
        self.assertIn("within 0.15s", str(ctx.exception))
        self.assertIn("bridge down", str(ctx.exception))

    def test_already_seen_files_are_not_accepted(self):
        self._write_png(1440, 4464)
        self.listing = ["penpot.resource.png.old"]
        with mock.patch.object(self.eb, "call_tool", lambda *a, **k: self._timeout_result()), \
                mock.patch.object(self.eb, "exporter_renders", lambda: list(self.listing)), \
                mock.patch.object(self.eb, "compose", self._fake_compose()):
            with self.assertRaises(self.eb.McpError):
                self.eb.export_png("u", self.info, self.target, wait=0.15, poll=0.01)
        # the render existed before the export fired: it belongs to an earlier call
        self.assertFalse(self.target.exists())


class RebuildLosslessTest(unittest.TestCase):
    """A rebuild must re-place provenance photos and report real counts."""

    def test_entries_for_board_requires_name_at_board_keys(self):
        prov = {
            "img-a": {"board": "13-kilavuzlar"},                  # legacy bare key
            "img-a@13-kilavuzlar": {"board": "13-kilavuzlar"},
            "img-b@13-kilavuzlar": {"board": "13-kilavuzlar"},
            "img-c@14-dergi": {"board": "14-dergi"},
        }
        self.assertEqual(media.entries_for_board(prov, "13-kilavuzlar"), ["img-a", "img-b"])
        self.assertEqual(media.entries_for_board(prov, "14-dergi"), ["img-c"])
        self.assertEqual(media.entries_for_board(prov, "99-yok"), [])

    def test_media_cache_key_carries_source_and_size(self):
        a = media.cached_path("img-x", 408, 320, "https://example/a.jpg")
        b = media.cached_path("img-x", 408, 320, "https://example/b.jpg")
        c = media.cached_path("img-x", 300, 320, "https://example/a.jpg")
        self.assertNotEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertEqual(a, media.cached_path("img-x", 408, 320, "https://example/a.jpg"))

    def test_expected_photo_names_reads_only_at_board_records(self):
        import build
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "provenance.json"
            path.write_text(json.dumps({
                "img-a": {"board": "13-kilavuzlar"},
                "img-a@13-kilavuzlar": {"board": "13-kilavuzlar"},
                "img-b@13-kilavuzlar": {"board": "13-kilavuzlar"},
            }))
            with mock.patch.object(build, "PROVENANCE", path):
                self.assertEqual(build.expected_photo_names("13-kilavuzlar"),
                                 ["img-a", "img-b"])

    def test_verify_photos_counts_exactly_one_fill_per_name(self):
        import build
        with mock.patch.object(build, "photo_counts",
                               lambda *a: {"img-a": 1, "img-b": 0, "img-c": 2}):
            ok, msg = build.verify_photos("u", "P", "B", ["img-a", "img-b", "img-c"])
        self.assertFalse(ok)
        self.assertIn("photos 1/3", msg)
        self.assertIn("img-b", msg)
        self.assertIn("img-c", msg)

    def test_verify_links_matches_destination_not_just_any_interaction(self):
        import build
        state = {"cta": ["next-board"], "other": ["next-board"]}
        with mock.patch.object(build, "current_page", lambda _u: "P"), \
                mock.patch.object(build, "call_execute_code",
                                  lambda *a: content_result(json.dumps(state))):
            ok, msg, missing = build.verify_links(
                "u", "P", "B", [{"shape": "cta", "dest": "next-board"}])
            self.assertTrue(ok)
            self.assertEqual(msg, "links 1/1")
            ok, msg, missing = build.verify_links(
                "u", "P", "B", [{"shape": "cta", "dest": "elsewhere"}])
        self.assertFalse(ok)
        self.assertIn("links 0/1", msg)
        self.assertIn("elsewhere", missing[0])


if __name__ == "__main__":
    unittest.main()
