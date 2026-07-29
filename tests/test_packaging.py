import hashlib
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

    def test_bundled_audio_has_commercial_license_manifest(self):
        sound_dir = PLUGIN / "assets" / "sounds"
        sources = read_json(sound_dir / "sources.json")
        self.assertEqual("Pixabay Content License", sources["license_name"])
        self.assertEqual(
            "https://pixabay.com/service/license-summary/",
            sources["license_url"],
        )
        self.assertTrue(sources["commercial_use_permitted"])
        self.assertTrue(sources["standalone_redistribution_prohibited"])

        entries = sources["sounds"]
        self.assertEqual(40, len(entries))
        self.assertEqual(40, len({entry["id"] for entry in entries}))
        self.assertEqual(40, len({entry["file"] for entry in entries}))
        for entry in entries:
            with self.subTest(sound=entry["id"]):
                path = sound_dir / entry["file"]
                self.assertTrue(path.is_file())
                self.assertEqual(
                    entry["sha256"],
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                )
                self.assertTrue(entry["source_page"].startswith("https://pixabay.com/"))

    def test_audio_files_exist_only_in_the_licensed_asset_directory(self):
        audio_extensions = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac"}
        found = [
            path
            for path in ROOT.rglob("*")
            if path.is_file() and path.suffix.lower() in audio_extensions
        ]
        self.assertEqual(40, len(found))
        sound_dir = PLUGIN / "assets" / "sounds"
        self.assertTrue(all(path.parent == sound_dir for path in found))

    def test_localized_readmes_exist(self):
        for name in ("README.ko.md", "README.ja.md", "README.zh-CN.md", "README.es.md"):
            with self.subTest(name=name):
                self.assertTrue((ROOT / "docs" / name).is_file())


if __name__ == "__main__":
    unittest.main()
