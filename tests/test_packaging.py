import hashlib
import json
import subprocess
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

    def test_bundled_audio_has_fail_closed_mixed_license_manifest(self):
        sound_dir = PLUGIN / "assets" / "sounds"
        sources = read_json(sound_dir / "sources.json")
        self.assertEqual(2, sources["schema_version"])

        entries = sources["sounds"]
        self.assertEqual(40, len(entries))
        self.assertEqual(40, len({entry["id"] for entry in entries}))
        self.assertEqual(40, len({entry["file"] for entry in entries}))
        self.assertEqual(39, sum(entry["provenance"] == "project_generated" for entry in entries))
        self.assertEqual(1, sum(entry["provenance"] == "verified_asset" for entry in entries))
        for entry in entries:
            with self.subTest(sound=entry["id"]):
                path = sound_dir / entry["file"]
                self.assertTrue(path.is_file())
                self.assertEqual(
                    entry["sha256"],
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                )
                self.assertNotEqual("verified_collection", entry["provenance"])
                if entry["provenance"] == "project_generated":
                    self.assertEqual("MIT", entry["license_name"])
                    self.assertEqual(
                        "plugins/session-alarm/scripts/generate_builtin_sounds.py",
                        entry["generator"],
                    )
                    self.assertTrue(entry["generator_seed"].startswith("session-alarm-v6:"))
                else:
                    self.assertEqual("Pixabay Content License", entry["license_name"])
                    self.assertTrue(entry["source_page"].startswith("https://pixabay.com/"))
                    self.assertNotIn("/search/", entry["source_page"])
                    self.assertTrue(entry["contributor"])
                    self.assertTrue(entry["title"])

    def test_generated_audio_and_manifest_are_reproducible(self):
        result = subprocess.run(
            [
                sys.executable,
                str(PLUGIN / "scripts" / "generate_builtin_sounds.py"),
                "--check",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

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
