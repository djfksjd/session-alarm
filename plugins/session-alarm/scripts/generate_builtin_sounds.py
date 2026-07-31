#!/usr/bin/env python3
"""Generate and verify Session Alarm's deterministic built-in notification tones."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import struct
import sys
import wave
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PLUGIN_ROOT.parents[1]
ASSET_DIR = PLUGIN_ROOT / "assets" / "sounds"
MANIFEST_PATH = ASSET_DIR / "sources.json"
GENERATOR_PATH = "plugins/session-alarm/scripts/generate_builtin_sounds.py"
SAMPLE_RATE = 44_100
EXTERNAL_ASSET_IDS = {"elephant"}

sys.path.insert(0, str(PLUGIN_ROOT))
from session_alarm.catalog import SOUNDS  # noqa: E402


def _tone_bytes(sound_id: str) -> bytes:
    seed = hashlib.sha256(("session-alarm-v6:" + sound_id).encode("utf-8")).digest()
    duration = 0.52 + (seed[0] % 34) / 100.0
    frame_count = int(round(duration * SAMPLE_RATE))
    base = 190.0 + int.from_bytes(seed[1:3], "big") % 620
    sweep = ((seed[3] % 81) - 40) / 100.0
    harmonic = 1.5 + (seed[4] % 16) / 10.0
    pulse_rate = 2.0 + (seed[5] % 7)
    trill_rate = 3.0 + (seed[6] % 11)
    phase = (seed[7] / 255.0) * math.tau
    samples: list[float] = []

    for index in range(frame_count):
        t = index / SAMPLE_RATE
        position = index / max(1, frame_count - 1)
        attack = min(1.0, t / 0.035)
        release = min(1.0, (duration - t) / 0.09)
        envelope = max(0.0, min(attack, release))
        pulse = 0.72 + 0.28 * math.sin(math.tau * pulse_rate * t + phase) ** 2
        frequency = base * (1.0 + sweep * (position - 0.5))
        frequency *= 1.0 + 0.025 * math.sin(math.tau * trill_rate * t)
        angle = math.tau * frequency * t
        value = (
            math.sin(angle)
            + 0.31 * math.sin(angle * harmonic + phase)
            + 0.12 * math.sin(angle * (harmonic + 1.0))
        )
        samples.append(value * envelope * pulse)

    peak = max(abs(value) for value in samples) or 1.0
    scale = 0.72 / peak
    pcm = b"".join(
        struct.pack("<h", int(round(max(-1.0, min(1.0, value * scale)) * 32767)))
        for value in samples
    )
    output = io.BytesIO()
    with wave.open(output, "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(SAMPLE_RATE)
        target.writeframes(pcm)
    return output.getvalue()


def _manifest(generated: dict[str, bytes]) -> dict[str, object]:
    sounds: list[dict[str, object]] = []
    for sound in sorted(SOUNDS, key=lambda item: item.sound_id):
        path = ASSET_DIR / f"{sound.sound_id}.wav"
        if sound.sound_id == "elephant":
            data = path.read_bytes()
            sounds.append(
                {
                    "id": "elephant",
                    "file": "elephant.wav",
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "provenance": "verified_asset",
                    "provider": "Pixabay",
                    "title": "Elephant Trumpeting",
                    "contributor": "DRAGON-STUDIO",
                    "source_page": (
                        "https://pixabay.com/sound-effects/"
                        "nature-elephant-trumpeting-494313/"
                    ),
                    "published_date": "2026-03-04",
                    "verified_at": "2026-07-30",
                    "license_name": "Pixabay Content License",
                    "license_url": "https://pixabay.com/service/license-summary/",
                    "commercial_use_permitted": True,
                    "attribution_required": False,
                    "standalone_redistribution_prohibited": True,
                    "verification": (
                        "The normalized WAV has 0.998711 waveform correlation with "
                        "the officially downloaded source after encoder-delay alignment."
                    ),
                }
            )
            continue
        data = generated[sound.sound_id]
        sounds.append(
            {
                "id": sound.sound_id,
                "file": f"{sound.sound_id}.wav",
                "sha256": hashlib.sha256(data).hexdigest(),
                "provenance": "project_generated",
                "creator": "Session Alarm contributors",
                "generator": GENERATOR_PATH,
                "generator_seed": f"session-alarm-v6:{sound.sound_id}",
                "license_name": "MIT",
                "license_file": "LICENSE",
            }
        )
    return {
        "schema_version": 2,
        "integration": (
            "Bundled as functional notification assets in Session Alarm; "
            "not offered as a standalone sound library."
        ),
        "sounds": sounds,
    }


def _expected_files() -> dict[str, bytes]:
    return {
        sound.sound_id: _tone_bytes(sound.sound_id)
        for sound in SOUNDS
        if sound.sound_id not in EXTERNAL_ASSET_IDS
    }


def write_assets() -> int:
    generated = _expected_files()
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    for sound_id, data in generated.items():
        (ASSET_DIR / f"{sound_id}.wav").write_bytes(data)
    manifest_text = json.dumps(
        _manifest(generated),
        ensure_ascii=False,
        indent=2,
    ) + "\n"
    MANIFEST_PATH.write_text(manifest_text, encoding="utf-8")
    print(f"Wrote {len(generated)} deterministic tones and {MANIFEST_PATH}")
    return 0


def check_assets() -> int:
    generated = _expected_files()
    errors: list[str] = []
    for sound_id, expected in generated.items():
        path = ASSET_DIR / f"{sound_id}.wav"
        if not path.is_file():
            errors.append(f"missing generated asset: {path}")
        elif path.read_bytes() != expected:
            errors.append(f"generated asset drift: {path}")
    expected_manifest = json.dumps(
        _manifest(generated),
        ensure_ascii=False,
        indent=2,
    ) + "\n"
    if not MANIFEST_PATH.is_file():
        errors.append(f"missing manifest: {MANIFEST_PATH}")
    elif MANIFEST_PATH.read_text(encoding="utf-8") != expected_manifest:
        errors.append(f"manifest drift: {MANIFEST_PATH}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"Verified {len(generated)} deterministic tones and mixed-license manifest")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write generated assets")
    mode.add_argument("--check", action="store_true", help="verify committed assets")
    args = parser.parse_args()
    return write_assets() if args.write else check_assets()


if __name__ == "__main__":
    raise SystemExit(main())
