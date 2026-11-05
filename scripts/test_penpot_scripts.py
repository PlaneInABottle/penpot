#!/usr/bin/env python3
"""Offline unit tests for the Penpot automation scripts.

    python3 -m unittest scripts/test_penpot_scripts.py

No network and no Penpot: the MCP responses are fixtures shaped like the ones the
plugin returns.
"""

from __future__ import annotations

import base64
import contextlib
import http.server
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "design" / "ihkd" / "tools"))
sys.path.insert(0, str(HERE.parent / "design" / "ihkd" / "build"))

import contrast_audit  # noqa: E402
import copy_lint  # noqa: E402
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


class _WireServer:
    """A loopback MCP endpoint that records requests and answers by method.

    Stateless by default — no `Mcp-Session-Id`, like the hosted instance — and
    stateful when a session id is passed, like the local server.
    """

    def __init__(self, *, session: str | None = None, result: dict | None = None,
                 status: dict | None = None, body: str = ""):
        import http.server
        outer = self
        self.requests: list[tuple[dict, dict]] = []
        self.result = result or {}
        self.status = status or {}
        self.body = body

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length") or 0)
                payload = json.loads(self.rfile.read(length) or b"{}")
                outer.requests.append((payload, dict(self.headers)))
                method = payload.get("method")
                if method in outer.status:
                    self._reply(outer.status[method], outer.body, {})
                elif method == "initialize":
                    extra = {"Mcp-Session-Id": session} if session else {}
                    self._reply(200, json.dumps({
                        "jsonrpc": "2.0", "id": 1,
                        "result": {"protocolVersion": "2025-06-18", "capabilities": {},
                                   "serverInfo": {"name": "wire", "version": "1"}}}), extra)
                elif method == "notifications/initialized":
                    self._reply(202, "", {})
                elif method == "tools/call":
                    name = (payload.get("params") or {}).get("name")
                    self._reply(200, json.dumps(outer.result.get(name) or {}), {})
                else:
                    self._reply(400, json.dumps({"error": "unknown method"}), {})

            def _reply(self, code: int, text: str, extra: dict) -> None:
                data = text.encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                for key, value in extra.items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args) -> None:
                pass

        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}/mcp?userToken=t"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()

    def methods(self) -> list[str]:
        return [payload.get("method") for payload, _ in self.requests]


def _header(headers: dict, name: str) -> str | None:
    return {key.lower(): value for key, value in headers.items()}.get(name.lower())


class McpWireTest(unittest.TestCase):
    """The real HTTP client against a fake endpoint, hosted-shape and local-shape.

    This proves the wire contract (headers, stateless handshake, ordering), not
    that the hosted service behaves this way; the live call is the acceptance.
    """

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        patcher = mock.patch.dict(os.environ, {
            "PENPOT_LOCK_DIR": str(self.tmp), "PENPOT_LOCK_WAIT": "5",
            "PENPOT_SESSION_WAIT": "5"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def _server(self, **kwargs) -> _WireServer:
        server = _WireServer(**kwargs)
        self.addCleanup(server.close)
        return server

    def test_stateless_initialize_needs_no_session_header(self):
        server = self._server(result={"execute_code": content_result('{"result": 2}')})
        result = penpot_exec.call_execute_code(server.url, "return 2;", write=False)
        self.assertEqual(penpot_exec.payload(result), 2)
        self.assertEqual(server.methods(),
                         ["initialize", "notifications/initialized", "tools/call"])
        for _, headers in server.requests:
            self.assertEqual(_header(headers, "User-Agent"), penpot_exec.USER_AGENT)
            self.assertNotIn("python-urllib", _header(headers, "User-Agent").lower())
            self.assertIsNone(_header(headers, "mcp-session-id"))

    def test_stateful_session_header_is_carried(self):
        server = self._server(session="abc123", result={"execute_code": content_result('"ok"')})
        penpot_exec.call_execute_code(server.url, "return 'ok';", write=False)
        self.assertEqual(server.methods(),
                         ["initialize", "notifications/initialized", "tools/call"])
        for payload, headers in server.requests[1:]:
            self.assertEqual(_header(headers, "mcp-session-id"), "abc123", payload.get("method"))

    def test_export_shape_uses_the_same_handshake(self):
        import export_board
        data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
        image = {"jsonrpc": "2.0", "id": 2, "result": {"content": [
            {"type": "image", "data": base64.b64encode(data).decode()}]}}
        server = self._server(result={"export_shape": image})
        result = export_board.tool_call(server.url, "export_shape", {"shapeId": "s1"})
        self.assertEqual(export_board.image_bytes(result), data)
        self.assertEqual(server.methods(),
                         ["initialize", "notifications/initialized", "tools/call"])
        self.assertEqual(server.requests[-1][0]["params"]["name"], "export_shape")
        self.assertIsNone(_header(server.requests[-1][1], "mcp-session-id"))

    def test_an_http_error_body_never_leaks_the_token(self):
        server = self._server(status={"initialize": 403})
        token = "c1c5439b-21a6-42f3-aea0-775ecbf416f0"
        server.url = server.url.rsplit("=", 1)[0] + "=" + token
        # the body echoes a bare token and the whole endpoint: both must be redacted
        server.body = "blocked userToken=" + token + " " + server.url
        with self.assertRaises(penpot_exec.McpError) as ctx:
            penpot_exec.call_execute_code(server.url, "return 1;", write=False)
        message = str(ctx.exception)
        self.assertNotIn(token, message)
        self.assertIn("userToken=<redacted>", message)
        self.assertIn("HTTP 403", message)

    def test_the_read_cli_runs_the_snippet_unchanged(self):
        server = self._server(result={"execute_code": content_result('"ok"')})
        with mock.patch.object(penpot_exec, "load_url", lambda: server.url), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(penpot_exec.main(["--read", "--code", "return 'ok';"]), 0)
        code = server.requests[-1][0]["params"]["arguments"]["code"]
        self.assertEqual(code, "return 'ok';", "a read must never prepend helper injection")


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

    def test_advisory_findings_are_printed_but_not_fatal_unless_strict(self):
        report = {"page": "Mobil", "shapes": 3, "boards": 1, "texts": 1,
                  "tokenSets": [{"name": "core", "tokens": 4, "active": True}],
                  "components": [], "unnamed": 1, "flows": [],
                  "interactiveShapes": 0,
                  "tokenCoverage": {"fills": "1/2", "textSizes": "1/1", "renderMismatches": 0,
                                    "hardColors": ["#FFFFFF"]}}
        with mock.patch.object(design_qa, "load_url", lambda: "u"), \
                mock.patch.object(design_qa, "ensure_helpers", lambda *a, **k: "1.5.0"), \
                mock.patch.object(design_qa, "audit", lambda url, page: report), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(design_qa.main(["--page", "Mobil"]), 0)
        text = out.getvalue()
        self.assertIn("hard-coded fill", text)
        self.assertIn("default name", text)
        self.assertIn("no prototype flow", text)
        self.assertIn("verdict: findings (non-strict)", text)
        self.assertIn("not a clean report", text)
        self.assertIn("pass --strict to fail all advisories", text)

        with mock.patch.object(design_qa, "load_url", lambda: "u"), \
                mock.patch.object(design_qa, "ensure_helpers", lambda *a, **k: "1.5.0"), \
                mock.patch.object(design_qa, "audit", lambda url, page: report), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(design_qa.main(["--page", "Mobil", "--strict"]), 1)

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
                 _node(id="cta1", name="hero cta", type="text", parentId="pg",
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
            for name in ("tile-01.png", "tile-02.png"):
                (pathlib.Path(tmp) / name).write_bytes(b"png")
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

    def _nodes(self, w=1600, h=1200, arrow=True):
        board = _node(id="b", name="01-home", type="board", parentId=None,
                      x=0, y=0, w=w, h=h)
        nav = _node(id="nav", name="primary nav ghost", type="text", parentId="b",
                    parent="01-home", x=100, y=10, w=120, h=20, fill="#111",
                    fontSize=16, lineHeight="1.5", text="Sign in",
                    inkX=100, inkY=10, inkW=80, inkH=17)
        footer = _node(id="foot", name="footer primary", type="text", parentId="b",
                       parent="01-home", x=100, y=50, w=160, h=20, fill="#111",
                       fontSize=16, lineHeight="1.5", text="Join now",
                       inkX=100, inkY=50, inkW=100, inkH=17)
        hero = _node(id="hero", name="hero cta", type="text", parentId="b",
                     parent="01-home", x=100, y=400, w=200, h=40, fill="#111",
                     fontSize=16, lineHeight="1.5", text="Join the program",
                     inkX=100, inkY=400, inkW=160, inkH=20)
        nodes = [board, nav, footer, hero]
        if arrow:
            nodes.append(_node(id="arrow", name="arrow icon", type="text", parentId="b",
                               parent="01-home", x=1400, y=500, w=80, h=20, fill="#111",
                               fontSize=16, lineHeight="1.5", text="->",
                               inkX=1400, inkY=500, inkW=24, inkH=17))
        return nodes

    def _write_nodes(self, tmp, arrow=True, w=1600, h=1200):
        path = pathlib.Path(tmp) / "nodes.json"
        path.write_text(json.dumps(self._nodes(w=w, h=h, arrow=arrow)))
        return path

    def _run_crop(self, argv):
        import crop_board
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = crop_board.main(argv)
        return code, buf.getvalue()

    def _manifest(self, out):
        return json.loads((out / "manifest.json").read_text())

    def _mark_reviewed(self, out):
        path = out / "manifest.json"
        manifest = json.loads(path.read_text())
        for entry in manifest["tiles"] + manifest["regions"]:
            entry["reviewed"] = True
            entry["note"] = "checked at 1:1"
        path.write_text(json.dumps(manifest))
        return manifest

    def test_explicit_primary_action_beats_the_heuristic(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self._png(tmp, 1600, 1200)
            nodes = self._write_nodes(tmp)
            out = pathlib.Path(tmp) / "tiles"
            code, stdout = self._run_crop(["--png", str(src), "--out", str(out),
                                           "--regions", str(nodes),
                                           "--primary-action", "hero cta"])
            self.assertEqual(code, 0, stdout)
            regions = {r["file"]: r for r in self._manifest(out)["regions"]}
            self.assertEqual(regions["region-primary-action.png"]["subject"], "hero cta")
            import crop_board
            auto = {r["slug"]: r for r in crop_board.pick_regions(self._nodes())}
            self.assertEqual(auto["primary-action"]["name"], "footer primary",
                             "the nav ghost must not win the CTA heuristic")

    def test_region_flag_is_repeatable(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self._png(tmp, 1600, 1200)
            out = pathlib.Path(tmp) / "tiles"
            one = json.dumps({"slug": "one", "name": "one", "x": 10, "y": 10, "w": 20, "h": 20})
            two = json.dumps({"slug": "two", "name": "two", "x": 40, "y": 40, "w": 20, "h": 20})
            code, stdout = self._run_crop(["--png", str(src), "--out", str(out),
                                           "--region", one, "--region", two])
            self.assertEqual(code, 0, stdout)
            regions = {r["file"] for r in self._manifest(out)["regions"]}
            self.assertEqual(regions, {"region-one.png", "region-two.png"})

    def test_rerun_keeps_a_declared_region_and_its_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self._png(tmp, 1600, 1200)
            nodes = self._write_nodes(tmp)
            out = pathlib.Path(tmp) / "tiles"
            region = json.dumps({"slug": "deep-rule", "name": "1px rule",
                                 "x": 20, "y": 30, "w": 40, "h": 40})
            code, stdout = self._run_crop(["--png", str(src), "--out", str(out),
                                           "--regions", str(nodes), "--region", region])
            self.assertEqual(code, 0, stdout)
            self._mark_reviewed(out)
            code, stdout = self._run_crop(["--png", str(src), "--out", str(out),
                                           "--regions", str(nodes)])
            self.assertEqual(code, 0, stdout)
            regions = {r["file"]: r for r in self._manifest(out)["regions"]}
            self.assertIn("region-deep-rule.png", regions)
            self.assertTrue(regions["region-deep-rule.png"]["reviewed"])
            self.assertEqual(regions["region-deep-rule.png"]["origin"], "declared")

    def test_changed_source_invalidates_attestation(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self._png(tmp, 1600, 1200)
            nodes = self._write_nodes(tmp)
            out = pathlib.Path(tmp) / "tiles"
            self.assertEqual(self._run_crop(["--png", str(src), "--out", str(out),
                                             "--regions", str(nodes)])[0], 0)
            self._mark_reviewed(out)
            from PIL import Image as PILImage
            PILImage.new("RGB", (1600, 1200), "gray").save(src)
            code, stdout = self._run_crop(["--png", str(src), "--out", str(out),
                                           "--regions", str(nodes)])
            self.assertEqual(code, 0, stdout)
            manifest = self._manifest(out)
            self.assertFalse(any(e["reviewed"] for e in manifest["tiles"] + manifest["regions"]))

    def test_attest_rejects_a_missing_png(self):
        import crop_board
        with tempfile.TemporaryDirectory() as tmp:
            manifest = pathlib.Path(tmp) / "manifest.json"
            manifest.write_text(json.dumps({
                "tiles": [{"file": "tile-01.png", "reviewed": True, "note": "checked"}],
                "regions": []}))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = crop_board.attest_manifest(manifest)
            self.assertEqual(code, 1)
            self.assertIn("referenced PNG(s) missing", buf.getvalue())
            self.assertIn("tile-01.png", buf.getvalue())

    def test_rerun_removes_stale_generated_tiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self._png(tmp, 3000, 1200)
            nodes = self._write_nodes(tmp, w=3000, h=1200)
            out = pathlib.Path(tmp) / "tiles"
            self.assertEqual(self._run_crop(["--png", str(src), "--out", str(out),
                                             "--regions", str(nodes)])[0], 0)
            self.assertTrue((out / "tile-02.png").is_file())
            from PIL import Image as PILImage
            PILImage.new("RGB", (800, 600), "white").save(src)
            code, stdout = self._run_crop(["--png", str(src), "--out", str(out)])
            self.assertEqual(code, 0, stdout)
            self.assertFalse((out / "tile-02.png").exists())
            self.assertIn("removed stale generated PNG", stdout)
            self.assertTrue((out / "tile-01.png").is_file())

    def test_off_origin_board_uses_board_relative_regions(self):
        from PIL import Image as PILImage, ImageDraw
        with tempfile.TemporaryDirectory() as tmp:
            image = PILImage.new("RGB", (400, 600), (245, 245, 245))
            draw = ImageDraw.Draw(image)
            draw.rectangle([0, 40, 399, 79], fill=(224, 54, 75))
            src = pathlib.Path(tmp) / "shot.png"
            image.save(src)
            nodes = [_node(id="b", name="01-home", type="board", parentId=None,
                           x=0, y=440, w=400, h=600),
                     _node(id="t", name="tiny label", type="text", parentId="b",
                           parent="01-home", x=100, y=490, w=120, h=16, fill="#111111",
                           fontSize=13, lineHeight="1.5", text="Label",
                           inkX=100, inkY=490, inkW=100, inkH=16)]
            nodes_path = pathlib.Path(tmp) / "nodes.json"
            nodes_path.write_text(json.dumps(nodes))
            out = pathlib.Path(tmp) / "tiles"
            region = json.dumps({"slug": "declared", "name": "band",
                                 "x": 100, "y": 50, "w": 40, "h": 20})
            code, stdout = self._run_crop(["--png", str(src), "--out", str(out),
                                           "--regions", str(nodes_path), "--region", region])
            self.assertEqual(code, 0, stdout)
            self.assertEqual(self._manifest(out)["board"], "01-home")
            declared = PILImage.open(out / "region-declared.png").convert("RGB")
            self.assertEqual(declared.getpixel((10, 10)), (224, 54, 75),
                             "declared y=50 is board-relative, not page y=490")
            auto = PILImage.open(out / "region-smallest-text.png").convert("RGB")
            self.assertEqual(auto.getpixel((10, 34)), (224, 54, 75),
                             "node y=490 must convert against board y=440")

    def test_region_board_dimension_mismatch_preserves_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self._png(tmp, 400, 600)
            nodes = pathlib.Path(tmp) / "nodes.json"
            nodes.write_text(json.dumps([
                _node(id="b", name="01-home", type="board", parentId=None,
                      x=0, y=0, w=1600, h=1200)]))
            out = pathlib.Path(tmp) / "tiles"
            out.mkdir()
            (out / "tile-01.png").write_bytes(b"old tile")
            (out / "manifest.json").write_text('{"board": "old"}')
            err = io.StringIO()
            with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as ctx:
                import crop_board
                crop_board.main(["--png", str(src), "--out", str(out),
                                 "--regions", str(nodes)])
            self.assertEqual(ctx.exception.code, 2)
            self.assertIn("but the render is 400x600", err.getvalue())
            self.assertEqual((out / "tile-01.png").read_bytes(), b"old tile")
            self.assertEqual((out / "manifest.json").read_text(), '{"board": "old"}')

    def test_ambiguous_node_boards_require_an_explicit_board(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self._png(tmp, 400, 600)
            nodes = [_node(id="a", name="A", type="board", parentId=None,
                           x=0, y=0, w=400, h=600),
                     _node(id="b", name="B", type="board", parentId=None,
                           x=0, y=0, w=400, h=600)]
            path = pathlib.Path(tmp) / "nodes.json"
            path.write_text(json.dumps(nodes))
            err = io.StringIO()
            with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as ctx:
                import crop_board
                crop_board.main(["--png", str(src), "--out", str(pathlib.Path(tmp) / "t"),
                                 "--regions", str(path)])
            self.assertEqual(ctx.exception.code, 2)
            self.assertIn("pass --board", err.getvalue())

    def test_primary_action_without_regions_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, str(HERE / "crop_board.py"), "--png", "missing.png",
                 "--out", str(pathlib.Path(tmp) / "tiles"),
                 "--primary-action", "hero cta"],
                capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            self.assertIn("--primary-action requires --regions", proc.stderr)

    def test_masthead_cta_does_not_win_the_heuristic(self):
        import crop_board
        nodes = [_node(id="b", name="01-home", type="board", parentId=None,
                       x=0, y=0, w=1440, h=2000),
                 _node(id="m", name="masthead cta", type="text", parentId="b",
                       parent="01-home", x=100, y=472, w=160, h=20, fill="#111",
                       fontSize=16, lineHeight="1.5", text="Join",
                       inkX=100, inkY=472, inkW=100, inkH=17),
                 _node(id="ml", name="masthead cta / label", type="text", parentId="b",
                       parent="01-home", x=100, y=480, w=160, h=20, fill="#111",
                       fontSize=16, lineHeight="1.5", text="Join",
                       inkX=100, inkY=480, inkW=100, inkH=17),
                 _node(id="hero", name="hero cta", type="text", parentId="b",
                       parent="01-home", x=100, y=848, w=200, h=40, fill="#111",
                       fontSize=16, lineHeight="1.5", text="Join the program",
                       inkX=100, inkY=848, inkW=160, inkH=20)]
        primary = {r["slug"]: r for r in crop_board.pick_regions(nodes)}["primary-action"]
        self.assertEqual(primary["name"], "hero cta")

    def test_board_mismatch_drops_old_declared_regions_and_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = self._png(tmp, 400, 600)
            out = pathlib.Path(tmp) / "tiles"
            one = json.dumps({"slug": "a-region", "name": "A", "x": 10, "y": 10,
                              "w": 20, "h": 20})
            self.assertEqual(self._run_crop(["--png", str(first), "--board", "A",
                                             "--out", str(out), "--region", one])[0], 0)
            self._mark_reviewed(out)
            self.assertTrue((out / "region-a-region.png").is_file())
            two = json.dumps({"slug": "b-region", "name": "B", "x": 10, "y": 10,
                              "w": 20, "h": 20})
            # Same source hash, different board: no review or region may carry.
            code, stdout = self._run_crop(["--png", str(first), "--board", "B",
                                           "--out", str(out), "--region", two])
            self.assertEqual(code, 0, stdout)
            manifest = self._manifest(out)
            self.assertEqual(manifest["board"], "B")
            self.assertNotIn("region-a-region.png",
                             {r["file"] for r in manifest["regions"]})
            self.assertFalse((out / "region-a-region.png").exists())
            self.assertTrue((out / "region-b-region.png").is_file())
            self.assertFalse(any(e["reviewed"] for e in manifest["tiles"] + manifest["regions"]))

    def test_unmanifested_generated_orphan_is_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self._png(tmp)
            out = pathlib.Path(tmp) / "tiles"
            out.mkdir()
            (out / "tile-99.png").write_bytes(b"orphan")
            (out / "keep-me.png").write_bytes(b"user asset")
            code, stdout = self._run_crop(["--png", str(src), "--out", str(out)])
            self.assertEqual(code, 0, stdout)
            self.assertFalse((out / "tile-99.png").exists())
            self.assertTrue((out / "keep-me.png").exists())

    def test_coverage_claims_icon_region_only_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = self._png(tmp, 1600, 1200)
            out = pathlib.Path(tmp) / "tiles"
            nodes = self._write_nodes(tmp, arrow=True)
            code, stdout = self._run_crop(["--png", str(src), "--out", str(out),
                                           "--regions", str(nodes)])
            self.assertEqual(code, 0, stdout)
            manifest = self._manifest(out)
            self.assertIn("icons-arrows", manifest["coverage"]["required"])

        with tempfile.TemporaryDirectory() as tmp:
            src = self._png(tmp, 1600, 1200)
            out = pathlib.Path(tmp) / "tiles"
            nodes = self._write_nodes(tmp, arrow=False)
            code, stdout = self._run_crop(["--png", str(src), "--out", str(out),
                                           "--regions", str(nodes)])
            self.assertEqual(code, 0, stdout)
            manifest = self._manifest(out)
            self.assertNotIn("icons-arrows", manifest["coverage"]["required"])
            self.assertIn("no icon/arrow row detected", stdout)


class ImportMediaContractTest(unittest.TestCase):
    """The generic importer's real CLI, and the docs that must not invent flags."""

    def _run(self, *args):
        return subprocess.run([sys.executable, str(HERE / "import_media.py"), *args],
                              capture_output=True, text=True)

    def test_project_only_flags_are_rejected_before_any_network(self):
        required = ["--url", "http://example.invalid/x", "--name", "img-a", "--page", "P",
                    "--board", "B", "--w", "1", "--h", "1"]
        for flag, value in (("--only", "img-a"), ("--force", None)):
            argv = required + [flag] + ([value] if value else [])
            proc = self._run(*argv)
            self.assertEqual(proc.returncode, 2, proc.stderr)
            self.assertIn(f"unrecognized arguments: {flag}", proc.stderr)

    def test_help_lists_source_and_geometry_flags(self):
        proc = self._run("--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for flag in ("--url", "--search", "--name", "--page", "--board",
                     "--x", "--y", "--w", "--h"):
            self.assertIn(flag, proc.stdout)
        self.assertNotIn("--only", proc.stdout)
        self.assertNotIn("--restore", proc.stdout)

    def test_docs_do_not_call_project_flags_generic(self):
        root = HERE.parent
        for rel in ("AGENTS.md", ".agents/skills/penpot-mcp-operations/SKILL.md",
                    ".agents/skills/penpot-design-system/references/craft.md",
                    "design/_template/media/README.md"):
            text = (root / rel).read_text(encoding="utf-8")
            self.assertNotIn("scripts/import_media.py --only", text, rel)
            self.assertNotIn("scripts/import_media.py --force", text, rel)

    def test_recipe_requires_persisting_provenance_before_a_rebuild(self):
        root = HERE.parent
        agents = (root / "AGENTS.md").read_text(encoding="utf-8")
        media = (root / "design/_template/media/README.md").read_text(encoding="utf-8")
        self.assertIn("does not write a media table", agents)
        self.assertIn("does not write the table", media)
        self.assertIn("prints `source:` and `provenance:`", media)
        self.assertIn("claiming a lossless", media)


class RebuildContractDocsTest(unittest.TestCase):
    def test_template_requires_the_project_runner_contract(self):
        text = (HERE.parent / "design" / "_template" / "build" / "README.md").read_text(
            encoding="utf-8")
        self.assertIn("does **not** ship one", text)
        self.assertIn("raw", text)
        self.assertIn("not a rebuild", text)
        for needle in ("currentPage", "fit", "photos", "links", "flows.js",
                       "RESULT ok|fail nulls=N"):
            self.assertIn(needle, text)


class ContrastAuditTest(unittest.TestCase):
    @staticmethod
    def _text(name="title", board_id="b", order=9, fg="#111111", cx=100, cy=100, size=32):
        return {"name": name, "board": "board", "boardId": board_id, "order": order,
                "fg": fg, "fgImage": False, "fgOpacity": 1, "size": size,
                "variant": "regular", "cx": cx, "cy": cy}

    @staticmethod
    def _layer(order=0, board_id="b", kind="solid", fill="#FFFFFF", opacity=1,
               x=0, y=0, w=400, h=400, name="layer"):
        return {"order": order, "boardId": board_id, "board": "board", "kind": kind,
                "fill": fill, "opacity": opacity, "x": x, "y": y, "w": w, "h": h, "name": name}

    def test_sibling_photo_is_manual_not_a_white_pass(self):
        data = {"layers": [self._layer(), self._layer(order=1, kind="image", fill=None)],
                "texts": [self._text(order=2)]}
        report = contrast_audit.resolve(data)
        self.assertEqual(report["checked"], 0)
        self.assertEqual(report["fails"], [])
        self.assertIn("over image fill", report["manual"][0]["reason"])

    def test_image_ancestor_is_manual(self):
        data = {"layers": [self._layer(kind="image", fill=None)], "texts": [self._text()]}
        report = contrast_audit.resolve(data)
        self.assertIn("over image fill", report["manual"][0]["reason"])

    def test_cross_board_isolation(self):
        data = {
            "layers": [self._layer(board_id="dark", fill="#000000"),
                       self._layer(order=2, board_id="light", fill="#FFFFFF")],
            "texts": [self._text(name="dark text", board_id="dark", order=1),
                      self._text(name="light text", board_id="light", order=3)],
        }
        report = contrast_audit.resolve(data)
        names = [row["name"] for row in report["fails"]]
        self.assertEqual(names, ["dark text"], "the light board must not borrow the dark fill")

    def test_later_sibling_and_opaque_layer_win(self):
        data = {
            "layers": [self._layer(fill="#FFFFFF"),
                       self._layer(order=1, fill="#000000", name="panel"),
                       self._layer(order=2, fill="#FFFFFF", name="card")],
            "texts": [self._text(order=3, fg="#111111")],
        }
        report = contrast_audit.resolve(data)
        self.assertEqual(report["checked"], 1)
        self.assertEqual(report["fails"], [])
        self.assertEqual(report["manual"], [])

    def test_translucent_layer_is_unsupported_compositing(self):
        data = {"layers": [self._layer(fill="#000000"),
                           self._layer(order=1, opacity=0.4, fill="#FFFFFF")],
                "texts": [self._text(order=2)]}
        report = contrast_audit.resolve(data)
        self.assertEqual(report["checked"], 0)
        self.assertIn("translucent layer", report["manual"][0]["reason"])

    def test_alpha_text_colour_is_manual(self):
        data = {"layers": [self._layer()], "texts": [self._text(order=1, fg="#11111180")]}
        report = contrast_audit.resolve(data)
        self.assertEqual(report["checked"], 0)
        self.assertIn("text fill carries alpha", report["manual"][0]["reason"])

    def test_no_background_is_unknown_not_pass(self):
        data = {"layers": [], "texts": [self._text()]}
        report = contrast_audit.resolve(data)
        self.assertEqual(report["checked"], 0)
        self.assertIn("no painted shape", report["manual"][0]["reason"])

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def _collect(self, shapes):
        code = contrast_audit.COLLECT.replace("__PAGE__", json.dumps("Page"))
        script = pathlib.Path(tempfile.mkdtemp()) / "collect.js"
        self.addCleanup(shutil.rmtree, script.parent, True)
        script.write_text(
            "const code = " + json.dumps(code) + ";\n"
            "const page = " + json.dumps(shapes) + ";\n"
            "const penpot = {currentFile: {pages: [{name: 'Page', root: page}]}};\n"
            "console.log(new Function('penpot', code)(penpot));\n")
        proc = subprocess.run(["node", str(script)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def _board(self, children, **over):
        board = {"type": "board", "id": "b1", "name": "01-home", "x": 0, "y": 0,
                 "width": 400, "height": 400,
                 "fills": [{"fillColor": "#FFFFFF", "fillOpacity": 1}],
                 "children": children}
        board.update(over)
        return board

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_collector_propagates_the_top_level_board_scope(self):
        shapes = {"children": [
            self._board([{"type": "board", "id": "panel", "name": "panel", "x": 0, "y": 0,
                          "width": 200, "height": 200, "fills": [], "children": [
                              {"type": "text", "id": "t1", "name": "title", "x": 10, "y": 10,
                               "width": 100, "height": 20, "fontSize": 16,
                               "fills": [{"fillColor": "#111111", "fillOpacity": 1}],
                               "textBounds": {"x": 10, "y": 10, "width": 100, "height": 20},
                               "children": []}]}]),
            {"type": "board", "id": "b2", "name": "02-other", "x": 500, "y": 0,
             "width": 400, "height": 400, "fills": [{"fillColor": "#000000", "fillOpacity": 1}],
             "children": []},
        ]}
        data = self._collect(shapes)
        self.assertEqual(data["texts"][0]["boardId"], "b1")
        self.assertEqual(data["texts"][0]["board"], "01-home")
        self.assertEqual({layer["boardId"] for layer in data["layers"]}, {"b1", "b2"})

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_shape_opacity_becomes_effective_text_opacity_and_manual(self):
        shapes = {"children": [self._board([
            {"type": "rectangle", "id": "red", "name": "on red", "x": 0, "y": 0,
             "width": 400, "height": 400, "opacity": 1,
             "fills": [{"fillColor": "#E0364B", "fillOpacity": 1}], "children": []},
            {"type": "text", "id": "t", "name": "mc label", "x": 10, "y": 10,
             "width": 100, "height": 20, "fontSize": 13, "opacity": 0.72,
             "fills": [{"fillColor": "#FFFFFF", "fillOpacity": 1}],
             "textBounds": {"x": 10, "y": 10, "width": 100, "height": 20}, "children": []},
        ])]}
        data = self._collect(shapes)
        self.assertAlmostEqual(data["texts"][0]["fgOpacity"], 0.72)
        report = contrast_audit.resolve(data)
        self.assertEqual(report["checked"], 0)
        self.assertIn("translucent text fill", report["manual"][0]["reason"])

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_hidden_layer_and_subtree_cannot_mask_a_visible_photo(self):
        hidden_board = {"type": "board", "id": "hidden-panel", "name": "hidden panel",
                        "x": 0, "y": 0, "width": 400, "height": 400, "visible": False,
                        "fills": [{"fillColor": "#FFFFFF", "fillOpacity": 1}], "children": [
                            {"type": "text", "id": "hidden-text", "name": "hidden caption",
                             "x": 10, "y": 10, "width": 100, "height": 20, "fontSize": 13,
                             "fills": [{"fillColor": "#111111", "fillOpacity": 1}],
                             "textBounds": {"x": 10, "y": 10, "width": 100, "height": 20},
                             "children": []}]}
        shapes = {"children": [self._board([
            {"type": "rectangle", "id": "photo", "name": "photo", "x": 0, "y": 0,
             "width": 400, "height": 400, "visible": True,
             "fills": [{"fillImage": {"id": "m"}, "fillOpacity": 1}], "children": []},
            {"type": "rectangle", "id": "hidden-white", "name": "hidden white",
             "x": 0, "y": 0, "width": 400, "height": 400, "visible": False,
             "fills": [{"fillColor": "#FFFFFF", "fillOpacity": 1}], "children": []},
            hidden_board,
            {"type": "text", "id": "t", "name": "caption", "x": 10, "y": 10,
             "width": 100, "height": 20, "fontSize": 13,
             "fills": [{"fillColor": "#111111", "fillOpacity": 1}],
             "textBounds": {"x": 10, "y": 10, "width": 100, "height": 20}, "children": []},
        ])]}
        data = self._collect(shapes)
        self.assertEqual([t["name"] for t in data["texts"]], ["caption"])
        self.assertNotIn("hidden white", {layer["name"] for layer in data["layers"]})
        report = contrast_audit.resolve(data)
        self.assertEqual(report["checked"], 0)
        self.assertIn("over image fill", report["manual"][0]["reason"])

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_shape_opacity_on_a_layer_is_manual(self):
        shapes = {"children": [self._board([
            {"type": "rectangle", "id": "red", "name": "on red", "x": 0, "y": 0,
             "width": 400, "height": 400, "opacity": 0.72,
             "fills": [{"fillColor": "#E0364B", "fillOpacity": 1}], "children": []},
            {"type": "text", "id": "t", "name": "caption", "x": 10, "y": 10,
             "width": 100, "height": 20, "fontSize": 13,
             "fills": [{"fillColor": "#FFFFFF", "fillOpacity": 1}],
             "textBounds": {"x": 10, "y": 10, "width": 100, "height": 20}, "children": []},
        ])]}
        data = self._collect(shapes)
        self.assertAlmostEqual(data["layers"][-1]["opacity"], 0.72)
        report = contrast_audit.resolve(data)
        self.assertEqual(report["checked"], 0)
        self.assertIn("over translucent layer", report["manual"][0]["reason"])

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_gradient_layer_is_manual_not_dropped(self):
        shapes = {"children": [self._board([
            {"type": "rectangle", "id": "grad", "name": "gradient", "x": 0, "y": 0,
             "width": 400, "height": 400, "opacity": 1,
             "fills": [{"fillColor": "#FFFFFF", "fillOpacity": 1,
                        "fillColorGradient": {"type": "linear"}}], "children": []},
            {"type": "text", "id": "t", "name": "title", "x": 10, "y": 10,
             "width": 100, "height": 20, "fontSize": 32,
             "fills": [{"fillColor": "#111111", "fillOpacity": 1}],
             "textBounds": {"x": 10, "y": 10, "width": 100, "height": 20}, "children": []},
        ])]}
        data = self._collect(shapes)
        self.assertEqual(data["layers"][-1]["kind"], "gradient")
        report = contrast_audit.resolve(data)
        self.assertEqual(report["checked"], 0)
        self.assertIn("over gradient fill", report["manual"][0]["reason"])

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_alpha_colour_is_manual_not_a_fabricated_ratio(self):
        shapes = {"children": [self._board([
            {"type": "rectangle", "id": "band", "name": "alpha band", "x": 0, "y": 0,
             "width": 400, "height": 400, "opacity": 1,
             "fills": [{"fillColor": "#E0364B80", "fillOpacity": 1}], "children": []},
            {"type": "text", "id": "t", "name": "title", "x": 10, "y": 10,
             "width": 100, "height": 20, "fontSize": 32,
             "fills": [{"fillColor": "#111111", "fillOpacity": 1}],
             "textBounds": {"x": 10, "y": 10, "width": 100, "height": 20}, "children": []},
        ])]}
        data = self._collect(shapes)
        report = contrast_audit.resolve(data)
        self.assertEqual(report["checked"], 0)
        self.assertIn("alpha colour", report["manual"][0]["reason"])

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_inherited_ancestor_opacity_is_manual(self):
        panel = {"type": "board", "id": "panel", "name": "panel", "x": 0, "y": 0,
                 "width": 300, "height": 300, "opacity": 0.72,
                 "fills": [{"fillColor": "#E0364B", "fillOpacity": 1}], "children": [
                     {"type": "text", "id": "t", "name": "caption", "x": 10, "y": 10,
                      "width": 100, "height": 20, "fontSize": 13,
                      "fills": [{"fillColor": "#FFFFFF", "fillOpacity": 1}],
                      "textBounds": {"x": 10, "y": 10, "width": 100, "height": 20},
                      "children": []}]}
        data = self._collect({"children": [self._board([panel])]})
        self.assertAlmostEqual(data["texts"][0]["fgOpacity"], 0.72)
        report = contrast_audit.resolve(data)
        self.assertEqual(report["checked"], 0)
        self.assertIn("translucent", report["manual"][0]["reason"])


class CopyLintTest(unittest.TestCase):
    def _run(self, project: pathlib.Path) -> tuple[int, str]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf), \
                mock.patch.object(copy_lint, "load_url",
                                  lambda: (_ for _ in ()).throw(AssertionError("plugin call"))):
            try:
                code = copy_lint.main(["--page", "P", "--project", str(project)])
            except SystemExit as exc:
                code = int(exc.code or 0)
        return code, buf.getvalue()

    def test_empty_terms_exit_zero_before_any_plugin_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            (project / "copy-terms.json").write_text('{"terms": [], "allow": []}')
            code, out = self._run(project)
        self.assertEqual(code, 0, out)
        self.assertIn("no terms declared", out)

    def test_missing_terms_file_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = self._run(pathlib.Path(tmp))
        self.assertEqual(code, 0, out)
        self.assertIn("nothing to check", out)

    def test_malformed_schema_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp)
            (project / "copy-terms.json").write_text('{"terms": "kalp"}')
            code, out = self._run(project)
        self.assertEqual(code, 1, out)
        self.assertIn("terms must be a list of non-empty strings", out)

    def test_actual_term_detection(self):
        self.assertEqual(copy_lint.find_typos(["kap"], ["kalp"], []),
                         [("kap", "kap", "kalp")])
        self.assertEqual(copy_lint.find_typos(["kalp"], ["kalp"], []), [])


class ReadOnlyCollectorTest(unittest.TestCase):
    """Read-only mains serialize on the call lock, bypass a build session, never inject helpers."""

    URL = "http://localhost:4401/mcp?userToken=SECRET-TOKEN-1234"

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.addCleanup(penpot_exec._HELD.clear)

    def _hold_session(self):
        holder = (
            "import sys, time\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "import penpot_exec\n"
            "penpot_exec.acquire_session(sys.argv[2])\n"
            "print('held', flush=True)\n"
            "time.sleep(float(sys.argv[3]))\n"
        )
        path = self.tmp / "holder_session.py"
        path.write_text(holder)
        env = dict(os.environ, PENPOT_LOCK_DIR=str(self.tmp), PENPOT_SESSION_WAIT="0.4",
                   PENPOT_LOCK_WAIT="5")
        hold = subprocess.Popen([sys.executable, str(path), str(HERE), self.URL, "3"],
                                stdout=subprocess.PIPE, text=True, env=env)
        self.addCleanup(hold.stdout.close)
        self.addCleanup(hold.kill)
        self.assertEqual(hold.stdout.readline().strip(), "held")

    def _run(self, module, argv, payload):
        codes: list[str] = []

        def fake_execute(url, code):
            codes.append(code)
            return content_result(json.dumps(payload))

        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, {"PENPOT_LOCK_DIR": str(self.tmp),
                                          "PENPOT_SESSION_WAIT": "900",
                                          "PENPOT_LOCK_WAIT": "5"}), \
                mock.patch.object(module, "load_url", lambda: self.URL), \
                mock.patch.object(penpot_exec, "_execute", fake_execute), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            started = time.monotonic()
            code = module.main(argv)
            elapsed = time.monotonic() - started
        self.assertIn("build in progress", err.getvalue())
        self.assertLess(elapsed, 2.0, "a reader must not wait for the writer session")
        self.assertEqual(len(codes), 1, codes)
        self.assertNotIn("Penpot MCP helpers", codes[0], "helpers must not be injected")
        self.assertNotIn("storage.H", codes[0], "helpers must not be injected")
        return code, out.getvalue()

    def test_contrast_audit_is_a_read(self):
        self._hold_session()
        code, out = self._run(contrast_audit, ["--page", "P"],
                              {"texts": [], "layers": []})
        self.assertEqual(code, 0, out)
        self.assertIn("NOTHING CHECKED", out)

    def test_copy_lint_is_a_read(self):
        self._hold_session()
        project = self.tmp / "proj"
        project.mkdir()
        (project / "copy-terms.json").write_text('{"terms": ["kalp"], "allow": []}')
        code, out = self._run(copy_lint, ["--page", "P", "--project", str(project)], [])
        self.assertEqual(code, 0, out)

    def test_ux_gate_is_a_read(self):
        import ux_gate
        self._hold_session()
        spec = self.tmp / "ux-spec.json"
        spec.write_text(json.dumps({"screens": [
            {"board": "01-home", "page": "Web", "task": "x"}]}))
        code, out = self._run(ux_gate, ["--spec", str(spec)], [])
        self.assertEqual(code, 1, out)  # board missing is a finding, not transport


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

    def test_mobile_is_opt_in_when_the_key_is_omitted(self):
        import ux_gate
        spec = self._screen_spec()
        del spec["screens"][0]["mobile"]
        self.assertEqual(ux_gate.evaluate(spec, {"Web": self._screen_nodes()}), [])

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

    def test_viewport_height_is_per_screen(self):
        """A per-screen viewportH wins over the defaults: the same text at y 870
        sits inside a 900 fold and below an 850 fold."""
        import ux_gate
        nodes = self._screen_nodes()
        nodes.append(_node(id="b2", name="02-home", type="board", parentId=None,
                           x=0, y=0, w=1440, h=2000))
        nodes.append(_node(id="c2", name="hero cta", type="board", parentId="b2",
                           parent="02-home", x=120, y=392, w=200, h=48, fill="#E0364B"))
        for board_id, node_id in (("b1", "t2"), ("b2", "t3")):
            nodes.append(_node(id=node_id, name="fold note", type="text", parentId=board_id,
                               parent="01-home" if board_id == "b1" else "02-home",
                               x=120, y=870, w=300, h=20, fill="#0E1318",
                               fontSize=16, lineHeight="1.5", text="Fold",
                               inkX=120, inkY=870, inkW=100, inkH=17))
        base = self._screen_spec()["screens"][0]
        spec = {"project": "demo", "defaults": {"accentMaxRatio": 0.3, "viewportH": 900},
                "screens": [dict(base, board="01-home", firstViewport=["fold note"]),
                            dict(base, board="02-home", firstViewport=["fold note"],
                                 viewportH=850)]}
        findings = ux_gate.evaluate(spec, {"Web": nodes})
        folds = [f["screen"] for f in findings if "below the fold" in f["finding"]]
        self.assertEqual(folds, ["02-home"], findings)


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
    def _report(self, first_y, args=None, rule_name="masthead rule"):
        board = _node(id="b", name="board", type="board", parentId=None,
                      x=0, y=400, w=1440, h=2000)
        rule = _node(id="r", name=rule_name, parentId="b", parent="board",
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
                code = rhythm.main([str(path)] + list(args or []))
        return code, buf.getvalue()

    def test_flags_large_void(self):
        code, out = self._report(236)
        self.assertEqual(code, 0)
        self.assertIn("TOP-VOID", out)
        self.assertIn("151px", out)
        self.assertIn("advisory", out)

    def test_ok_small_void(self):
        code, out = self._report(156)
        self.assertEqual(code, 0)
        self.assertNotIn("TOP-VOID", out)
        self.assertIn("top-void ok", out)

    def test_over_2x_gap_is_visibly_advisory_and_exits_zero(self):
        board = _node(id="b", name="board", type="board", parentId=None,
                      x=0, y=0, w=1440, h=2000)
        a = _node(id="a", name="row a", parentId="b", parent="board", x=120, y=10, w=500, h=20)
        b = _node(id="b-row", name="row b", parentId="b", parent="board", x=120, y=40, w=500, h=20)
        c = _node(id="c", name="row c", parentId="b", parent="board", x=120, y=600, w=500, h=20)
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "nodes.json"
            path.write_text(json.dumps([board, a, b, c]))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = rhythm.main([str(path), "--rhythm", "30"])
        self.assertEqual(code, 0, "rhythm stays advisory, not a finding")
        self.assertIn("advisory over-2x: [540]", buf.getvalue())
        self.assertIn("not a gate", buf.getvalue())

    def test_rule_name_selects_the_head_rule(self):
        code, out = self._report(236, args=["--rule-name", "head rule"], rule_name="head rule")
        self.assertEqual(code, 0)
        self.assertIn("TOP-VOID", out)
        code, out = self._report(236, rule_name="head rule")
        self.assertEqual(code, 0)
        self.assertIn("no 'masthead rule' shape", out)


class ExportRescueTest(unittest.TestCase):
    """The export must survive the MCP task limit by taking the exporter's render.

    Docker is mocked: `compose` is replaced, so these tests prove the decision
    logic (which file is accepted, what happens on mismatch or silence), not
    that this machine's compose file is right.
    """

    LOCAL = "http://localhost:9001/mcp?userToken=t"
    REMOTE = "https://design.example.test/mcp?userToken=t"

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
            self.eb.export_png(self.LOCAL, self.info, self.target, wait=1, poll=0.01, provenance=note)
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
            self.eb.export_png(self.LOCAL, self.info, self.target, wait=2, poll=0.01, provenance=note)
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
                self.eb.export_png(self.LOCAL, self.info, self.target, wait=0.2, poll=0.01)
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

        with mock.patch.object(export_rescue, "load_url", lambda: self.LOCAL), \
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

        with mock.patch.object(export_rescue, "load_url", lambda: self.LOCAL), \
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
                self.eb.export_png(self.LOCAL, self.info, self.target, wait=0.15, poll=0.01)
        self.assertIn("within 0.15s", str(ctx.exception))
        self.assertIn("bridge down", str(ctx.exception))

    def test_already_seen_files_are_not_accepted(self):
        self._write_png(1440, 4464)
        self.listing = ["penpot.resource.png.old"]
        with mock.patch.object(self.eb, "call_tool", lambda *a, **k: self._timeout_result()), \
                mock.patch.object(self.eb, "exporter_renders", lambda: list(self.listing)), \
                mock.patch.object(self.eb, "compose", self._fake_compose()):
            with self.assertRaises(self.eb.McpError):
                self.eb.export_png(self.LOCAL, self.info, self.target, wait=0.15, poll=0.01)
        # the render existed before the export fired: it belongs to an earlier call
        self.assertFalse(self.target.exists())

    def test_only_loopback_endpoints_get_the_exporter_fallback(self):
        self.assertTrue(self.eb.is_local_endpoint("http://localhost:9001/mcp?userToken=t"))
        self.assertTrue(self.eb.is_local_endpoint("http://127.0.0.1:9001/mcp?userToken=t"))
        self.assertTrue(self.eb.is_local_endpoint("http://[::1]:9001/mcp?userToken=t"))
        self.assertFalse(self.eb.is_local_endpoint(self.REMOTE))
        self.assertFalse(self.eb.is_local_endpoint("http://localhost.example.test/mcp"))

    def test_a_remote_bridge_failure_never_calls_compose(self):
        """The hosted instance has no exporter container here: no compose, no wait."""
        self.listing = ["penpot.resource.png.fresh"]
        with mock.patch.object(self.eb, "call_tool", lambda *a, **k: self._timeout_result()), \
                mock.patch.object(self.eb, "exporter_renders",
                                  lambda: self.fail("remote endpoint must not read the exporter")), \
                mock.patch.object(self.eb, "compose",
                                  lambda *a: self.fail("remote endpoint must not call compose")):
            with self.assertRaises(self.eb.McpError) as ctx:
                self.eb.export_png(self.REMOTE, self.info, self.target, wait=5, poll=0.01)
        self.assertIn("loopback-only", str(ctx.exception))
        self.assertIn("timed out after 120 seconds", str(ctx.exception))
        self.assertFalse(self.target.exists())

    def test_a_remote_bridge_render_is_written(self):
        data = self._write_png(1440, 4464)
        result = {"result": {"content": [{"type": "image", "data": base64.b64encode(data).decode()}]}}
        with mock.patch.object(self.eb, "call_tool", lambda *a, **k: result), \
                mock.patch.object(self.eb, "compose",
                                  lambda *a: self.fail("remote endpoint must not call compose")):
            note: list[str] = []
            self.eb.export_png(self.REMOTE, self.info, self.target, wait=1, poll=0.01,
                               provenance=note)
        self.assertEqual(self.eb.png_size(self.target), (1440, 4464))
        self.assertTrue(note[0].startswith("bridge "), note)


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




class ContrastCollectorTest(unittest.TestCase):
    """The COLLECT node walk must read Penpot's null opacity as "unset".

    Penpot returns `opacity: null` for an untouched shape and `fillOpacity: 1`
    for a painted fill. `Number(null)` is 0, so a naive coercion turned every
    text into "translucent (opacity 0)" and the audit checked nothing on the
    live file (2026-11-03). These cases run the shipped collector source in
    node against a stub page, then classify the result.
    """

    def _collect(self, shapes):
        if not shutil.which("node"):
            self.skipTest("node is required for the collector contract test")
        source = contrast_audit.COLLECT.replace("__PAGE__", json.dumps("P"))
        harness = (
            "const COLLECT = " + json.dumps(source) + ";\n"
            "const shapes = " + json.dumps(shapes) + ";\n"
            "const penpot = { currentFile: { pages: [{ name: 'P', root: { children: shapes } }] } };\n"
            "const result = new Function('penpot', COLLECT)(penpot);\n"
            "process.stdout.write(result);\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "collect.js"
            path.write_text(harness)
            proc = subprocess.run(["node", str(path)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    @staticmethod
    def _shape(name, kind="text", **over):
        shape = {"name": name, "type": kind, "visible": True, "x": 0, "y": 0,
                 "width": 400, "height": 400, "fills": [], "children": []}
        shape.update(over)
        return shape

    @staticmethod
    def _fill(color="#111111", opacity=1):
        return {"fillColor": color, "fillOpacity": opacity}

    def _page(self, text_opacity=None, fill_opacity=1, board_opacity=None):
        text = self._shape("t", opacity=text_opacity,
                           fontSize="16", fontVariantId="regular",
                           textBounds={"x": 10, "y": 10, "width": 100, "height": 20},
                           fills=[self._fill(opacity=fill_opacity)])
        board = self._shape("panel", kind="board", opacity=board_opacity, w=400, h=400,
                            fills=[self._fill("#FFFFFF", 1)], children=[text])
        return [board]

    def test_null_opacity_reads_as_opaque(self):
        data = self._collect(self._page(text_opacity=None, fill_opacity=None, board_opacity=None))
        text = data["texts"][0]
        self.assertEqual(text["fgOpacity"], 1)
        layer = [layer for layer in data["layers"] if layer["name"] == "panel"][0]
        self.assertEqual(layer["opacity"], 1)
        self.assertEqual(contrast_audit.resolve(data)["manual"], [])

    def test_explicit_zero_stays_transparent(self):
        data = self._collect(self._page(text_opacity=0))
        text = data["texts"][0]
        self.assertEqual(text["fgOpacity"], 0)
        report = contrast_audit.resolve(data)
        self.assertEqual(report["checked"], 0)
        self.assertIn("translucent text fill", report["manual"][0]["reason"])

    def test_fractional_opacity_is_preserved(self):
        data = self._collect(self._page(text_opacity=0.72))
        self.assertEqual(data["texts"][0]["fgOpacity"], 0.72)
        report = contrast_audit.resolve(data)
        self.assertEqual(report["checked"], 0)
        self.assertIn("0.72", report["manual"][0]["reason"])

    def test_full_opacity_is_one(self):
        data = self._collect(self._page(text_opacity=1, fill_opacity=1))
        self.assertEqual(data["texts"][0]["fgOpacity"], 1)
        self.assertEqual(contrast_audit.resolve(data)["checked"], 1)

    def test_ancestor_zero_makes_the_text_transparent(self):
        data = self._collect(self._page(board_opacity=0))
        self.assertEqual(data["texts"][0]["fgOpacity"], 0)
        self.assertIn("translucent", contrast_audit.resolve(data)["manual"][0]["reason"])

    def test_unreadable_fill_opacity_is_manual_not_opaque(self):
        data = self._collect(self._page(fill_opacity="abc"))
        report = contrast_audit.resolve(data)
        self.assertEqual(report["checked"], 0)
        self.assertEqual(report["fails"], [])
        self.assertIn("unknown", report["manual"][0]["reason"])

    def test_nan_opacity_in_the_report_is_manual(self):
        """A NaN that still reaches the resolver must not become a solid ratio."""
        data = {"layers": [{"order": 0, "boardId": "b", "board": "board", "kind": "solid",
                            "fill": "#FFFFFF", "opacity": 1, "x": 0, "y": 0, "w": 400, "h": 400,
                            "name": "panel"}],
                "texts": [{"name": "t", "board": "board", "boardId": "b", "order": 1,
                           "fg": "#111111", "fgKind": "solid", "fgPaints": 1,
                           "fgOpacity": float("nan"), "size": 16, "variant": "regular",
                           "cx": 10, "cy": 10}]}
        report = contrast_audit.resolve(data)
        self.assertEqual(report["checked"], 0)
        self.assertIn("unknown text opacity", report["manual"][0]["reason"])

    def test_unreadable_shape_opacity_survives_json_as_manual(self):
        data = self._collect(self._page(text_opacity="abc"))
        self.assertIsNone(data["texts"][0]["fgOpacity"])
        report = contrast_audit.resolve(data)
        self.assertEqual(report["checked"], 0)
        self.assertIn("unknown text opacity", report["manual"][0]["reason"])

    def test_unreadable_ancestor_opacity_survives_json_as_manual(self):
        data = self._collect(self._page(board_opacity="abc"))
        report = contrast_audit.resolve(data)
        self.assertEqual(report["checked"], 0)
        self.assertIn("unknown text opacity", report["manual"][0]["reason"])

    def test_unreadable_sibling_layer_opacity_survives_json_as_manual(self):
        shapes = self._page()
        shapes[0]["children"].insert(0, self._shape(
            "unknown layer", kind="rectangle", opacity="abc",
            fills=[self._fill("#FFFFFF")]))
        data = self._collect(shapes)
        report = contrast_audit.resolve(data)
        self.assertEqual(report["checked"], 0)
        self.assertIn("over layer with unknown opacity", report["manual"][0]["reason"])



class ReflowColumnTest(unittest.TestCase):
    """The shipped lib's canvas reflow, exercised against the real 2026-11-03 fixture.

    `design/ihkd/build/lib.js` holds the function the project runner calls after a
    board's height settles; a rebuild used to leave the following boards where they
    were (07-program's bottom 7336 sat under 08-bildiri's top 7220 — 116px of
    overlap). The fixture below is the live Kongre column at the time of the bug.
    """

    FIXTURE = [
        ("06-kongre", 0, 440, 3840),
        ("07-program", 0, 4480, 2856),
        ("08-bildiri", 0, 7220, 2632),
        ("09-kayit", 0, 10660, 1968),
        ("10-konaklama", 0, 13660, 2400),
        ("07-program-loading", 0, 16300, 1300),
        ("09-kayit-hata", 0, 17840, 1104),
        ("separate column", 2000, 500, 400),
    ]

    def _run(self, board_name="08-bildiri", gap=240):
        if not shutil.which("node"):
            self.skipTest("node is required for the reflow contract test")
        lib = (HERE.parent / "design" / "ihkd" / "build" / "lib.js").read_text()
        boards = [{"type": "board", "name": name, "x": x, "y": y, "height": h}
                  for name, x, y, h in self.FIXTURE]
        harness = (
            "const lib = " + json.dumps(lib) + ";\n"
            "const storage = { H: { version: 'test' } };\n"
            "const boards = " + json.dumps(boards) + ";\n"
            "const penpot = { currentFile: { pages: [{ name: 'P', root: { children: boards } }] } };\n"
            "const IK = new Function('storage', 'penpot', lib + '\\nreturn storage.IK;')(storage, penpot);\n"
            f"const first = IK.reflowColumn('P', {json.dumps(board_name)}, {gap});\n"
            f"const second = IK.reflowColumn('P', {json.dumps(board_name)}, {gap});\n"
            "process.stdout.write(JSON.stringify({ first, second, boards }));\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "reflow.js"
            path.write_text(harness)
            proc = subprocess.run(["node", str(path)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)

    def test_overlapping_followers_are_moved_to_the_project_gap(self):
        data = self._run()
        moves = {m["name"]: (m["from"], m["to"]) for m in data["first"]["moves"]}
        self.assertEqual(moves, {"07-program": (4480, 4520), "08-bildiri": (7220, 7616)},
                         "the 200px gap above 07 and the 116px overlap below it are both repaired")
        bounds = {b["name"]: b for b in data["boards"]}
        self.assertEqual(bounds["08-bildiri"]["y"] - (bounds["07-program"]["y"] + 2856), 240)
        self.assertGreaterEqual(bounds["09-kayit"]["y"] - (bounds["08-bildiri"]["y"] + 2632), 240)

    def test_second_run_is_a_no_op(self):
        data = self._run()
        self.assertEqual(data["second"]["moves"], [])

    def test_untouched_neighbours_keep_their_positions(self):
        data = self._run()
        before = {name: (x, y, h) for name, x, y, h in self.FIXTURE}
        after = {b["name"]: (b["x"], b["y"], b["height"]) for b in data["boards"]}
        for name in ("06-kongre", "09-kayit", "10-konaklama",
                     "07-program-loading", "09-kayit-hata", "separate column"):
            self.assertEqual(after[name], before[name], f"{name} must not move")
        self.assertEqual(after["06-kongre"][2], before["06-kongre"][2], "no height may change")

    def test_other_column_is_not_linearised(self):
        data = self._run(board_name="separate column")
        self.assertEqual(data["first"]["moves"], [])
        self.assertEqual(data["boards"][-1]["y"], 500)

if __name__ == "__main__":
    unittest.main()
