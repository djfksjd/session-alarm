import math
import os
import struct
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from unittest import mock


PLUGIN_ROOT = Path(__file__).resolve().parents[1] / "plugins" / "session-alarm"
sys.path.insert(0, str(PLUGIN_ROOT))

from session_alarm.core import (
    ConfigError,
    default_config,
    ensure_sound,
    load_config,
    save_config,
    sound_exists,
)
from session_alarm.custom import (
    CustomSoundError,
    import_custom_sound,
    load_custom_sounds,
    remove_custom_sound,
)


def write_test_wav(path: Path, *, rate: int = 22_050, channels: int = 2) -> None:
    duration = 0.12
    frames = int(rate * duration)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(channels)
        output.setsampwidth(2)
        output.setframerate(rate)
        payload = bytearray()
        for index in range(frames):
            sample = int(10_000 * math.sin(2.0 * math.pi * 440.0 * index / rate))
            for _ in range(channels):
                payload.extend(struct.pack("<h", sample))
        output.writeframes(bytes(payload))


class CustomSoundTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.environment = mock.patch.dict(
            os.environ,
            {"SESSION_ALARM_HOME": str(self.root)},
            clear=False,
        )
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temporary.cleanup()

    def test_import_normalizes_and_registers_pcm_wav(self):
        source = self.root / "My Bell.wav"
        write_test_wav(source)

        metadata = import_custom_sound(
            self.root,
            source,
            name="My Bell",
            requested_id="bell",
        )

        self.assertEqual("custom:bell", metadata["id"])
        self.assertTrue(sound_exists("custom:bell"))
        self.assertIn("custom:bell", load_custom_sounds(self.root))
        with wave.open(metadata["path"], "rb") as imported:
            self.assertEqual(1, imported.getnchannels())
            self.assertEqual(2, imported.getsampwidth())
            self.assertEqual(44_100, imported.getframerate())
            self.assertEqual("NONE", imported.getcomptype())

    def test_custom_sound_can_be_configured_and_volume_cached(self):
        source = self.root / "bell.wav"
        write_test_wav(source, rate=44_100, channels=1)
        import_custom_sound(self.root, source, requested_id="bell")

        config = default_config("en")
        config["sounds"]["complete"] = "custom:bell"
        save_config(config)

        self.assertEqual("custom:bell", load_config()["sounds"]["complete"])
        rendered = ensure_sound("custom:bell", 0.35)
        self.assertTrue(rendered.is_file())
        self.assertEqual("custom-bell.wav", rendered.name)

    def test_remove_deletes_master_and_cached_files(self):
        source = self.root / "bell.wav"
        write_test_wav(source)
        metadata = import_custom_sound(self.root, source, requested_id="bell")
        cached = ensure_sound("custom:bell", 0.5)

        removed = remove_custom_sound(self.root, "custom:bell")

        self.assertEqual("custom:bell", removed["id"])
        self.assertFalse(Path(metadata["path"]).exists())
        self.assertFalse(cached.exists())
        self.assertFalse(sound_exists("custom:bell"))

    def test_non_wav_file_is_rejected(self):
        source = self.root / "clip.mp3"
        source.write_bytes(b"not audio")
        with self.assertRaises(CustomSoundError):
            import_custom_sound(self.root, source)

    def test_malformed_custom_id_cannot_resolve_or_escape_cache(self):
        source = self.root / "bell.wav"
        write_test_wav(source)
        import_custom_sound(self.root, source, requested_id="sound")

        self.assertFalse(sound_exists("custom:../../sound"))
        with self.assertRaises(ConfigError):
            ensure_sound("custom:../../sound", 0.5)


if __name__ == "__main__":
    unittest.main()
