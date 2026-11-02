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
import time
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


class PluginLockTest(unittest.TestCase):
    """One plugin, one writer: the lock is the gate, pgrep was not."""

    URL = "http://localhost:4401/mcp?userToken=SECRET-TOKEN-1234"

    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        patcher = mock.patch.object(penpot_exec, "LOCK_DIR", self.tmp)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(penpot_exec._HELD.clear)

    def test_lock_file_is_keyed_by_host_and_a_short_hash_not_the_token(self):
        call_lock, session_lock = penpot_exec.lock_paths(self.URL)
        self.assertEqual(call_lock.name, f"plugin-localhost-{penpot_exec.token_tag(self.URL)}.lock")
        self.assertEqual(session_lock.name, f"plugin-localhost-{penpot_exec.token_tag(self.URL)}.session.lock")
        self.assertEqual(call_lock.parent, self.tmp)
        self.assertNotIn("SECRET", str(call_lock) + str(session_lock))
        self.assertEqual(len(penpot_exec.token_tag(self.URL)), 8)
        other = penpot_exec.lock_paths(self.URL.replace("1234", "5678"))[0]
        self.assertNotEqual(other, call_lock, "a different token must not share the lock")

    def test_lock_is_reentrant_in_one_thread_and_counts_depth(self):
        with penpot_exec.plugin_lock(self.URL, write=True):
            with penpot_exec.plugin_lock(self.URL, write=True):  # ensure_helpers -> call
                self.assertEqual(len(penpot_exec._HELD), 2)  # session + call, one fd each
        self.assertEqual(penpot_exec._HELD, {}, "the last release must drop both locks")

    def test_reader_passes_a_build_session_with_a_warning(self):
        err = io.StringIO()
        with mock.patch.object(penpot_exec, "_held_elsewhere", lambda path: True), \
                mock.patch.object(penpot_exec, "_holder_text", lambda path: "pid=4242 t=7s"), \
                contextlib.redirect_stderr(err):
            with penpot_exec.plugin_lock(self.URL, write=False):
                passed = True
        self.assertTrue(passed)
        self.assertIn("build in progress: held by pid=4242 t=7s", err.getvalue())
        self.assertIn("PENPOT_WAIT_BUILD=1", err.getvalue())

    @unittest.skipUnless(shutil.which(sys.executable), "no interpreter")
    def test_a_second_process_is_told_plugin_busy_and_a_patient_one_waits(self):
        holder = (
            "import sys, time\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "import penpot_exec\n"
            "with penpot_exec.plugin_lock(sys.argv[2], write=True):\n"
            "    print('held', flush=True)\n"
            "    time.sleep(float(sys.argv[3]))\n"
        )
        waiter = (
            "import sys\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "import penpot_exec\n"
            "try:\n"
            "    with penpot_exec.plugin_lock(sys.argv[2], write=True):\n"
            "        print('acquired')\n"
            "except penpot_exec.PluginBusy as exc:\n"
            "    print(f'busy: {exc}')\n"
        )
        (self.tmp / "holder.py").write_text(holder)
        (self.tmp / "waiter.py").write_text(waiter)
        env = dict(os.environ, PENPOT_LOCK_DIR=str(self.tmp), PENPOT_LOCK_WAIT="0.4",
                   PENPOT_SESSION_WAIT="0.4")
        with tempfile.TemporaryDirectory() as scripts:
            shutil.copy(HERE / "penpot_exec.py", pathlib.Path(scripts) / "penpot_exec.py")
            hold = subprocess.Popen(
                [sys.executable, str(self.tmp / "holder.py"), scripts, self.URL, "1.2"],
                stdout=subprocess.PIPE, text=True, env=env)
            self.addCleanup(hold.stdout.close)
            self.addCleanup(hold.kill)
            self.assertEqual(hold.stdout.readline().strip(), "held")
            started = time.monotonic()
            quick = subprocess.run([sys.executable, str(self.tmp / "waiter.py"), scripts, self.URL],
                                   capture_output=True, text=True, env=env)
            elapsed = time.monotonic() - started
            self.assertIn(f"plugin busy: held by pid={hold.pid}", quick.stdout)
            self.assertIn("t=", quick.stdout)
            self.assertLess(elapsed, 1.0, "a short wait must give up, not hang")

            patient = subprocess.run(
                [sys.executable, str(self.tmp / "waiter.py"), scripts, self.URL],
                capture_output=True, text=True,
                env=dict(env, PENPOT_LOCK_WAIT="10", PENPOT_SESSION_WAIT="10"))
            self.assertIn("acquired", patient.stdout, patient.stderr)

    def test_expect_page_guards_inside_the_task_and_verifies_after_it(self):
        seen: list[str] = []

        def fake_execute(url, code):
            seen.append(code)
            if "currentPage.name) || null" in code:
                return _mcp_result(json.dumps({"page": "Üyelik"}))
            return _mcp_result("{}")

        with mock.patch.object(penpot_exec, "_execute", fake_execute):
            penpot_exec.call_execute_code(self.URL, "return 1;", expect_page="Üyelik")
        self.assertIn("page-affinity", seen[0])
        self.assertIn(json.dumps("Üyelik"), seen[0])
        self.assertTrue(seen[0].rstrip().endswith("return 1;"), "the guard must precede the snippet")
        self.assertEqual(len(seen), 2, "the page must be read once before and once after")

    def test_a_page_changed_during_the_task_fails_the_call(self):
        def fake_execute(url, code):
            if "currentPage.name) || null" in code:
                return _mcp_result(json.dumps({"page": "Mobil"}))
            return _mcp_result("{}")

        with mock.patch.object(penpot_exec, "_execute", fake_execute):
            with self.assertRaises(penpot_exec.PluginBusy) as ctx:
                penpot_exec.call_execute_code(self.URL, "return 1;", expect_page="Üyelik")
        self.assertIn("another session changed the page", str(ctx.exception))
        self.assertIn("Mobil", str(ctx.exception))

    def test_expect_page_off_sends_the_snippet_unchanged(self):
        seen: list[str] = []

        def fake_execute(url, code):
            seen.append(code)
            return _mcp_result("{}")

        with mock.patch.object(penpot_exec, "_execute", fake_execute):
            penpot_exec.call_execute_code(self.URL, "return 1;")
        self.assertEqual(seen, ["return 1;"])

    def test_cli_read_flag_maps_to_write_false(self):
        seen: list[bool] = []

        def fake_call(url, code, *, write=True, expect_page=None):
            seen.append(write)
            return _mcp_result("{}")

        with mock.patch.object(penpot_exec, "load_url", lambda: self.URL), \
                mock.patch.object(penpot_exec, "call_execute_code", fake_call), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(penpot_exec.main(["--code", "return 1;"]), 0)
            self.assertEqual(penpot_exec.main(["--read", "--code", "return 1;"]), 0)
        self.assertEqual(seen, [True, False])

    def test_read_mode_refuses_to_inject_helpers(self):
        calls: list[str] = []

        def fake_call(url, code, **kwargs):
            calls.append(code)
            return _mcp_result(json.dumps({"version": "1.0.0"}))

        @contextlib.contextmanager
        def fake_lock(*args, **kwargs):
            yield

        with mock.patch.object(penpot_exec, "plugin_lock", fake_lock), \
                mock.patch.object(penpot_exec, "call_execute_code", fake_call):
            with self.assertRaises(penpot_exec.McpError) as ctx:
                penpot_exec.ensure_helpers(self.URL, write=False)
        self.assertIn("refusing to inject during a read", str(ctx.exception))
        self.assertEqual(len(calls), 1, "a read must probe, never send the helper source")

    def test_read_passes_a_held_session_without_waiting(self):
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
        err = io.StringIO()
        with mock.patch.dict(os.environ, {"PENPOT_LOCK_DIR": str(self.tmp),
                                          "PENPOT_SESSION_WAIT": "900",
                                          "PENPOT_LOCK_WAIT": "5"}), \
                mock.patch.object(penpot_exec, "_execute",
                                  lambda url, code: _mcp_result("{}")), \
                contextlib.redirect_stderr(err):
            started = time.monotonic()
            penpot_exec.call_execute_code(self.URL, "return 1;", write=False)
            elapsed = time.monotonic() - started
            self.assertIn("build in progress", err.getvalue())
            self.assertLess(elapsed, 2.0, "a reader must not wait for the writer session")
        with mock.patch.dict(os.environ, {"PENPOT_LOCK_DIR": str(self.tmp),
                                          "PENPOT_SESSION_WAIT": "0.4",
                                          "PENPOT_LOCK_WAIT": "5"}), \
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(penpot_exec.PluginBusy):
                penpot_exec.call_execute_code(self.URL, "return 1;", write=True)


def _mcp_result(text: str) -> dict:
    return {"result": {"content": [{"type": "text", "text": text}]}}


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

    def test_crop_uses_the_spec_primary_cta_when_nodes_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp) / "proj"
            (project / "build").mkdir(parents=True)
            (project / "build" / "build.py").write_text(
                'SCREENS = {"screen-01": ("Kurumsal", "01-ana-sayfa")}\n')
            (project / "ux-spec.json").write_text(json.dumps({"screens": [
                {"board": "01-ana-sayfa", "page": "Kurumsal", "primaryCta": "hero cta"}]}))
            seen: list[tuple[str, list[str]]] = []

            def fake_step(label, argv, timeout):
                seen.append((label, list(argv)))
                if label.startswith("design_lint"):
                    path = pathlib.Path(argv[argv.index("--dump-nodes") + 1])
                    path.write_text("[]")
                if label.startswith("export_board"):
                    shots = project / "shots"
                    shots.mkdir(parents=True, exist_ok=True)
                    (shots / "01-ana-sayfa.png").write_bytes(b"png")
                return {"step": label, "code": 0, "seconds": 0.0, "output": ""}

            with mock.patch.object(gate, "run_step", fake_step), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(gate.gate(["Kurumsal"], ["01"], project, 30), 0)
            crops = [argv for label, argv in seen if label.startswith("crop_board")]
            self.assertEqual(len(crops), 1)
            self.assertIn("--regions", crops[0])
            index = crops[0].index("--primary-action")
            self.assertEqual(crops[0][index + 1], "hero cta")

    def test_an_unconfigured_lint_warning_is_visible_and_not_full_coverage(self):
        def fake_step(label, argv, timeout):
            if label.startswith("design_lint"):
                return {"step": label, "code": 0, "seconds": 0.0,
                        "output": "page: Mobil  shapes: 1  findings: 0 (0 high, 0 medium, "
                                  "0 acknowledged)\nwarning: surface.role is not configured — "
                                  "declare \"surface_white\" and \"surface_alt\" in the project "
                                  "craft-rules.json; the rule was skipped\n"}
            return {"step": label, "code": 0, "seconds": 0.0, "output": ""}

        buf = io.StringIO()
        with mock.patch.object(gate, "run_step", fake_step), contextlib.redirect_stdout(buf):
            code = gate.gate(["Mobil"], [], gate.DEFAULT_PROJECT, 30)
        text = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("surface.role is not configured", text)
        self.assertIn("rule-coverage warning", text)
        self.assertIn("coverage incomplete", text)
        self.assertNotIn("gate: PASS —", text)

    def test_an_invalid_lint_step_is_fail_not_pass(self):
        """design_lint exit 2 on an unmeasured page must never read as PASS."""
        def fake_step(label, argv, timeout):
            if label.startswith("design_lint"):
                return {"step": label, "code": 2, "seconds": 0.0,
                        "output": "error: page not active: textBounds unavailable — open Mobil; "
                                  "findings are NOT valid (7/7 texts unmeasured)",
                        "invalid": gate.INVALID_MARKER in "page not active: textBounds unavailable"}
            return {"step": label, "code": 0, "seconds": 0.0, "output": ""}

        buf = io.StringIO()
        with mock.patch.object(gate, "run_step", fake_step), contextlib.redirect_stdout(buf):
            code = gate.gate(["Mobil"], [], gate.DEFAULT_PROJECT, 30)
        text = buf.getvalue()
        self.assertEqual(code, 2)
        self.assertIn("gate: FAIL (invalid)", text)
        self.assertIn("INVALID", text)
        self.assertNotIn("gate: PASS", text)

    def test_qa_advisory_output_is_visible_and_pass_is_not_clean(self):
        def fake_step(label, argv, timeout):
            if label.startswith("design_qa"):
                return {"step": label, "code": 0, "seconds": 0.0,
                        "output": "findings:\n  - 2 shape(s) use a hard-coded fill: #FFFFFF\n"
                                  "verdict: findings (non-strict) — 1 advisory finding(s); "
                                  "hard-coded fills are not a clean fill count"}
            return {"step": label, "code": 0, "seconds": 0.0, "output": ""}

        buf = io.StringIO()
        with mock.patch.object(gate, "run_step", fake_step), contextlib.redirect_stdout(buf):
            code = gate.gate(["Mobil"], [], gate.DEFAULT_PROJECT, 30)
        text = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("non-fatal QA finding", text)
        self.assertIn("hard-coded fill", text)
        self.assertIn("gate: PASS (", text)
        self.assertIn("not clean", text)

    def test_an_environment_step_still_reports_environment(self):
        def fake_step(label, argv, timeout):
            return {"step": label, "code": 2, "seconds": 0.0, "output": "no plugin connected"}

        buf = io.StringIO()
        with mock.patch.object(gate, "run_step", fake_step), contextlib.redirect_stdout(buf):
            code = gate.gate(["Mobil"], [], gate.DEFAULT_PROJECT, 30)
        self.assertEqual(code, 2)
        self.assertIn("gate: ENVIRONMENT", buf.getvalue())

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
        # build.main takes the real plugin session lock; keep the run hermetic
        patcher = mock.patch.object(penpot_exec, "LOCK_DIR", self.tmp)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(penpot_exec._HELD.clear)

    def test_status_probe_does_not_ship_the_library(self):
        code = self.build.status_js("Üyelik", "19-giris")
        self.assertNotIn("const IK = (function", code)
        self.assertIn("storage.IK", code)
        self.assertIn("K.fit(P, B)", code)
        self.assertIn("__LIB_VERSION__", code)

    def test_lock_blocks_a_second_build_and_stale_lock_is_taken(self):
        self.build.acquire_lock("screen-19")
        self.addCleanup(self.build.release_lock)
        with self.assertRaises(self.build.Locked):
            self.build.acquire_lock("screen-01")
        os.utime(self.build.LOCK, (0, 0))
        self.build.acquire_lock("screen-01")
        self.assertIn("pid=", self.build.LOCK.read_text())

    def test_fit_board_is_quiet_and_gives_up_when_nothing_moves(self):
        answers = [{"nulls": 3, "fitted": 2, "bars": 0, "cards": 0},
                   {"nulls": 1, "fitted": 1, "bars": 0, "cards": 0},
                   {"nulls": 0, "fitted": 0, "bars": 0, "cards": 0},
                   {"nulls": 0, "fitted": 0, "bars": 0, "cards": 0}]
        with mock.patch.object(self.build, "call_execute_code", lambda url, code: answers.pop(0)), \
                mock.patch.object(self.build, "payload", lambda value: value), \
                mock.patch.object(self.build, "POLL_S", 0.001):
            quiet, nulls, names, seconds, passes = self.build.fit_board(
                "u", "Üyelik", "19-giris", 'const VERSION = "1.0.0";', 5)
        self.assertTrue(quiet)
        self.assertEqual(nulls, 0)
        self.assertEqual(passes, 4)
        self.assertGreater(seconds, 0)

        with mock.patch.object(self.build, "call_execute_code",
                               lambda url, code: {"nulls": 1, "fitted": 0, "bars": 0,
                                                  "cards": 0, "nullNames": ["late"]}), \
                mock.patch.object(self.build, "payload", lambda value: value), \
                mock.patch.object(self.build, "POLL_S", 0.001):
            quiet, nulls, names, _, passes = self.build.fit_board(
                "u", "Üyelik", "19-giris", 'const VERSION = "1.0.0";', 5)
        self.assertFalse(quiet)
        self.assertEqual(nulls, 1)
        self.assertEqual(names, ["late"])
        self.assertLessEqual(passes, self.build.FIT_ATTEMPTS)

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
            code, remaining = self.build.main(["screen-19"])
        self.assertEqual(code, 2)
        self.assertEqual(remaining, 0)
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
            quiet, _, _, _, _ = self.build.fit_board("u", "Üyelik", "19-giris", lib, 2)
        self.assertTrue(quiet)
        self.assertEqual(len(seen), 3)
        self.assertNotIn("const IK = (function", seen[0])
        self.assertIn("const IK = (function", seen[1])
        self.assertIn("const IK = (function", seen[2])


if __name__ == "__main__":
    unittest.main()
