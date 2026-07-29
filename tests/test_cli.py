import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins" / "session-alarm" / "scripts" / "session_alarm.py"


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.environment = dict(os.environ)
        self.environment.update(
            {
                "SESSION_ALARM_HOME": self.temporary.name,
                "SESSION_ALARM_DISABLE_AUDIO": "1",
                "SESSION_ALARM_DISABLE_NOTIFICATIONS": "1",
            }
        )

    def tearDown(self):
        self.temporary.cleanup()

    def run_cli(self, *arguments, input_text=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            input=input_text,
            text=True,
            capture_output=True,
            env=self.environment,
            check=False,
        )

    def test_catalog_json_contains_forty_sounds(self):
        result = self.run_cli("catalog", "--json", "--language", "en")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(40, len(json.loads(result.stdout)))

    def test_preview_all_can_play_one_group_in_order(self):
        result = self.run_cli(
            "preview-all",
            "--group",
            "pets",
            "--volume",
            "30",
            "--gap",
            "0",
            "--language",
            "en",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("[01/04] Cat (cat)", result.stdout)
        self.assertIn("[04/04] Puppy (puppy)", result.stdout)
        self.assertIn("Preview complete.", result.stdout)

    def test_noninteractive_configuration_and_status(self):
        result = self.run_cli(
            "configure",
            "--attention",
            "crocodile",
            "--complete",
            "elephant",
            "--error",
            "hyena",
            "--session-end",
            "owl",
            "--volume",
            "55",
            "--notifications",
            "off",
            "--quiet-hours",
            "23:00-07:00",
            "--language",
            "ko",
        )
        self.assertEqual(0, result.returncode, result.stderr)

        status = self.run_cli("status", "--json")
        payload = json.loads(status.stdout)
        self.assertTrue(payload["configured"])
        self.assertEqual("crocodile", payload["config"]["sounds"]["attention"])
        self.assertEqual(0.55, payload["config"]["volume"])

    def test_unconfigured_hook_emits_valid_first_run_json(self):
        payload = json.dumps({"hook_event_name": "SessionStart"})
        result = self.run_cli("hook", "--source", "claude", input_text=payload)
        self.assertEqual(0, result.returncode)
        output = json.loads(result.stdout)
        self.assertEqual(
            "SessionStart",
            output["hookSpecificOutput"]["hookEventName"],
        )

    def test_malformed_hook_input_never_blocks(self):
        result = self.run_cli("hook", "--source", "codex", input_text="{broken")
        self.assertEqual(0, result.returncode)
        self.assertEqual({}, json.loads(result.stdout))

    def test_setup_refuses_noninteractive_input(self):
        result = self.run_cli("setup", input_text="")
        self.assertEqual(2, result.returncode)
        self.assertIn("terminal", result.stderr)

    def test_reset_requires_explicit_confirmation(self):
        result = self.run_cli("reset")
        self.assertEqual(2, result.returncode)


if __name__ == "__main__":
    unittest.main()
