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

    def run_script(self, answers, jev_py=None, env=None):
        args = ["sh", str(SCRIPT), str(self.dir)] + ([str(jev_py)] if jev_py else [])
        data = answers if isinstance(answers, bytes) else ("\n".join(answers) + "\n").encode()
        proc = subprocess.run(args, input=data, capture_output=True, timeout=60,
                              env=env or clean_env())
        return proc.returncode, (proc.stdout + proc.stderr).decode("utf-8", "replace")

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
        self.env_file.write_text("OTHER=1\nexport JEV_AI_BASE_URL=old\nJEV_AI_MODEL=x\nLAST=2")
        code, out = self.run_script(["y", "https://api.typesafe.ai/", "jev-1.14.0", KEY])
        self.assertEqual(code, 0, out)
        lines = self.env_file.read_text().splitlines()
        self.assertIn("OTHER=1", lines)
        self.assertIn("LAST=2", lines)
        self.assertNotIn("export JEV_AI_BASE_URL=old", lines)
        self.assertNotIn("JEV_AI_MODEL=x", lines)
        self.assertIn("JEV_AI_BASE_URL=https://api.typesafe.ai", lines)
        self.assertIn("JEV_AI_MODEL=jev-1.14.0", lines)

    def test_binary_or_non_utf8_lines_are_kept(self):
        original = b"A=1\n# caf\xe9\nB=\x00x\nJEV_AI_MODEL=old\n"
        self.env_file.write_bytes(original)
        code, out = self.run_script(["y", "", "", KEY])
        self.assertEqual(code, 0, out)
        data = self.env_file.read_bytes()
        for line in (b"A=1\n", b"# caf\xe9\n", b"B=\x00x\n"):
            self.assertIn(line, data)
        self.assertNotIn(b"JEV_AI_MODEL=old", data)

    def test_symlinked_gitignore_is_not_written(self):
        self.git_init()
        outside = Path(self._tmp.name + "-outside")
        outside.write_text("keep\n")
        self.addCleanup(outside.unlink)
        (self.dir / ".gitignore").symlink_to(outside)
        code, out = self.run_script(["y", "", "", KEY, "y"])
        self.assertEqual(code, 0, out)
        self.assertEqual(outside.read_text(), "keep\n")

    def test_env_directory_is_refused(self):
        self.env_file.mkdir()
        code, out = self.run_script(["y", "", "", KEY])
        self.assertEqual(list(self.env_file.iterdir()), [])

    def test_configured_dotenv_asks_nothing_and_changes_nothing(self):
        for line in ("JEV_AI_API_KEY=old-SECRET-123\n", "export JEV_AI_API_KEY='old-SECRET-123'\n",
                     "TYPESAFE_API_KEY=old-SECRET-123\n"):
            for jev_py in (JEV_PY, None):
                self.env_file.write_text("A=1\n" + line)
                code, out = self.run_script([], jev_py=jev_py)
                self.assertEqual(code, 0, out)
                self.assertEqual(self.env_file.read_text(), "A=1\n" + line)
                self.assertIn("уже настроен", out)
                self.assertNotIn("Настроить Jev", out)
                self.assertNotIn("old-SECRET-123", out)

    def test_empty_or_overridden_key_is_not_configured(self):
        for text in ('JEV_AI_API_KEY=""\n', "JEV_AI_API_KEY=''\n",
                     "JEV_AI_API_KEY=real\nJEV_AI_API_KEY=\n"):
            self.env_file.write_text(text)
            code, out = self.run_script(["n"], jev_py=JEV_PY)
            self.assertIn("Настроить Jev", out, text)
        for text in ('JEV_AI_API_KEY=""\n', "JEV_AI_API_KEY=''\n"):
            self.env_file.write_text(text)
            code, out = self.run_script(["n"])
            self.assertIn("Настроить Jev", out, text)

    def test_rejected_config_is_reported_without_questions(self):
        self.env_file.write_text("JEV_AI_API_KEY=k-SECRET\nJEV_AI_BASE_URL=http://evil.example\n")
        code, out = self.run_script([], jev_py=JEV_PY)
        self.assertEqual(code, 0, out)
        self.assertIn("не принята", out)
        self.assertNotIn("Настроить Jev", out)
        self.assertNotIn("k-SECRET", out)

    def test_configured_by_environment_asks_nothing(self):
        code, out = self.run_script([], env=clean_env(JEV_AI_API_KEY=KEY))
        self.assertEqual(code, 0, out)
        self.assertIn("уже настроен", out)
        self.assertFalse(self.env_file.exists())
        self.assertNotIn(KEY, out)

    def test_empty_key_line_is_not_configured(self):
        self.env_file.write_text("JEV_AI_API_KEY=\n")
        code, out = self.run_script(["n"])
        self.assertIn("Настроить Jev", out)

    def test_broken_utf8_answer_does_not_crash(self):
        # Стёртая наполовину кириллица: sed на macOS падал с «illegal byte sequence».
        env = clean_env(LANG="C.UTF-8", LC_ALL="C.UTF-8")
        code, out = self.run_script(b"\xd0y\n", env=env)
        self.assertEqual(code, 0, out)
        self.assertFalse(self.env_file.exists())

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
