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


if __name__ == "__main__":
    unittest.main()
