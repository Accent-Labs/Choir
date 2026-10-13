import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


CLI = Path(__file__).resolve().parents[1] / "bin" / "choir"


class ChoirCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "choir home"
        self.log = self.root / "calls"
        self.env = dict(os.environ, PATH=f"{self.root}:{os.environ['PATH']}",
                        CHOIR_HOME=str(self.home), CHOIR_IMAGE="choir:test",
                        CHOIR_RUNTIME="container",
                        CALL_LOG=str(self.log), RUNNING="", EXISTING="", FAIL="")
        container = self.root / "container"
        container.write_text('''#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
with open(os.environ["CALL_LOG"], "a") as log:
    log.write(json.dumps(args) + "\\n")
if args[0] == os.environ["FAIL"]:
    sys.exit(17)
if args[0] in ("list", "ps"):
    print(os.environ["EXISTING" if "--all" in args else "RUNNING"])
''')
        container.chmod(0o755)
        (self.root / "docker").symlink_to(container)

    def run_cli(self, *args, status=0):
        result = subprocess.run([str(CLI), *args], env=self.env,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, status, result.stderr)
        return result

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def agent(self):
        codex = self.home / "agents" / "marketing" / ".codex"
        codex.mkdir(parents=True)
        (codex / "AGENTS.md").write_text("Existing identity\n")

    def test_create_preserves_literal_instructions_and_private_home(self):
        prompt = 'Help with "launches".\nDo not execute $(anything).'
        self.run_cli("create", "marketing", "--instructions", prompt)
        home = self.home / "agents" / "marketing"
        self.assertEqual(home.stat().st_mode & 0o777, 0o700)
        self.assertEqual(self.calls(), [[
            "run", "--rm", "--name", "choir-marketing", "--network", "none",
            "--cap-drop", "ALL", "--mount",
            f"type=bind,source={home},target=/home/worker",
            "--env", f"CHOIR_INSTRUCTIONS={prompt}", "choir:test", "true",
        ]])

    def test_login_and_pair(self):
        self.agent()
        self.run_cli("login", "marketing")
        login = self.calls()[-1]
        self.assertEqual(login[-4:], ["choir:test", "codex", "login", "--device-auth"])
        self.assertIn("--tty", login)
        self.assertIn("--rm", login)
        self.run_cli("pair", "marketing")
        self.assertEqual(self.calls()[-1], ["exec", "choir-marketing", "codex", "remote-control", "pair"])

    def test_start_creates_resumes_or_leaves_running_container(self):
        self.agent()
        self.run_cli("start", "marketing")
        self.assertEqual(self.calls()[-1], [
            "run", "--detach", "--name", "choir-marketing", "--cap-drop", "ALL",
            "--mount", f"type=bind,source={self.home}/agents/marketing,target=/home/worker",
            "choir:test",
        ])
        self.env["EXISTING"] = "choir-marketing"
        self.run_cli("start", "marketing")
        self.assertEqual(self.calls()[-1], ["start", "choir-marketing"])
        self.env["RUNNING"] = "choir-marketing"
        self.run_cli("start", "marketing")
        self.assertEqual(self.calls()[-1], ["list", "--quiet"])

    def test_invalid_input_never_calls_container(self):
        for args in [(), ("delete", "marketing"), ("start", "../outside"),
                     ("start", "-flag"), ("start", "marketing", "extra"),
                     ("create", "marketing", "--instructions", ""),
                     ("create", "marketing", "--unknown", "text"),
                     ("start", "missing")]:
            with self.subTest(args=args):
                self.run_cli(*args, status=1)
        for home in ["relative", "/tmp/comma,path"]:
            self.env["CHOIR_HOME"] = home
            self.run_cli("create", "marketing", "--instructions", "text", status=1)
        self.assertFalse(self.log.exists())

    def test_container_errors_propagate_without_fallback(self):
        self.agent()
        self.env["FAIL"] = "list"
        self.run_cli("start", "marketing", status=17)
        self.assertEqual(self.calls(), [["list", "--quiet"]])
        self.env["FAIL"] = "exec"
        self.run_cli("pair", "marketing", status=17)

    def test_docker_uses_host_user_and_docker_listing(self):
        self.env["CHOIR_RUNTIME"] = "docker"
        if os.getuid() == 0:
            self.run_cli("create", "marketing", "--instructions", "text", status=1)
            self.assertFalse(self.log.exists())
            return
        self.run_cli("create", "marketing", "--instructions", "text")
        self.agent()
        self.run_cli("start", "marketing")
        self.assertIn(["ps", "--format", "{{.Names}}"], self.calls())
        self.assertIn(["ps", "--all", "--format", "{{.Names}}"], self.calls())
        self.run_cli("login", "marketing")
        for args in self.calls():
            if args[0] == "run":
                self.assertEqual(args[args.index("--user") + 1], f"{os.getuid()}:{os.getgid()}")
        self.env["EXISTING"] = "choir-marketing"
        self.run_cli("start", "marketing")
        self.assertEqual(self.calls()[-1], ["start", "choir-marketing"])
        self.env["RUNNING"] = "choir-marketing"
        self.run_cli("start", "marketing")
        self.assertEqual(self.calls()[-1], ["ps", "--format", "{{.Names}}"])
        self.run_cli("pair", "marketing")
        self.assertEqual(self.calls()[-1], ["exec", "choir-marketing", "codex", "remote-control", "pair"])

    def test_unknown_runtime_is_rejected(self):
        self.env["CHOIR_RUNTIME"] = "unknown"
        self.run_cli("create", "marketing", "--instructions", "text", status=1)
        self.assertFalse(self.log.exists())


if __name__ == "__main__":
    unittest.main()
