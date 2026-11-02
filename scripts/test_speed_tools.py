#!/usr/bin/env python3
"""Offline tests for the speed/diagnosis tools: patch_file, gate, build, timeout.

    python3 -m unittest scripts.test_speed_tools

No network and no Penpot. The helpers cache is proven by running the real
helpers.js in node against a fake `penpot`, so "one token-set resolution per
generation" is measured, not assumed.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gate  # noqa: E402
import patch_file  # noqa: E402
import penpot_exec  # noqa: E402

BUILD_PY = HERE.parent / "design" / "ihkd" / "build" / "build.py"
HELPERS_JS = HERE.parent / ".agents" / "skills" / "penpot-design-system" / "assets" / "helpers.js"


def load_build_module():
    spec = importlib.util.spec_from_file_location("ihkd_build_under_test", BUILD_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PatchFileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def write(self, name: str, text: str) -> pathlib.Path:
        path = self.tmp / name
        path.write_text(text)
        return path

    def run_patch(self, argv: list[str]) -> tuple[int, str]:
        out = io.StringIO()
        code = 0
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            try:
                code = patch_file.main(argv)
            except SystemExit as exc:  # the CLI contract: non-zero exit, no traceback
                code = int(exc.code or 0)
        return code, out.getvalue()

    def test_unique_block_is_replaced_with_backup_and_validation(self):
        target = self.write("mod.py", "a = 1\nb = 2\n")
        code, out = self.run_patch([str(target), "--old", "b = 2", "--new", "b = 3"])
        self.assertEqual(code, 0, out)
        self.assertEqual(target.read_text(), "a = 1\nb = 3\n")
        self.assertEqual((self.tmp / "mod.py.bak").read_text(), "a = 1\nb = 2\n")
        self.assertIn("py_compile", out)

    def test_old_that_appears_twice_fails_without_touching_the_file(self):
        target = self.write("dup.py", "x = 1\nx = 1\n")
        code, out = self.run_patch([str(target), "--old", "x = 1", "--new", "x = 2"])
        self.assertEqual(code, 1)
        self.assertIn("occurs 2 times", out)
        self.assertEqual(target.read_text(), "x = 1\nx = 1\n")
        self.assertFalse((self.tmp / "dup.py.bak").exists())

    def test_missing_old_reports_the_whitespace_hint(self):
        target = self.write("mod.py", "if True:\n    x = 1\n")
        code, out = self.run_patch([str(target), "--old", "if True:\n  x = 1", "--new", "y"])
        self.assertEqual(code, 1)
        self.assertIn("occurs 0 times", out)
        self.assertIn("whitespace", out)

    def test_invalid_python_rolls_back(self):
        target = self.write("mod.py", "a = 1\n")
        code, out = self.run_patch([str(target), "--old", "a = 1", "--new", "a = ("])
        self.assertEqual(code, 1)
        self.assertIn("restored", out)
        self.assertEqual(target.read_text(), "a = 1\n")

    def test_invalid_json_rolls_back(self):
        target = self.write("data.json", '{"a": 1}\n')
        code, out = self.run_patch([str(target), "--old", '"a": 1', "--new", '"a": ,'])
        self.assertEqual(code, 1)
        self.assertEqual(target.read_text(), '{"a": 1}\n')

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_invalid_js_rolls_back(self):
        target = self.write("mod.js", "const a = 1;\n")
        code, out = self.run_patch([str(target), "--old", "const a = 1;", "--new", "const a = ;"])
        self.assertEqual(code, 1)
        self.assertIn("node --check", out)
        self.assertEqual(target.read_text(), "const a = 1;\n")

    def test_old_and_new_from_files_and_stdin(self):
        target = self.write("mod.py", "one\ntwo\n")
        old = self.write("old.txt", "two")
        with mock.patch.object(sys, "stdin", io.StringIO("three")):
            code, out = self.run_patch([str(target), "--old-file", str(old)])
        self.assertEqual(code, 0, out)
        self.assertEqual(target.read_text(), "one\nthree\n")

    def test_multiline_block_replace(self):
        target = self.write("mod.py", "def f():\n    return 1\n\nx = 2\n")
        old = self.write("old.txt", "def f():\n    return 1")
        new = self.write("new.txt", "def f():\n    return 10")
        code, out = self.run_patch([str(target), "--old-file", str(old), "--new-file", str(new)])
        self.assertEqual(code, 0, out)
        self.assertIn("return 10", target.read_text())


class HelpersCacheTest(unittest.TestCase):
    """Runs the real helpers.js in node against a fake plugin API."""

    NS = """
const fs = require("fs");
const source = fs.readFileSync(process.argv[2], "utf8");
const tokens = [
  { type: "color", name: "ink.900", value: "#111111" },
  { type: "color", name: "paper", value: "#FFFFFF" },
];
const sets = [{ name: "ihkd", tokens: tokens, addToken(t) { tokens.push(t); return t; } }];
let reads = 0;
const tokensApi = { sets: [], addSet(o) { const s = { name: o.name, tokens: [], addToken(t) { this.tokens.push(t); return t; } }; sets.push(s); return s; } };
Object.defineProperty(tokensApi, "sets", { get() { reads++; return sets; } });
const penpot = { library: { local: { tokens: tokensApi } }, currentPage: { root: { children: [] } } };
const storage = {};
new Function("penpot", "storage", source)(penpot, storage);
const H = storage.H;
const shape = { name: "perf", fills: [], applyToken() { this.bound = true; } };
for (let i = 0; i < 32; i++) H.apply(shape, "ihkd", "ink.900", ["fill"]);
const afterApply = reads;
const fillsBefore = JSON.parse(JSON.stringify(shape.fills));
const missing = H.apply(shape, "ihkd", "nope", ["fill"]);
const afterMissing = reads;
H.syncTokens("ihkd", [{ type: "color", name: "ink.900", value: "#222222" }]);
H.apply(shape, "ihkd", "ink.900", ["fill"]);
console.log(JSON.stringify({
  version: H.version,
  readsAfter32: afterApply,
  readsAfterMissing: afterMissing,
  readsAfterSync: reads,
  bound: shape.bound === true,
  fillsBefore: fillsBefore,
  fillsAfterSync: shape.fills,
  missingApplied: missing.applied,
}));
"""

    @unittest.skipUnless(shutil.which("node"), "node is not installed")
    def test_one_set_read_per_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = pathlib.Path(tmp) / "probe.js"
            script.write_text(self.NS)
            proc = subprocess.run(["node", str(script), str(HELPERS_JS)],
                                  capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(data["version"], "1.5.0")
        self.assertEqual(data["readsAfter32"], 1, "32 bindings must resolve the set once")
        self.assertEqual(data["readsAfterMissing"], 1, "a missing token must reuse the cache")
        self.assertEqual(data["readsAfterSync"], 3, "syncTokens must invalidate and re-add")
        self.assertTrue(data["bound"])
        self.assertEqual(data["fillsBefore"], [{"fillColor": "#111111", "fillOpacity": 1}])
        self.assertEqual(data["fillsAfterSync"], [{"fillColor": "#222222", "fillOpacity": 1}])
        self.assertFalse(data["missingApplied"])


class TimeoutTest(unittest.TestCase):
    def test_default_and_env_override(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PENPOT_HTTP_TIMEOUT", None)
            self.assertEqual(penpot_exec.http_timeout(), 240.0)
            os.environ["PENPOT_HTTP_TIMEOUT"] = "90"
            self.assertEqual(penpot_exec.http_timeout(), 90.0)
            os.environ["PENPOT_HTTP_TIMEOUT"] = "soon"
            with self.assertRaises(penpot_exec.McpError):
                penpot_exec.http_timeout()

    def test_timeout_is_not_retried_and_says_so(self):
        calls = []

        def boom(req, timeout):
            calls.append(timeout)
            raise TimeoutError("timed out")

        with mock.patch.object(penpot_exec.urllib.request, "urlopen", boom):
            with self.assertRaises(penpot_exec.TaskTimeout) as ctx:
                penpot_exec.post("http://example.invalid/mcp", {"jsonrpc": "2.0"})
        self.assertEqual(len(calls), 1, "a timed-out call must not be retried")
        self.assertIn("may still be running", str(ctx.exception))
        self.assertTrue(issubclass(penpot_exec.TaskTimeout, penpot_exec.McpError))


class GateTest(unittest.TestCase):
    def test_resolve_board_by_number_and_name(self):
        screens = {"screen-01": ("Kurumsal", "01-ana-sayfa"), "screen-19": ("Üyelik", "19-giris")}
        self.assertEqual(gate.resolve_board("01", screens), ("Kurumsal", "01-ana-sayfa"))
        self.assertEqual(gate.resolve_board("19", screens), ("Üyelik", "19-giris"))
        self.assertEqual(gate.resolve_board("19-giris", screens), ("Üyelik", "19-giris"))
        self.assertIsNone(gate.resolve_board("99", screens))

    def test_load_screens_reads_the_project_build_table(self):
        screens = gate.load_screens(BUILD_PY)
        self.assertEqual(screens["screen-19"], ("Üyelik", "19-giris"))

    def test_run_step_reports_exit_code_and_seconds(self):
        ok = gate.run_step("ok", [sys.executable, "-c", "print('fine')"], 30)
        bad = gate.run_step("bad", [sys.executable, "-c", "raise SystemExit(1)"], 30)
        slow = gate.run_step("slow", [sys.executable, "-c", "import time; time.sleep(5)"], 0.2)
        self.assertEqual((ok["code"], bad["code"], slow["code"]), (0, 1, 2))
        self.assertIn("timed out", slow["output"])
        self.assertGreater(ok["seconds"], 0)

    def test_export_window_outlives_the_mcp_task_limit(self):
        self.assertGreater(gate.export_timeout(300), gate.EXPORT_WAIT_S)
        self.assertEqual(gate.export_timeout(10), gate.EXPORT_WAIT_S + 60)

    def test_crop_reads_the_exported_file_and_is_skipped_without_one(self):
        """A second live export in the crop step is the double timeout this gate avoids."""
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp) / "proj"
            (project / "build").mkdir(parents=True)
            (project / "build" / "build.py").write_text(
                'SCREENS = {"screen-01": ("Kurumsal", "01-ana-sayfa")}\n')
            seen: list[tuple[str, list[str]]] = []

            def fake_step(label, argv, timeout):
                seen.append((label, list(argv)))
                if label.startswith("export_board") and not self.export_fails:
                    shots = project / "shots"
                    shots.mkdir(parents=True, exist_ok=True)
                    (shots / "01-ana-sayfa.png").write_bytes(b"png")
                    return {"step": label, "code": 0, "seconds": 0.0, "output": ""}
                if label.startswith("export_board"):
                    return {"step": label, "code": 2, "seconds": 0.0, "output": "no render appeared"}
                return {"step": label, "code": 0, "seconds": 0.0, "output": ""}

            self.export_fails = False
            with mock.patch.object(gate, "run_step", fake_step), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(gate.gate(["Kurumsal"], ["01"], project, 30), 0)
            crops = [argv for label, argv in seen if label.startswith("crop_board")]
            self.assertEqual(len(crops), 1)
            self.assertIn("--png", crops[0])
            self.assertIn(str(project / "shots" / "01-ana-sayfa.png"), crops[0])
            self.assertIn("--board", crops[0])

            seen.clear()
            self.export_fails = True
            buf = io.StringIO()
            with mock.patch.object(gate, "run_step", fake_step), contextlib.redirect_stdout(buf):
                self.assertEqual(gate.gate(["Kurumsal"], ["01"], project, 30), 2)
            self.assertEqual([l for l, _ in seen if l.startswith("crop_board")], [],
                             "crop must not run without its render")
            self.assertIn("skipped (export exit 2)", buf.getvalue())

    def test_stage_adds_ignored_design_files_with_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
            (root / ".gitignore").write_text("design/*/\n")
            design = root / "design" / "p"
            design.mkdir(parents=True)
            (design / "f.js").write_text("1;\n")
            (root / "plain.txt").write_text("x\n")
            with mock.patch.object(gate, "ROOT", root):
                self.assertEqual(gate.stage([str(design / "f.js"), str(root / "plain.txt")]), 0)
            listed = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True).stdout
            self.assertIn("design/p/f.js", listed)
            self.assertIn("plain.txt", listed)
            status = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True).stdout
            self.assertIn("A  design/p/f.js", status)
            self.assertIn("A  plain.txt", status)


class BuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.build = load_build_module()

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self._lock = self.build.LOCK
        self.build.LOCK = self.tmp / ".build.lock"
        self.addCleanup(setattr, self.build, "LOCK", self._lock)

    def test_status_probe_does_not_ship_the_library(self):
        code = self.build.status_js("Üyelik", "19-giris")
        self.assertNotIn("const IK = (function", code)
        self.assertIn("storage.IK", code)
        self.assertIn("IK.fit(P, B)", code)
        self.assertIn("__LIB_VERSION__", code)

    def test_lock_blocks_a_second_build_and_stale_lock_is_taken(self):
        self.build.acquire_lock("screen-19")
        self.addCleanup(self.build.release_lock)
        with self.assertRaises(self.build.Locked):
            self.build.acquire_lock("screen-01")
        os.utime(self.build.LOCK, (0, 0))
        self.build.acquire_lock("screen-01")
        self.assertIn("pid=", self.build.LOCK.read_text())

    def test_poll_fit_returns_quiet_and_gives_up_at_the_deadline(self):
        answers = [{"nulls": 3, "fitted": 2, "bars": 0},
                   {"nulls": 1, "fitted": 1, "bars": 0},
                   {"nulls": 0, "fitted": 0, "bars": 0}]
        with mock.patch.object(self.build, "call_execute_code", lambda url, code: answers.pop(0)), \
                mock.patch.object(self.build, "payload", lambda value: value), \
                mock.patch.object(self.build, "POLL_S", 0.01):
            quiet, seconds, passes = self.build.poll_fit("u", "Üyelik", "19-giris", 'const VERSION = "1.0.0";', 5)
        self.assertTrue(quiet)
        self.assertEqual(passes, 3)
        self.assertGreater(seconds, 0)

        with mock.patch.object(self.build, "call_execute_code",
                               lambda url, code: {"nulls": 1, "fitted": 0, "bars": 0}), \
                mock.patch.object(self.build, "payload", lambda value: value), \
                mock.patch.object(self.build, "POLL_S", 0.01):
            quiet, seconds, _ = self.build.poll_fit("u", "Üyelik", "19-giris", 'const VERSION = "1.0.0";', 0.1)
        self.assertFalse(quiet)
        self.assertGreaterEqual(seconds, 0.1)

    def test_timeout_reports_live_state_and_never_reruns_the_screen(self):
        calls = []

        def boom(url, screen, deadline):
            calls.append(screen)
            raise self.build.TimedOut("MCP call timed out after 240s")

        with mock.patch.object(self.build, "load_url", lambda: "url"), \
                mock.patch.object(self.build, "ensure_helpers", lambda url: "1.5.0"), \
                mock.patch.object(self.build, "run", boom), \
                mock.patch.object(self.build, "live_state", lambda url, page, board: '{"nodes": 31}'), \
                contextlib.redirect_stderr(io.StringIO()) as err:
            code = self.build.main(["screen-19"])
        self.assertEqual(code, 2)
        self.assertEqual(calls, ["screen-19"], "a timed-out build must not be re-run")
        self.assertIn("not retrying", err.getvalue())
        self.assertFalse(self.build.LOCK.exists())

    def test_poll_fit_resends_the_library_once_when_storage_is_cold(self):
        seen = []
        lib = 'const IK = (function () { return {}; })();\nconst VERSION = "1.0.0";'

        def call(url, code):
            seen.append(code)
            if "const IK = (function" in code:
                return {"nulls": 0, "fitted": 0, "bars": 0}
            return {"reload": True}

        with mock.patch.object(self.build, "call_execute_code", call), \
                mock.patch.object(self.build, "payload", lambda value: value), \
                mock.patch.object(self.build, "POLL_S", 0.01):
            quiet, _, _ = self.build.poll_fit("u", "Üyelik", "19-giris", lib, 2)
        self.assertTrue(quiet)
        self.assertEqual(len(seen), 2)
        self.assertNotIn("const IK = (function", seen[0])
        self.assertIn("const IK = (function", seen[1])


if __name__ == "__main__":
    unittest.main()
