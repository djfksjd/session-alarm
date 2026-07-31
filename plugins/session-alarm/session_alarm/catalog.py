"""Short real-animal notification recordings bundled with Session Alarm.

Every bundled recording is published under CC0 on its individual Freesound
page. See SOUND_LICENSE.md and assets/sounds/sources.json in the repository.
"""

from __future__ import annotations

import math
import struct
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


SAMPLE_RATE = 44_100
SOUND_PACK_VERSION = 7
Samples = List[float]
ASSET_DIR = Path(__file__).resolve().parent.parent / "assets" / "sounds"


@dataclass(frozen=True)
class Sound:
    sound_id: str
    group: str
    name_en: str
    name_ko: str
    description_en: str
    description_ko: str


_SOUND_IDENTITIES = (
    ("cat", "pets", "Cat", "고양이"),
    ("dog", "pets", "Dog", "강아지"),
    ("cow", "farm", "Cow", "소"),
    ("horse", "farm", "Horse", "말"),
    ("pig", "farm", "Pig", "돼지"),
    ("goat", "farm", "Goat", "염소"),
    ("sheep", "farm", "Sheep", "양"),
    ("rooster", "farm", "Rooster", "수탉"),
    ("owl", "birds", "Owl", "올빼미"),
    ("crow", "birds", "Crow", "까마귀"),
    ("frog", "small", "Frog", "개구리"),
    ("cricket", "small", "Cricket", "귀뚜라미"),
)


def _sound(identity: tuple[str, str, str, str]) -> Sound:
    sound_id, group, name_en, name_ko = identity
    return Sound(
        sound_id,
        group,
        name_en,
        name_ko,
        f"A short CC0 recording of a real {name_en.lower()}",
        f"실제 {name_ko}를 녹음한 짧은 CC0 알림음",
    )


SOUNDS: Tuple[Sound, ...] = tuple(_sound(identity) for identity in _SOUND_IDENTITIES)

SOUND_BY_ID: Dict[str, Sound] = {sound.sound_id: sound for sound in SOUNDS}

GROUP_NAMES = {
    "pets": ("Pets", "반려동물"),
    "farm": ("Farm", "농장동물"),
    "birds": ("Birds", "새"),
    "small": ("Small creatures", "작은 생물"),
}


def asset_path(sound_id: str) -> Path:
    if sound_id not in SOUND_BY_ID:
        raise ValueError("Unknown sound: {0}".format(sound_id))
    return ASSET_DIR / (sound_id + ".wav")


def _read_asset(sound_id: str) -> Tuple[Samples, int]:
    path = asset_path(sound_id)
    if not path.is_file():
        raise ValueError("Bundled sound is missing: {0}".format(path))
    try:
        with wave.open(str(path), "rb") as source:
            if (
                source.getnchannels() != 1
                or source.getsampwidth() != 2
                or source.getcomptype() != "NONE"
            ):
                raise ValueError("Bundled sound must be mono 16-bit PCM WAV: {0}".format(path))
            rate = source.getframerate()
            frames = source.readframes(source.getnframes())
    except (OSError, EOFError, wave.Error) as exc:
        raise ValueError("Could not read bundled sound {0}: {1}".format(path, exc)) from exc
    samples = [
        value[0] / 32768.0
        for value in struct.iter_unpack("<h", frames)
    ]
    if not samples:
        raise ValueError("Bundled sound is empty: {0}".format(path))
    return samples, rate


def _resample(samples: Samples, source_rate: int) -> Samples:
    if source_rate == SAMPLE_RATE:
        return list(samples)
    if source_rate <= 0:
        raise ValueError("Invalid bundled sound sample rate")
    output_length = max(1, int(round(len(samples) * SAMPLE_RATE / source_rate)))
    if len(samples) == 1:
        return [samples[0]] * output_length
    ratio = source_rate / SAMPLE_RATE
    final = len(samples) - 1
    output: Samples = []
    for index in range(output_length):
        position = min(index * ratio, final)
        left = int(math.floor(position))
        right = min(left + 1, final)
        fraction = position - left
        output.append(samples[left] * (1.0 - fraction) + samples[right] * fraction)
    return output


def synthesize(sound_id: str) -> Samples:
    """Load one bundled sound as 44.1 kHz floating-point samples."""
    samples, source_rate = _read_asset(sound_id)
    return _resample(samples, source_rate)


def render_wav(sound_id: str, path: Path, volume: float = 0.7) -> Path:
    """Render a volume-adjusted mono 16-bit 44.1 kHz PCM WAV."""
    if not 0.0 <= volume <= 1.0:
        raise ValueError("volume must be between 0.0 and 1.0")
    samples = synthesize(sound_id)
    pcm = bytearray()
    for value in samples:
        clamped = max(-1.0, min(1.0, value * volume))
        pcm.extend(struct.pack("<h", int(round(clamped * 32767))))

    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(bytes(pcm))
    return path


def localized_name(sound: Sound, language: str) -> str:
    return sound.name_ko if language == "ko" else sound.name_en


def localized_description(sound: Sound, language: str) -> str:
    return sound.description_ko if language == "ko" else sound.description_en
