import datetime as dt
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PLUGIN_ROOT = Path(__file__).resolve().parents[1] / "plugins" / "session-alarm"
sys.path.insert(0, str(PLUGIN_ROOT))

from session_alarm.core import (
    ConfigError,
    default_config,
    event_from_hook,
    is_duplicate,
    load_config,
    notify_event,
    quiet_now,
    run_hook,
    save_config,
    stop_has_error,
    stop_needs_input,
)


class IsolatedStateTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.environment = mock.patch.dict(
            os.environ,
            {
                "SESSION_ALARM_HOME": self.temporary.name,
                "SESSION_ALARM_DISABLE_AUDIO": "1",
                "SESSION_ALARM_DISABLE_NOTIFICATIONS": "1",
                "SESSION_ALARM_LANGUAGE": "en",
            },
            clear=False,
        )
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()


class ConfigurationTests(IsolatedStateTestCase):
    def test_round_trip(self):
        config = default_config("ko")
        config["sounds"]["attention"] = "frog"
        path = save_config(config)
        self.assertTrue(path.exists())
        self.assertEqual("frog", load_config()["sounds"]["attention"])

    def test_retired_sound_is_migrated_to_real_recording(self):
        config = default_config("ko")
        config["sounds"]["attention"] = "crocodile"
        save_config(config)
        self.assertEqual("frog", load_config()["sounds"]["attention"])

    def test_invalid_sound_is_rejected(self):
        config = default_config("en")
        config["sounds"]["complete"] = "famous-meme"
        with self.assertRaises(ConfigError):
            save_config(config)

    def test_save_uses_valid_json(self):
        path = save_config(default_config("en"))
        with path.open(encoding="utf-8") as handle:
            value = json.load(handle)
        self.assertEqual(1, value["schema_version"])

    def test_quiet_hours_cross_midnight(self):
        config = default_config("en")
        config["quiet_hours"] = {
            "enabled": True,
            "start": "22:00",
            "end": "08:00",
        }
        self.assertTrue(quiet_now(config, dt.datetime(2026, 7, 30, 23, 0)))
        self.assertTrue(quiet_now(config, dt.datetime(2026, 7, 30, 7, 59)))
        self.assertFalse(quiet_now(config, dt.datetime(2026, 7, 30, 12, 0)))

    def test_quiet_hours_same_start_and_end_means_all_day(self):
        config = default_config("en")
        config["quiet_hours"] = {
            "enabled": True,
            "start": "09:00",
            "end": "09:00",
        }
        self.assertTrue(quiet_now(config, dt.datetime(2026, 7, 30, 12, 0)))


class EventTests(IsolatedStateTestCase):
    def test_stop_question_needs_input_in_english(self):
        self.assertTrue(stop_needs_input("The build is ready. Which option do you prefer?"))

    def test_stop_question_needs_input_in_korean(self):
        self.assertTrue(stop_needs_input("두 가지 구현이 가능합니다. 어느 것을 선택하시겠어요?"))

    def test_finished_message_is_complete(self):
        self.assertFalse(stop_needs_input("Implemented the feature and all tests pass."))

    def test_failed_message_is_error(self):
        self.assertTrue(stop_has_error("The build failed and I could not complete the task."))
        self.assertEqual(
            "error",
            event_from_hook(
                {
                    "hook_event_name": "Stop",
                    "last_assistant_message": "테스트가 실패하여 작업이 중단되었습니다.",
                }
            ),
        )

    def test_historical_error_in_success_summary_is_not_error(self):
        self.assertFalse(stop_has_error("Fixed the parsing error and all tests now pass."))

    def test_hook_event_mapping(self):
        cases = (
            ({"hook_event_name": "PermissionRequest"}, "attention"),
            ({"hook_event_name": "StopFailure"}, "error"),
            ({"hook_event_name": "SessionEnd"}, "session_end"),
            (
                {
                    "hook_event_name": "Notification",
                    "notification_type": "agent_needs_input",
                },
                "attention",
            ),
            (
                {
                    "hook_event_name": "Notification",
                    "notification_type": "agent_completed",
                },
                "complete",
            ),
            (
                {
                    "hook_event_name": "Stop",
                    "last_assistant_message": "Done.",
                },
                "complete",
            ),
        )
        for payload, expected in cases:
            with self.subTest(payload=payload):
                self.assertEqual(expected, event_from_hook(payload))

    def test_stop_with_background_work_does_not_alarm(self):
        payload = {
            "hook_event_name": "Stop",
            "last_assistant_message": "Waiting.",
            "background_tasks": [{"id": "task-1"}],
        }
        self.assertIsNone(event_from_hook(payload))

    def test_first_run_injects_configuration_context(self):
        result = run_hook({"hook_event_name": "SessionStart"}, "codex")
        context = result["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Session Alarm", context)

    def test_configured_hook_returns_empty_json(self):
        save_config(default_config("en"))
        result = run_hook(
            {
                "hook_event_name": "Stop",
                "last_assistant_message": "Everything is complete.",
            },
            "claude",
        )
        self.assertEqual({}, result)

    def test_notifications_are_deduplicated(self):
        self.assertFalse(is_duplicate("complete", "codex", window_seconds=60))
        self.assertTrue(is_duplicate("complete", "codex", window_seconds=60))
        self.assertFalse(is_duplicate("attention", "codex", window_seconds=60))

    def test_force_notification_works_with_disabled_audio_environment(self):
        config = default_config("en")
        config["desktop_notifications"] = False
        save_config(config)
        played, reason = notify_event("complete", "manual", force=True, config=config)
        self.assertTrue(played)
        self.assertIn("audio disabled", reason)


if __name__ == "__main__":
    unittest.main()
