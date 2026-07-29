import os
import hashlib
import math
import sys
import tempfile
import unittest
import wave
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1] / "plugins" / "session-alarm"
sys.path.insert(0, str(PLUGIN_ROOT))

from session_alarm.catalog import (
    RECIPES,
    SAMPLE_RATE,
    SOUNDS,
    SOUND_BY_ID,
    render_wav,
    synthesize,
)


class CatalogTests(unittest.TestCase):
    def test_catalog_has_forty_unique_sounds(self):
        ids = [sound.sound_id for sound in SOUNDS]
        self.assertEqual(40, len(ids))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), set(RECIPES))
        self.assertEqual(set(ids), set(SOUND_BY_ID))

    def test_requested_fun_animals_are_present(self):
        expected = {
            "elephant",
            "crocodile",
            "hyena",
            "camel",
            "peacock",
            "penguin",
            "raccoon",
            "hippo",
            "mosquito",
        }
        self.assertTrue(expected.issubset(SOUND_BY_ID))

    def test_every_recipe_is_non_silent_and_bounded_in_length(self):
        for sound in SOUNDS:
            with self.subTest(sound=sound.sound_id):
                samples = synthesize(sound.sound_id)
                duration = len(samples) / SAMPLE_RATE
                self.assertGreater(duration, 0.2)
                self.assertLess(duration, 3.0)
                self.assertGreater(max(abs(value) for value in samples), 0.01)
                self.assertLessEqual(max(abs(value) for value in samples), 1.0)
                self.assertTrue(all(math.isfinite(value) for value in samples))
                self.assertLess(abs(sum(samples) / len(samples)), 0.08)

    def test_every_sound_renders_as_valid_pcm_wav(self):
        fingerprints = set()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for sound in SOUNDS:
                with self.subTest(sound=sound.sound_id):
                    path = render_wav(sound.sound_id, root / (sound.sound_id + ".wav"), 0.65)
                    with wave.open(str(path), "rb") as handle:
                        self.assertEqual(1, handle.getnchannels())
                        self.assertEqual(2, handle.getsampwidth())
                        self.assertEqual(SAMPLE_RATE, handle.getframerate())
                        self.assertGreater(handle.getnframes(), 1000)
                    fingerprints.add(hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(len(SOUNDS), len(fingerprints))

    def test_render_rejects_invalid_volume(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                render_wav("cat", Path(directory) / "cat.wav", 1.1)

    def test_unknown_sound_is_rejected(self):
        with self.assertRaises(ValueError):
            synthesize("copyrighted-meme")


if __name__ == "__main__":
    unittest.main()
