"""Тесты scripts/configure-jev.sh (шаг make install). Ответы подаются в stdin.

Запуск из корня репозитория: python3 -m unittest discover -s tests/orchestrate -v
"""

import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_jev import KEY, MODELS, FakeApi, clean_env

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "configure-jev.sh"
JEV_PY = REPO / "skills" / "orchestrate" / "scripts" / "jev.py"


class ConfigureJev(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.env_file = self.dir / ".env"

    def tearDown(self):
        self._tmp.cleanup()

    def git_init(self):
        subprocess.run(["git", "init", "-q", str(self.dir)], check=True)

    def run_script(self, answers, jev_py=None):
        args = ["sh", str(SCRIPT), str(self.dir)] + ([str(jev_py)] if jev_py else [])
        proc = subprocess.run(args, input="\n".join(answers) + "\n", capture_output=True,
                              text=True, timeout=60, env=clean_env())
        return proc.returncode, proc.stdout + proc.stderr

    def test_decline_writes_nothing(self):
        code, out = self.run_script(["n"])
        self.assertEqual(code, 0)
        self.assertFalse(self.env_file.exists())

    def test_defaults_and_key_are_written_privately(self):
        self.git_init()
        code, out = self.run_script(["y", "", "", KEY, ""])
        self.assertEqual(code, 0, out)
        text = self.env_file.read_text()
        self.assertIn("JEV_AI_BASE_URL=https://jev-ai.pro/api\n", text)
        self.assertIn("JEV_AI_MODEL=jev-latest\n", text)
        self.assertIn("JEV_AI_API_KEY=%s\n" % KEY, text)
        self.assertEqual(stat.S_IMODE(self.env_file.stat().st_mode), 0o600)
        self.assertNotIn(KEY, out)
        self.assertIn(".env", (self.dir / ".gitignore").read_text().splitlines())
        self.assertEqual([p.name for p in self.dir.glob(".env.jev.*")], [])

    def test_other_lines_kept_and_old_jev_lines_replaced(self):
        self.env_file.write_text("OTHER=1\nexport JEV_AI_API_KEY=old\nJEV_AI_MODEL=x\nLAST=2")
        code, out = self.run_script(["y", "y", "https://api.typesafe.ai/", "jev-1.14.0", KEY])
        self.assertEqual(code, 0, out)
        lines = self.env_file.read_text().splitlines()
        self.assertIn("OTHER=1", lines)
        self.assertIn("LAST=2", lines)
        self.assertNotIn("export JEV_AI_API_KEY=old", lines)
        self.assertNotIn("JEV_AI_MODEL=x", lines)
        self.assertIn("JEV_AI_BASE_URL=https://api.typesafe.ai", lines)
        self.assertIn("JEV_AI_MODEL=jev-1.14.0", lines)

    def test_existing_key_kept_when_replacement_declined(self):
        original = "JEV_AI_API_KEY=old\n"
        self.env_file.write_text(original)
        code, out = self.run_script(["y", "n"])
        self.assertEqual(code, 0, out)
        self.assertEqual(self.env_file.read_text(), original)

    def test_tracked_env_file_is_refused(self):
        self.git_init()
        self.env_file.write_text("A=1\n")
        subprocess.run(["git", "-C", str(self.dir), "add", ".env"], check=True)
        code, out = self.run_script(["y", "", "", KEY])
        self.assertEqual(code, 0)
        self.assertEqual(self.env_file.read_text(), "A=1\n")
        self.assertIn("отслеживается git", out)

    def test_plain_http_remote_url_is_asked_again(self):
        code, out = self.run_script(["y", "http://example.com/api", "", "", KEY])
        self.assertEqual(code, 0, out)
        self.assertIn("Нужен адрес https://", out)
        self.assertIn("JEV_AI_BASE_URL=https://jev-ai.pro/api", self.env_file.read_text())

    def test_key_with_space_is_not_written(self):
        code, out = self.run_script(["y", "", "", "bad key"])
        self.assertEqual(code, 0)
        self.assertFalse(self.env_file.exists())

    def test_key_with_shell_metacharacters_is_not_written(self):
        for bad in ("abc;rm", "a&b", "a|b", "a(b)", "a>b"):
            code, out = self.run_script(["y", "", "", bad])
            self.assertFalse(self.env_file.exists(), bad)

    def test_empty_key_cancels(self):
        code, out = self.run_script(["y", "", "", ""])
        self.assertFalse(self.env_file.exists())

    def test_check_runs_against_api_without_printing_key(self):
        fake = FakeApi([(200, MODELS)])
        self.addCleanup(fake.close)
        code, out = self.run_script(["y", fake.url, "", KEY, "y"], jev_py=JEV_PY)
        self.assertEqual(code, 0, out)
        self.assertIn("jev-1.14.0", out)
        self.assertIn("Jev отвечает", out)
        self.assertNotIn(KEY, out)
        self.assertEqual(fake.requests[0]["auth"], "Bearer " + KEY)


if __name__ == "__main__":
    unittest.main()
