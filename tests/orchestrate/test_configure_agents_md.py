"""Тесты scripts/configure-agents-md.sh (шаг make install). Ответы подаются в stdin.

Запуск из корня репозитория: python3 -m unittest discover -s tests/orchestrate -v
"""

import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "configure-agents-md.sh"
BEGIN = "<!-- skills:orchestrate-models:begin"
END = "<!-- skills:orchestrate-models:end -->"


def block_of(text):
    """Строки от BEGIN до END включительно."""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(BEGIN))
    stop = next(i for i, line in enumerate(lines) if line.startswith(END))
    return lines[start:stop + 1]


class ConfigureAgentsMd(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.file = self.dir / "AGENTS.md"

    def tearDown(self):
        self._tmp.cleanup()

    def run_script(self, answers):
        data = answers if isinstance(answers, bytes) else ("\n".join(answers) + "\n").encode()
        proc = subprocess.run(["sh", str(SCRIPT), str(self.dir)], input=data,
                              capture_output=True, timeout=60)
        return proc.returncode, (proc.stdout + proc.stderr).decode("utf-8", "replace")

    # Новый блок: согласие, две модели, конец списка, «top только эскалацией» — нет.
    NEW = ["y", "deepseek-flash: coding", "deepseek-v4-pro: top", "", "n"]

    def test_decline_writes_nothing(self):
        code, out = self.run_script(["n"])
        self.assertEqual(code, 0, out)
        self.assertFalse(self.file.exists())

    def test_new_file_gets_block(self):
        code, out = self.run_script(self.NEW)
        self.assertEqual(code, 0, out)
        text = self.file.read_text()
        block = block_of(text)
        self.assertIn("## Модели child (orchestrate)", block)
        self.assertIn("- deepseek-flash: coding", block)
        self.assertIn("- deepseek-v4-pro: top", block)
        self.assertNotIn("- top: только эскалация", block)
        self.assertEqual(text.count(BEGIN), 1)
        self.assertEqual(stat.S_IMODE(self.file.stat().st_mode), 0o644)
        self.assertEqual([p.name for p in self.dir.glob(".AGENTS.md.*")], [])

    def test_append_keeps_existing_bytes(self):
        original = b"# Project\r\n\r\nRule \xe9 one"  # CRLF, не-UTF-8, без перевода строки
        self.file.write_bytes(original)
        self.file.chmod(0o640)
        code, out = self.run_script(self.NEW)
        self.assertEqual(code, 0, out)
        data = self.file.read_bytes()
        self.assertTrue(data.startswith(original + b"\n"))
        self.assertIn(b"- deepseek-flash: coding\n", data)
        self.assertEqual(stat.S_IMODE(self.file.stat().st_mode), 0o640)

    def test_reinstall_replaces_block_and_keeps_classes(self):
        self.run_script(self.NEW)
        before = self.file.read_text()
        # Пользователь дописал текст вокруг блока и испортил текст набора внутри него.
        text = "Top text\n\n" + before.replace("## Модели child (orchestrate)",
                                               "## Модели child (orchestrate)\nold managed text") \
            + "\n## После\n\nkeep\n"
        self.file.write_text(text)
        # Обновить — да; оставить классы — Enter (да); эскалация — Enter (как было: нет).
        code, out = self.run_script(["", "", ""])
        self.assertEqual(code, 0, out)
        after = self.file.read_text()
        self.assertTrue(after.startswith("Top text\n\n"))
        self.assertTrue(after.endswith("\n## После\n\nkeep\n"))
        self.assertNotIn("old managed text", after)
        self.assertEqual(block_of(after), block_of(before))
        self.assertEqual(after.count(BEGIN), 1)

    def test_reinstall_can_change_classes_and_escalation(self):
        self.run_script(self.NEW)
        code, out = self.run_script(["y", "n", "deepseek-flash: light", "", "y"])
        self.assertEqual(code, 0, out)
        block = block_of(self.file.read_text())
        self.assertIn("- deepseek-flash: light", block)
        self.assertNotIn("- deepseek-v4-pro: top", block)
        self.assertIn("- top: только эскалация", block)

    def test_unmarked_section_is_adopted(self):
        self.file.write_text("# P\n\n## Модели child (orchestrate)\n\n- deepseek-flash: coding\n"
                             "- top: только эскалация\n\n## Другое\n\nkeep\n")
        code, out = self.run_script(["y", "", ""])
        self.assertEqual(code, 0, out)
        text = self.file.read_text()
        self.assertEqual(text.count("## Модели child"), 1)
        block = block_of(text)
        self.assertIn("- deepseek-flash: coding", block)
        self.assertIn("- top: только эскалация", block)
        self.assertTrue(text.startswith("# P\n\n" + BEGIN))
        self.assertTrue(text.endswith("\n## Другое\n\nkeep\n"))

    def test_backslash_in_project_path_keeps_section(self):
        self.dir = Path(self._tmp.name) / "a\\nb"
        self.dir.mkdir()
        self.file = self.dir / "AGENTS.md"
        self.run_script(self.NEW)
        code, out = self.run_script(["", "", ""])
        self.assertEqual(code, 0, out)
        self.assertIn("- deepseek-flash: coding", block_of(self.file.read_text()))

    def test_adopt_with_own_text_changes_nothing(self):
        text = ("## Модели child (orchestrate)\n\n- deepseek-flash: coding\n"
                "Важно: не использовать b.\n\n## Другое\n")
        self.file.write_text(text)
        code, out = self.run_script(["y", "", ""])
        self.assertEqual(code, 0, out)
        self.assertEqual(self.file.read_text(), text)
        self.assertIn("Важно: не использовать b.", out)

    def test_duplicate_check_is_literal(self):
        code, out = self.run_script(["y", "gpt-411: coding", "gpt-4.1: top", "", "n"])
        self.assertEqual(code, 0, out)
        block = block_of(self.file.read_text())
        self.assertIn("- gpt-411: coding", block)
        self.assertIn("- gpt-4.1: top", block)
        code, out = self.run_script(["y", "n", "a.b: top", "a.b: coding", "", "n"])
        self.assertIn("уже введена", out)

    def test_missing_or_dash_project_dir(self):
        proc = subprocess.run(["sh", str(SCRIPT), str(self.dir / "nope")], input=b"y\n",
                              capture_output=True, timeout=60)
        self.assertEqual(proc.returncode, 0)
        dash = self.dir / "-p"
        dash.mkdir()
        proc = subprocess.run(["sh", str(SCRIPT), "-p"], cwd=self.dir,
                              input="\n".join(self.NEW).encode() + b"\n",
                              capture_output=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("- deepseek-flash: coding", block_of((dash / "AGENTS.md").read_text()))

    def test_fenced_example_is_not_a_section(self):
        text = ("# P\n\n```markdown\n## Модели child (orchestrate)\n- x: top\n```\n\n"
                "## Сборка\n\nmake\n")
        self.file.write_text(text)
        code, out = self.run_script(self.NEW)
        self.assertEqual(code, 0, out)
        after = self.file.read_text()
        self.assertTrue(after.startswith(text + "\n" + BEGIN))
        self.assertEqual(after.count("```"), 2)

    def test_fence_inside_section_blocks_adopt(self):
        text = ("## Модели child (orchestrate)\n\n- a: top\n```sh\n# переключение\n```\n"
                "- b: light\n\n## Другое\n")
        self.file.write_text(text)
        code, out = self.run_script(["y", "", ""])
        self.assertEqual(code, 0, out)
        self.assertEqual(self.file.read_text(), text)

    def test_update_keeps_missing_final_newline(self):
        self.run_script(self.NEW)
        self.file.write_text(self.file.read_text() + "\ntail")
        code, out = self.run_script(["", "", ""])
        self.assertEqual(code, 0, out)
        self.assertTrue(self.file.read_text().endswith(END + "\n\ntail"))

    def test_ids_with_colon_and_brackets(self):
        code, out = self.run_script(["y", "qwen2.5:7b : light", "claude-opus-4-6[1m]: top", "", "n"])
        self.assertEqual(code, 0, out)
        block = block_of(self.file.read_text())
        self.assertIn("- qwen2.5:7b: light", block)
        self.assertIn("- claude-opus-4-6[1m]: top", block)
        code, out = self.run_script(["", "", ""])
        self.assertEqual(block_of(self.file.read_text()), block)

    def test_unparsed_list_line_in_block_changes_nothing(self):
        self.run_script(self.NEW)
        text = self.file.read_text().replace("- deepseek-v4-pro: top",
                                             "- deepseek-v4-pro: top\n- my model: best")
        self.file.write_text(text)
        code, out = self.run_script(["", "", ""])
        self.assertEqual(code, 0, out)
        self.assertEqual(self.file.read_text(), text)
        self.assertIn("my model: best", out)

    def test_broken_markers_change_nothing(self):
        for text in (BEGIN + " -->\n- a: top\n",
                     BEGIN + " -->\n" + END + "\n" + BEGIN + " -->\n" + END + "\n",
                     END + "\n" + BEGIN + " -->\n"):
            self.file.write_text(text)
            code, out = self.run_script(self.NEW)
            self.assertEqual(code, 0, out)
            self.assertEqual(self.file.read_text(), text)
            self.assertIn("маркеры", out)

    def test_symlink_is_not_written(self):
        outside = Path(self._tmp.name + "-outside.md")
        outside.write_text("keep\n")
        self.addCleanup(outside.unlink)
        self.file.symlink_to(outside)
        code, out = self.run_script(self.NEW)
        self.assertEqual(code, 0, out)
        self.assertEqual(outside.read_text(), "keep\n")

    def test_invalid_line_is_asked_again(self):
        code, out = self.run_script(["y", "deepseek flash: fast", "deepseek-flash: coding", "", "n"])
        self.assertEqual(code, 0, out)
        self.assertIn("Формат", out)
        self.assertIn("- deepseek-flash: coding", block_of(self.file.read_text()))

    def test_no_models_writes_nothing(self):
        code, out = self.run_script(["y", ""])
        self.assertEqual(code, 0, out)
        self.assertFalse(self.file.exists())

    def test_interrupted_input_changes_nothing(self):
        self.file.write_text("keep\n")
        code, out = self.run_script(b"y\ndeepseek-flash: coding\n")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.file.read_text(), "keep\n")
        self.assertEqual([p.name for p in self.dir.glob(".AGENTS.md.*")], [])


if __name__ == "__main__":
    unittest.main()
