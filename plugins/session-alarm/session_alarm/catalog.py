"""Licensed animal notification sounds bundled with Session Alarm.

The audio assets come from Pixabay and remain subject to the Pixabay Content
License. See SOUND_LICENSE.md and assets/sounds/sources.json in the repository.
"""

from __future__ import annotations

import math
import struct
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


SAMPLE_RATE = 44_100
SOUND_PACK_VERSION = 5
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


SOUNDS: Tuple[Sound, ...] = (
    Sound("cat", "pets", "Cat", "고양이", "A clear cat call", "또렷한 고양이 울음"),
    Sound("kitten", "pets", "Kitten", "아기 고양이", "A small kitten call", "작은 아기 고양이 울음"),
    Sound("dog", "pets", "Dog", "강아지", "A lively dog bark", "활기찬 개 짖는 소리"),
    Sound("puppy", "pets", "Puppy", "아기 강아지", "A playful puppy call", "장난스러운 아기 강아지 울음"),
    Sound("cow", "farm", "Cow", "소", "A resonant moo", "공명하는 음매"),
    Sound("horse", "farm", "Horse", "말", "A bright horse neigh", "힘찬 말 울음"),
    Sound("donkey", "farm", "Donkey", "당나귀", "A comic donkey bray", "익살스러운 당나귀 울음"),
    Sound("pig", "farm", "Pig", "돼지", "A short pig call", "짧은 돼지 울음"),
    Sound("goat", "farm", "Goat", "염소", "A lively goat bleat", "활기찬 염소 울음"),
    Sound("sheep", "farm", "Sheep", "양", "A soft sheep bleat", "부드러운 양 울음"),
    Sound("duck", "farm", "Duck", "오리", "A distinct duck quack", "뚜렷한 오리 꽥꽥"),
    Sound("goose", "farm", "Goose", "거위", "A nasal goose honk", "콧소리 나는 거위 울음"),
    Sound("chicken", "farm", "Chicken", "암탉", "A busy chicken cluck", "바쁜 암탉 꼬꼬댁"),
    Sound("rooster", "farm", "Rooster", "수탉", "A full rooster crow", "힘찬 수탉 꼬끼오"),
    Sound("turkey", "farm", "Turkey", "칠면조", "A rolling turkey call", "빠르게 구르는 칠면조 울음"),
    Sound("wolf", "wild", "Wolf", "늑대", "A resonant wolf howl", "멀리 퍼지는 늑대 하울링"),
    Sound("fox", "wild", "Fox", "여우", "A sharp fox call", "날카로운 여우 울음"),
    Sound("lion", "wild", "Lion", "사자", "A deep lion roar", "낮고 힘찬 사자 포효"),
    Sound("elephant", "wild", "Elephant", "코끼리", "A real trumpet-like call", "실감 나는 코끼리 나팔 울음"),
    Sound("monkey", "wild", "Monkey", "원숭이", "A playful monkey call", "장난스러운 원숭이 울음"),
    Sound("bear", "wild", "Bear", "곰", "A heavy bear growl", "묵직한 곰 으르렁"),
    Sound("crocodile", "wild", "Crocodile", "악어", "A low crocodile call", "낮게 울리는 악어 소리"),
    Sound("hyena", "wild", "Hyena", "하이에나", "A bouncing hyena laugh", "통통 튀는 하이에나 웃음"),
    Sound("camel", "wild", "Camel", "낙타", "A wobbling camel call", "출렁이는 낙타 울음"),
    Sound("raccoon", "wild", "Raccoon", "라쿤", "A busy raccoon call", "빠르고 부산스러운 라쿤 울음"),
    Sound("hippo", "wild", "Hippo", "하마", "A round hippo grunt", "둥글고 낮은 하마 울음"),
    Sound("snake", "wild", "Snake", "뱀", "A clean snake hiss", "선명한 뱀 경고음"),
    Sound("owl", "birds", "Owl", "올빼미", "A hollow owl hoot", "속이 빈 듯한 올빼미 울음"),
    Sound("crow", "birds", "Crow", "까마귀", "A rough crow caw", "거친 까마귀 울음"),
    Sound("sparrow", "birds", "Sparrow", "참새", "A crisp sparrow chirp", "맑고 빠른 참새 지저귐"),
    Sound("eagle", "birds", "Eagle", "독수리", "A high eagle cry", "높고 날카로운 독수리 울음"),
    Sound("peacock", "birds", "Peacock", "공작", "A dramatic peacock call", "과장된 공작 울음"),
    Sound("penguin", "birds", "Penguin", "펭귄", "A comic penguin call", "익살스러운 펭귄 울음"),
    Sound("frog", "small", "Frog", "개구리", "A pulsing frog croak", "통통 울리는 개구리 소리"),
    Sound("cricket", "small", "Cricket", "귀뚜라미", "A crisp cricket chirp", "또렷한 귀뚜라미 소리"),
    Sound("bee", "small", "Bee", "벌", "A close bee buzz", "가까이 나는 벌의 윙윙"),
    Sound("mosquito", "small", "Mosquito", "모기", "A tiny mosquito whine", "가느다란 모기 윙윙"),
    Sound("dolphin", "ocean", "Dolphin", "돌고래", "A bright dolphin call", "맑은 돌고래 울음"),
    Sound("seal", "ocean", "Seal", "물개", "A hollow seal bark", "통통 튀는 물개 울음"),
    Sound("whale", "ocean", "Whale", "고래", "A calm whale call", "잔잔한 고래 울음"),
)

SOUND_BY_ID: Dict[str, Sound] = {sound.sound_id: sound for sound in SOUNDS}

GROUP_NAMES = {
    "pets": ("Pets", "반려동물"),
    "farm": ("Farm", "농장동물"),
    "wild": ("Wild", "야생동물"),
    "birds": ("Birds", "새"),
    "small": ("Small creatures", "작은 생물"),
    "ocean": ("Ocean", "바다동물"),
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
    """Load one bundled licensed sound as 44.1 kHz floating-point samples."""
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
