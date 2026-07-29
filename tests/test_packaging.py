import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "session-alarm"
sys.path.insert(0, str(PLUGIN))

from session_alarm import __version__


def read_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


class PackagingTests(unittest.TestCase):
    def test_manifest_names_and_versions_match(self):
        codex = read_json(PLUGIN / ".codex-plugin" / "plugin.json")
        claude = read_json(PLUGIN / ".claude-plugin" / "plugin.json")
        marketplace = read_json(ROOT / ".claude-plugin" / "marketplace.json")
        self.assertEqual("session-alarm", codex["name"])
        self.assertEqual(codex["name"], claude["name"])
        self.assertEqual(__version__, codex["version"])
        self.assertEqual(__version__, claude["version"])
        self.assertEqual(__version__, marketplace["plugins"][0]["version"])

    def test_marketplace_sources_resolve(self):
        codex = read_json(ROOT / ".agents" / "plugins" / "marketplace.json")
        claude = read_json(ROOT / ".claude-plugin" / "marketplace.json")
        self.assertEqual("./plugins/session-alarm", codex["plugins"][0]["source"]["path"])
        self.assertEqual("./plugins/session-alarm", claude["plugins"][0]["source"])
        self.assertTrue((ROOT / "plugins" / "session-alarm").is_dir())

    def test_required_hook_events_are_declared(self):
        codex = read_json(PLUGIN / "hooks" / "hooks.json")["hooks"]
        claude = read_json(PLUGIN / "hooks" / "claude.json")["hooks"]
        self.assertTrue({"SessionStart", "PermissionRequest", "Stop", "SessionEnd"} <= set(codex))
        self.assertTrue(
            {"SessionStart", "Notification", "Stop", "StopFailure", "SessionEnd"}
            <= set(claude)
        )
        for groups in claude.values():
            for group in groups:
                for hook in group["hooks"]:
                    self.assertEqual("node", hook["command"])
                    self.assertIn("${CLAUDE_PLUGIN_ROOT}/scripts/hook.mjs", hook["args"])

    def test_repository_contains_no_sampled_audio(self):
        audio_extensions = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac"}
        found = [
            path
            for path in ROOT.rglob("*")
            if path.is_file() and path.suffix.lower() in audio_extensions
        ]
        self.assertEqual([], found)

    def test_localized_readmes_exist(self):
        for name in ("README.ko.md", "README.ja.md", "README.zh-CN.md", "README.es.md"):
            with self.subTest(name=name):
                self.assertTrue((ROOT / "docs" / name).is_file())


if __name__ == "__main__":
    unittest.main()
