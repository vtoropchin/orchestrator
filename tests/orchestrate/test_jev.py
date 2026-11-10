"""Тесты scripts/jev.py пакета orchestrate. Без внешней сети: сохранённые ответы
(--response-file) и локальный HTTP-сервер на 127.0.0.1.

Запуск из корня репозитория: python3 -m unittest discover -s tests/orchestrate -v
"""

import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "skills" / "orchestrate" / "scripts" / "jev.py"
KEY = "test-secret-key-0123456789"
ENV_NAMES = (
    "JEV_AI_API_KEY", "JEV_AI_BASE_URL", "JEV_AI_MODEL",
    "TYPESAFE_API_KEY", "TYPESAFE_BASE_URL", "TYPESAFE_DEFAULT_MODEL",
)


def clean_env(**extra):
    env = {k: v for k, v in os.environ.items() if k not in ENV_NAMES}
    env["JEV_AI_RETRY_DELAYS"] = "0,0"
    # Локальный сервер не должен идти через прокси среды.
    env["NO_PROXY"] = "127.0.0.1,localhost"
    env["no_proxy"] = "127.0.0.1,localhost"
    env.update(extra)
    return env


def run(args, cwd, env=None, stdin=None):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd, env=env or clean_env(), input=stdin,
        capture_output=True, text=True, timeout=60,
    )
    out = json.loads(proc.stdout) if proc.stdout.strip() else None
    return proc.returncode, out, proc.stdout + proc.stderr


def size_answer(p0, p1, p2, p3):
    probs = {"0": p0, "1": p1, "2": p2, "3": p3}
    score = sum(int(k) * v for k, v in probs.items())
    return {"type": "score", "score": score, "confidence": 0.9, "probabilities": probs}


def noul(p):
    return {"type": "noul", "noul": p}


def calibrate_response(size=(0.6, 0.35, 0.04, 0.01), **nouls):
    answers = {"size": size_answer(*size)}
    for name in ("ambiguous", "design_choice", "auth", "secrets",
                 "external_input", "migration", "public_contract"):
        answers[name] = noul(nouls.get(name, 0.05))
    return {"model": "jev-1.14.0", "answers": answers,
            "usage": {"input_tokens": 120, "output_tokens": 0}}


def repair_response(cause, p):
    labels = ["brief_gap", "environment", "permissions", "missing_data", "reasoning_error"]
    rest = (1 - p) / (len(labels) - 1)
    probs = {label: (p if label == cause else rest) for label in labels}
    return {"model": "jev-1.14.0",
            "answers": {"cause": {"type": "choice", "choice": cause,
                                  "confidence": p, "probabilities": probs}},
            "usage": {"input_tokens": 80, "output_tokens": 0}}


class Tmp(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, data):
        path = self.dir / name
        path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
        return path

    def calibrate(self, state, response):
        s = self.write("state.json", state)
        r = self.write("response.json", response)
        return run(["calibrate", "--state", str(s), "--response-file", str(r)], self.dir)


BASE_STATE = {
    "role": "worker",
    "goal": "Добавить поле email в форму профиля",
    "acceptance_criteria": ["поле сохраняется"],
    "planned_paths": ["src/profile/form.py"],
    "writes_code": True,
    "review_md_risk": "low",
}


class CalibrateTable(Tmp):
    def test_small_clear_code_task_gets_coding(self):
        code, out, _ = self.calibrate(BASE_STATE, calibrate_response())
        self.assertEqual(code, 0)
        self.assertEqual(out["profile"], "coding")
        self.assertIn("writes_code_floor", out["rules"])

    def test_small_read_only_fact_finding_gets_light(self):
        state = dict(BASE_STATE, role="scout", writes_code=False)
        code, out, _ = self.calibrate(state, calibrate_response())
        self.assertEqual(code, 0)
        self.assertEqual(out["profile"], "light")

    def test_large_task_for_lead_gets_top(self):
        state = dict(BASE_STATE, role="dev-lead")
        code, out, _ = self.calibrate(state, calibrate_response(size=(0.2, 0.4, 0.3, 0.1)))
        self.assertEqual(code, 0)
        self.assertEqual(out["profile"], "top")
        self.assertIn("large_or_open", out["rules"])

    def test_large_task_for_worker_stays_coding(self):
        code, out, _ = self.calibrate(BASE_STATE, calibrate_response(size=(0.1, 0.3, 0.5, 0.1)))
        self.assertEqual(out["profile"], "coding")

    def test_open_question_for_read_only_scout_gets_coding(self):
        state = dict(BASE_STATE, role="scout", writes_code=False)
        code, out, _ = self.calibrate(state, calibrate_response(design_choice=0.5))
        self.assertEqual(out["profile"], "coding")

    def test_risk_signal_yes_gets_top_even_for_scout(self):
        state = dict(BASE_STATE, role="scout", writes_code=False)
        code, out, _ = self.calibrate(state, calibrate_response(secrets=0.9))
        self.assertEqual(out["profile"], "top")
        self.assertIn("risk_signal:secrets", out["rules"])

    def test_unclear_risk_is_treated_as_high(self):
        code, out, _ = self.calibrate(BASE_STATE, calibrate_response(migration=0.5))
        self.assertEqual(out["profile"], "top")
        self.assertIn("risk_unclear:migration", out["rules"])

    def test_review_md_high_floor_is_never_lowered(self):
        state = dict(BASE_STATE, review_md_risk="high")
        code, out, _ = self.calibrate(state, calibrate_response())
        self.assertEqual(out["profile"], "top")
        self.assertIn("review_md_high_floor", out["rules"])

    def test_unknown_review_risk_is_treated_as_high(self):
        state = dict(BASE_STATE, review_md_risk="unknown")
        code, out, _ = self.calibrate(state, calibrate_response())
        self.assertEqual(out["profile"], "top")

    def test_verifier_not_weaker_than_author(self):
        state = dict(BASE_STATE, role="verifier", author_profile="top")
        code, out, _ = self.calibrate(state, calibrate_response())
        self.assertEqual(out["profile"], "top")
        self.assertIn("verifier_not_below_author", out["rules"])

    def test_size_without_all_levels_is_error_not_small(self):
        response = calibrate_response()
        response["answers"]["size"]["probabilities"] = {"0": 0.9, "1": 0.1}
        code, out, _ = self.calibrate(dict(BASE_STATE, role="dev-lead"), response)
        self.assertEqual(code, 4)
        self.assertEqual(out["error"], "bad_response")

    def test_output_keeps_judgments_for_audit(self):
        code, out, _ = self.calibrate(BASE_STATE, calibrate_response(auth=0.2))
        self.assertAlmostEqual(out["judgments"]["auth"]["p"], 0.2)
        self.assertEqual(out["judgments"]["auth"]["verdict"], "no")
        self.assertIn("p_large", out["judgments"]["size"])
        self.assertEqual(out["model"], "jev-1.14.0")


class CalibrateInput(Tmp):
    def test_missing_role_is_input_error(self):
        state = {k: v for k, v in BASE_STATE.items() if k != "role"}
        code, out, _ = self.calibrate(state, calibrate_response())
        self.assertEqual(code, 2)
        self.assertEqual(out["error"], "bad_input")

    def test_unknown_role_is_input_error(self):
        code, out, _ = self.calibrate(dict(BASE_STATE, role="boss"), calibrate_response())
        self.assertEqual(code, 2)

    def test_oversized_state_is_rejected_before_sending(self):
        code, out, _ = self.calibrate(dict(BASE_STATE, goal="x" * 70000), calibrate_response())
        self.assertEqual(code, 2)
        self.assertEqual(out["error"], "state_too_large")

    def test_malformed_response_is_error_not_answer(self):
        code, out, _ = self.calibrate(BASE_STATE, {"model": "jev", "answers": {}})
        self.assertEqual(code, 4)
        self.assertEqual(out["error"], "bad_response")

    def test_paths_must_be_list_of_strings(self):
        code, out, _ = self.calibrate(dict(BASE_STATE, planned_paths="src/a.py"),
                                      calibrate_response())
        self.assertEqual(code, 2)

    def test_state_from_stdin(self):
        r = self.write("response.json", calibrate_response())
        code, out, _ = run(["calibrate", "--state", "-", "--response-file", str(r)],
                           self.dir, stdin=json.dumps(BASE_STATE))
        self.assertEqual(code, 0)
        self.assertEqual(out["profile"], "coding")


class RepairCause(Tmp):
    STATE = {"failure_report": "тест падает: неверно считается скидка",
             "check_output": "FAILED test_discount", "failed_repairs": 2,
             "current_profile": "coding"}

    def repair(self, state, response):
        s = self.write("state.json", state)
        r = self.write("response.json", response)
        return run(["repair-cause", "--state", str(s), "--response-file", str(r)], self.dir)

    def test_reasoning_error_after_two_repairs_escalates(self):
        code, out, _ = self.repair(self.STATE, repair_response("reasoning_error", 0.8))
        self.assertEqual(code, 0)
        self.assertEqual(out["action"], "escalate")
        self.assertEqual(out["target_profile"], "top")

    def test_reasoning_error_after_one_repair_is_parent_decision(self):
        state = dict(self.STATE, failed_repairs=1)
        code, out, _ = self.repair(state, repair_response("reasoning_error", 0.8))
        self.assertEqual(out["action"], "parent_decides")

    def test_failed_repairs_must_be_non_negative_int(self):
        for bad in (True, -1, "2"):
            code, out, _ = self.repair(dict(self.STATE, failed_repairs=bad),
                                       repair_response("reasoning_error", 0.8))
            self.assertEqual(code, 2, bad)

    def test_environment_is_blocker_not_escalation(self):
        code, out, _ = self.repair(self.STATE, repair_response("environment", 0.85))
        self.assertEqual(out["action"], "blocker")
        self.assertIsNone(out["target_profile"])

    def test_uncertain_cause_is_parent_decision(self):
        code, out, _ = self.repair(self.STATE, repair_response("reasoning_error", 0.5))
        self.assertEqual(out["action"], "parent_decides")

    def test_top_profile_has_nowhere_to_escalate(self):
        state = dict(self.STATE, current_profile="top")
        code, out, _ = self.repair(state, repair_response("reasoning_error", 0.9))
        self.assertEqual(out["action"], "parent_decides")


class FakeApi:
    """Локальный сервер: отдаёт заданные ответы по очереди и запоминает запросы."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []
        api = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def _reply(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                api.requests.append({"method": self.command, "path": self.path,
                                     "auth": self.headers.get("Authorization"),
                                     "body": body.decode("utf-8")})
                reply = api.replies.pop(0) if api.replies else (500, {})
                status, payload = reply[0], reply[1]
                data = json.dumps(payload).encode()
                self.send_response(status)
                for name, value in (reply[2] if len(reply) > 2 else {}).items():
                    self.send_header(name, value)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            do_GET = _reply
            do_POST = _reply

            def log_message(self, *args):
                pass

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = "http://127.0.0.1:%d/api" % self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


MODELS = {"data": [{"name": "jev-latest", "description": "alias", "release_date": "2026-09-15"},
                   {"name": "jev-1.14.0", "description": "stable", "release_date": "2026-10-20"}]}


class Http(Tmp):
    def api(self, replies):
        fake = FakeApi(replies)
        self.addCleanup(fake.close)
        return fake

    def test_check_reads_key_from_dotenv_and_never_prints_it(self):
        fake = self.api([(200, MODELS)])
        self.write(".env", "# comment\nOTHER=1\nexport JEV_AI_API_KEY=\"%s\"\nJEV_AI_BASE_URL=%s\n"
                   % (KEY, fake.url))
        code, out, raw = run(["check"], self.dir)
        self.assertEqual(code, 0, raw)
        self.assertEqual(out["models"], ["jev-latest", "jev-1.14.0"])
        self.assertEqual(out["host"], "127.0.0.1")
        self.assertEqual(out["key_source"], ".env")
        self.assertEqual(fake.requests[0]["method"], "GET")
        self.assertEqual(fake.requests[0]["path"], "/api/v1/models")
        self.assertEqual(fake.requests[0]["auth"], "Bearer " + KEY)
        self.assertNotIn(KEY, raw)

    def test_process_env_overrides_dotenv(self):
        fake = self.api([(200, MODELS)])
        self.write(".env", "JEV_AI_API_KEY=from-dotenv\nJEV_AI_BASE_URL=%s\n" % fake.url)
        code, out, raw = run(["check"], self.dir, env=clean_env(JEV_AI_API_KEY=KEY))
        self.assertEqual(code, 0, raw)
        self.assertEqual(fake.requests[0]["auth"], "Bearer " + KEY)
        self.assertEqual(out["key_source"], "env")

    def test_calibrate_sends_only_task_text_and_model(self):
        fake = self.api([(200, calibrate_response())])
        self.write(".env", "JEV_AI_API_KEY=%s\nJEV_AI_BASE_URL=%s\nJEV_AI_MODEL=jev-1.14.0\n"
                   % (KEY, fake.url))
        s = self.write("state.json", BASE_STATE)
        code, out, raw = run(["calibrate", "--state", str(s)], self.dir)
        self.assertEqual(code, 0, raw)
        req = fake.requests[0]
        self.assertEqual((req["method"], req["path"]), ("POST", "/api/v1/systemone"))
        body = json.loads(req["body"])
        self.assertEqual(body["model"], "jev-1.14.0")
        self.assertEqual(set(body["state"]["task"]), {"goal", "acceptance_criteria", "planned_paths"})
        self.assertEqual(body["questions"]["size"]["type"], "score")
        self.assertEqual(body["questions"]["secrets"]["type"], "noul")
        self.assertNotIn(KEY, raw)

    def test_retries_server_error_then_succeeds(self):
        fake = self.api([(503, {"error": "busy"}), (200, MODELS)])
        self.write(".env", "JEV_AI_API_KEY=%s\nJEV_AI_BASE_URL=%s\n" % (KEY, fake.url))
        code, out, raw = run(["check"], self.dir)
        self.assertEqual(code, 0, raw)
        self.assertEqual(len(fake.requests), 2)

    def test_server_error_after_retries_is_exit_4(self):
        fake = self.api([(500, {}), (502, {}), (503, {})])
        self.write(".env", "JEV_AI_API_KEY=%s\nJEV_AI_BASE_URL=%s\n" % (KEY, fake.url))
        code, out, raw = run(["check"], self.dir)
        self.assertEqual(code, 4)
        self.assertEqual(out["error"], "unavailable")
        self.assertEqual(len(fake.requests), 3)

    def test_auth_error_is_exit_5_without_key_in_output(self):
        fake = self.api([(401, {"error": "invalid key " + KEY})])
        self.write(".env", "JEV_AI_API_KEY=%s\nJEV_AI_BASE_URL=%s\n" % (KEY, fake.url))
        code, out, raw = run(["check"], self.dir)
        self.assertEqual(code, 5)
        self.assertEqual(out["status"], 401)
        self.assertNotIn(KEY, raw)
        self.assertEqual(len(fake.requests), 1)

    def test_redirect_is_not_followed_and_key_not_forwarded(self):
        other = self.api([(200, MODELS)])
        fake = self.api([(302, {}, {"Location": other.url + "/v1/models"})])
        self.write(".env", "JEV_AI_API_KEY=%s\nJEV_AI_BASE_URL=%s\n" % (KEY, fake.url))
        code, out, raw = run(["check"], self.dir)
        self.assertEqual(code, 5, raw)
        self.assertEqual(out["status"], 302)
        self.assertEqual(other.requests, [])

    def test_rate_limit_is_retried(self):
        fake = self.api([(429, {}), (200, MODELS)])
        self.write(".env", "JEV_AI_API_KEY=%s\nJEV_AI_BASE_URL=%s\n" % (KEY, fake.url))
        code, out, raw = run(["check"], self.dir)
        self.assertEqual(code, 0, raw)

    def test_no_key_is_exit_3(self):
        code, out, _ = run(["check"], self.dir)
        self.assertEqual(code, 3)
        self.assertEqual(out["error"], "not_configured")

    def test_plain_http_to_remote_host_is_refused(self):
        self.write(".env", "JEV_AI_API_KEY=%s\nJEV_AI_BASE_URL=http://example.com/api\n" % KEY)
        code, out, _ = run(["check"], self.dir)
        self.assertEqual(code, 3)
        self.assertEqual(out["error"], "bad_config")

    def test_default_destination_is_jev_ai(self):
        self.write(".env", "JEV_AI_API_KEY=%s\n" % KEY)
        code, out, _ = run(["config"], self.dir)
        self.assertEqual(code, 0)
        self.assertEqual(out["base_url"], "https://jev-ai.pro/api")
        self.assertEqual(out["model"], "jev-latest")
        self.assertEqual(out["provider"], "jev-ai")

    def test_typesafe_key_uses_official_api(self):
        code, out, _ = run(["config"], self.dir, env=clean_env(TYPESAFE_API_KEY=KEY))
        self.assertEqual(out["base_url"], "https://api.typesafe.ai")
        self.assertEqual(out["provider"], "typesafe")

    def test_dotenv_found_from_git_worktree(self):
        main = self.dir / "main"
        main.mkdir()
        git = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(["git", "init", "-q", str(main)], check=True)
        subprocess.run(git + ["-C", str(main), "commit", "-q", "--allow-empty", "-m", "x"],
                       check=True)
        wt = self.dir / "wt"
        subprocess.run(["git", "-C", str(main), "worktree", "add", "-q", str(wt)], check=True)
        (main / ".env").write_text("JEV_AI_API_KEY=%s\n" % KEY, encoding="utf-8")
        code, out, _ = run(["config"], wt)
        self.assertEqual(code, 0)
        self.assertEqual(Path(out["env_file"]).resolve(), (main / ".env").resolve())


if __name__ == "__main__":
    unittest.main()
