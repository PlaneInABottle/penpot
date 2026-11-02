#!/usr/bin/env python3
"""Offline unit tests for the Penpot automation scripts.

    python3 -m unittest scripts/test_penpot_scripts.py

No network and no Penpot: the MCP responses are fixtures shaped like the ones the
plugin returns.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import pathlib
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import design_qa  # noqa: E402
import penpot_exec  # noqa: E402
import tokens_sync  # noqa: E402
import design_lint  # noqa: E402
import rhythm  # noqa: E402

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


if __name__ == "__main__":
    unittest.main()
