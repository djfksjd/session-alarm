"""Original procedural animal notification synthesis for Session Alarm.

No recordings, samples, model outputs, or third-party audio are embedded here.
Each sound is generated from deterministic DSP primitives at 44.1 kHz.
"""

from __future__ import annotations

import math
import random
import struct
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple


SAMPLE_RATE = 44_100
SOUND_PACK_VERSION = 3
TAU = math.tau
Samples = List[float]
Point = Tuple[float, float]


@dataclass(frozen=True)
class Sound:
    sound_id: str
    group: str
    name_en: str
    name_ko: str
    description_en: str
    description_ko: str


SOUNDS: Tuple[Sound, ...] = (
    Sound("cat", "pets", "Cat", "고양이", "A rounded two-part meow", "둥글게 이어지는 두 음절 야옹"),
    Sound("kitten", "pets", "Kitten", "아기 고양이", "A tiny high mew", "작고 높은 아기 고양이 울음"),
    Sound("dog", "pets", "Dog", "강아지", "Two punchy barks", "힘차게 두 번 짖는 소리"),
    Sound("puppy", "pets", "Puppy", "아기 강아지", "Three playful yips", "장난스럽게 세 번 짖는 소리"),
    Sound("cow", "farm", "Cow", "소", "A long resonant moo", "공명하며 길게 우는 음매"),
    Sound("horse", "farm", "Horse", "말", "A rising, trembling neigh", "위로 치솟으며 떨리는 히이잉"),
    Sound("donkey", "farm", "Donkey", "당나귀", "A comic hee-haw", "익살스러운 히호"),
    Sound("pig", "farm", "Pig", "돼지", "Two nasal oinks", "콧소리 나는 두 번의 꿀꿀"),
    Sound("goat", "farm", "Goat", "염소", "A wobbly bleat", "덜덜 떨리는 메에"),
    Sound("sheep", "farm", "Sheep", "양", "A soft sustained baa", "부드럽고 길게 이어지는 매애"),
    Sound("duck", "farm", "Duck", "오리", "Three dry quacks", "톡톡 끊기는 세 번의 꽥꽥"),
    Sound("goose", "farm", "Goose", "거위", "Two nasal honks", "콧소리 나는 두 번의 꿱"),
    Sound("chicken", "farm", "Chicken", "암탉", "A busy cluck cluster", "바쁘게 이어지는 꼬꼬댁"),
    Sound("rooster", "farm", "Rooster", "수탉", "A full morning crow", "길고 힘찬 아침 꼬끼오"),
    Sound("turkey", "farm", "Turkey", "칠면조", "A rolling gobble", "빠르게 구르는 골골 울음"),
    Sound("wolf", "wild", "Wolf", "늑대", "A distant resonant howl", "멀리 퍼지는 공명 하울링"),
    Sound("fox", "wild", "Fox", "여우", "Three sharp calls", "날카롭게 세 번 우는 소리"),
    Sound("lion", "wild", "Lion", "사자", "A deep textured roar", "낮고 거친 포효"),
    Sound("elephant", "wild", "Elephant", "코끼리", "A bright trunk trumpet", "코로 힘차게 부는 나팔 소리"),
    Sound("monkey", "wild", "Monkey", "원숭이", "Fast playful chatter", "빠르고 장난스러운 재잘거림"),
    Sound("bear", "wild", "Bear", "곰", "A heavy chesty growl", "가슴을 울리는 묵직한 으르렁"),
    Sound("crocodile", "wild", "Crocodile", "악어", "A hiss over a low rumble", "낮은 진동 위로 올라오는 쉿 소리"),
    Sound("hyena", "wild", "Hyena", "하이에나", "A bouncing laugh-call", "통통 튀는 웃음 같은 울음"),
    Sound("camel", "wild", "Camel", "낙타", "A wobbling desert groan", "출렁이는 듯한 사막의 울음"),
    Sound("raccoon", "wild", "Raccoon", "라쿤", "Busy masked chatter", "빠르고 부산스러운 재잘거림"),
    Sound("hippo", "wild", "Hippo", "하마", "Three round bass grunts", "둥글고 낮은 세 번의 울음"),
    Sound("snake", "wild", "Snake", "뱀", "A clean warning hiss", "선명하게 이어지는 경고 쉿"),
    Sound("owl", "birds", "Owl", "올빼미", "Two hollow hoots", "속이 빈 듯 둥근 두 번의 부엉"),
    Sound("crow", "birds", "Crow", "까마귀", "Two rough caws", "거칠게 두 번 우는 까악"),
    Sound("sparrow", "birds", "Sparrow", "참새", "A bright chirp phrase", "맑고 빠른 짹짹"),
    Sound("eagle", "birds", "Eagle", "독수리", "A high descending cry", "높게 시작해 내려오는 울음"),
    Sound("peacock", "birds", "Peacock", "공작", "A dramatic two-note call", "과장된 두 음절 울음"),
    Sound("penguin", "birds", "Penguin", "펭귄", "A comic braying honk", "익살스러운 나팔 같은 울음"),
    Sound("frog", "small", "Frog", "개구리", "Three pulsing croaks", "통통 울리는 세 번의 개굴"),
    Sound("cricket", "small", "Cricket", "귀뚜라미", "A crisp chirp pattern", "또렷하게 반복되는 귀뚤 소리"),
    Sound("bee", "small", "Bee", "벌", "A circling buzz", "주위를 도는 듯한 윙윙"),
    Sound("mosquito", "small", "Mosquito", "모기", "A tiny fly-by whine", "귓가를 스쳐 가는 가느다란 윙"),
    Sound("dolphin", "ocean", "Dolphin", "돌고래", "Clicks and a rising whistle", "딸깍 소리 뒤로 올라가는 휘파람"),
    Sound("seal", "ocean", "Seal", "물개", "Three hollow barks", "속이 빈 듯 통통 튀는 세 번의 울음"),
    Sound("whale", "ocean", "Whale", "고래", "A calm echoing call", "잔잔하게 메아리치는 수중 울음"),
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


def _silence(duration: float) -> Samples:
    return [0.0] * max(0, int(round(duration * SAMPLE_RATE)))


def _concat(*parts: Iterable[float]) -> Samples:
    result: Samples = []
    for part in parts:
        result.extend(part)
    return result


def _mix_at(*tracks: Tuple[Sequence[float], float]) -> Samples:
    length = 0
    offsets: List[Tuple[Sequence[float], int]] = []
    for track, offset_seconds in tracks:
        offset = max(0, int(round(offset_seconds * SAMPLE_RATE)))
        offsets.append((track, offset))
        length = max(length, offset + len(track))
    result = [0.0] * length
    for track, offset in offsets:
        for index, value in enumerate(track):
            result[offset + index] += value
    return result


def _repeat(factory: Callable[[int], Samples], count: int, gap: float) -> Samples:
    parts: List[Iterable[float]] = []
    for index in range(count):
        parts.append(factory(index))
        if index != count - 1:
            parts.append(_silence(gap))
    return _concat(*parts)


def _envelope(
    duration: float,
    attack: float = 0.02,
    release: float = 0.12,
    *,
    tremolo_hz: float = 0.0,
    tremolo_depth: float = 0.0,
) -> Samples:
    count = max(1, int(round(duration * SAMPLE_RATE)))
    output: Samples = []
    for index in range(count):
        position = index / SAMPLE_RATE
        attack_gain = 1.0 if attack <= 0 else min(1.0, position / attack)
        release_gain = 1.0 if release <= 0 else min(1.0, (duration - position) / release)
        gain = math.sin(0.5 * math.pi * max(0.0, min(attack_gain, release_gain)))
        if tremolo_hz:
            gain *= 1.0 - tremolo_depth * (
                0.5 + 0.5 * math.sin(TAU * tremolo_hz * position)
            )
        output.append(gain)
    return output


def _curve(points: Sequence[Point], ratio: float) -> float:
    if not points:
        return 0.0
    if ratio <= points[0][0]:
        return points[0][1]
    for (left_x, left_y), (right_x, right_y) in zip(points, points[1:]):
        if ratio <= right_x:
            local = (ratio - left_x) / max(1e-9, right_x - left_x)
            smooth = local * local * (3.0 - 2.0 * local)
            return left_y + (right_y - left_y) * smooth
    return points[-1][1]


def _biquad_bandpass(samples: Sequence[float], center_hz: float, q: float) -> Samples:
    omega = TAU * center_hz / SAMPLE_RATE
    alpha = math.sin(omega) / (2.0 * max(0.1, q))
    a0 = 1.0 + alpha
    b0 = alpha / a0
    b1 = 0.0
    b2 = -alpha / a0
    a1 = (-2.0 * math.cos(omega)) / a0
    a2 = (1.0 - alpha) / a0
    x1 = x2 = y1 = y2 = 0.0
    output: Samples = []
    for sample in samples:
        value = b0 * sample + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1 = x1, sample
        y2, y1 = y1, value
        output.append(value)
    return output


def _lowpass(samples: Sequence[float], cutoff_hz: float) -> Samples:
    coefficient = 1.0 - math.exp(-TAU * cutoff_hz / SAMPLE_RATE)
    state = 0.0
    output: Samples = []
    for sample in samples:
        state += coefficient * (sample - state)
        output.append(state)
    return output


def _highpass(samples: Sequence[float], cutoff_hz: float) -> Samples:
    low = _lowpass(samples, cutoff_hz)
    return [sample - base for sample, base in zip(samples, low)]


def _apply_envelope(samples: Sequence[float], envelope: Sequence[float]) -> Samples:
    return [sample * gain for sample, gain in zip(samples, envelope)]


def _normalize(samples: Sequence[float], peak: float = 0.92) -> Samples:
    maximum = max((abs(value) for value in samples), default=0.0)
    if maximum <= 1e-9:
        return list(samples)
    scale = peak / maximum
    return [max(-1.0, min(1.0, value * scale)) for value in samples]


def _noise(
    duration: float,
    *,
    seed: int,
    lowpass_hz: Optional[float] = None,
    highpass_hz: Optional[float] = None,
    band_hz: Optional[float] = None,
    band_q: float = 1.0,
    attack: float = 0.01,
    release: float = 0.12,
    tremolo_hz: float = 0.0,
    tremolo_depth: float = 0.0,
) -> Samples:
    count = max(1, int(round(duration * SAMPLE_RATE)))
    rng = random.Random(seed)
    samples = [rng.uniform(-1.0, 1.0) for _ in range(count)]
    if lowpass_hz:
        samples = _lowpass(samples, lowpass_hz)
    if highpass_hz:
        samples = _highpass(samples, highpass_hz)
    if band_hz:
        samples = _biquad_bandpass(samples, band_hz, band_q)
    envelope = _envelope(
        duration,
        attack,
        release,
        tremolo_hz=tremolo_hz,
        tremolo_depth=tremolo_depth,
    )
    return _normalize(_apply_envelope(samples, envelope), 0.75)


def _vocal(
    duration: float,
    pitch: Sequence[Point],
    *,
    formants: Sequence[Tuple[float, float, float]],
    seed: int,
    harmonics: int = 12,
    vibrato_hz: float = 0.0,
    vibrato_depth: float = 0.0,
    tremolo_hz: float = 0.0,
    tremolo_depth: float = 0.0,
    roughness: float = 0.0,
    breath: float = 0.0,
    attack: float = 0.025,
    release: float = 0.14,
) -> Samples:
    count = max(1, int(round(duration * SAMPLE_RATE)))
    rng = random.Random(seed)
    phase = 0.0
    jitter = 0.0
    source: Samples = []
    harmonic_weights = [1.0 / (number ** 1.18) for number in range(1, harmonics + 1)]
    total_weight = sum(harmonic_weights)

    for index in range(count):
        position = index / SAMPLE_RATE
        ratio = index / max(1, count - 1)
        frequency = _curve(pitch, ratio)
        if vibrato_hz:
            frequency *= 1.0 + vibrato_depth * math.sin(TAU * vibrato_hz * position)
        if roughness:
            jitter = 0.985 * jitter + 0.015 * rng.uniform(-1.0, 1.0)
            frequency *= 1.0 + roughness * jitter
        phase += TAU * max(20.0, frequency) / SAMPLE_RATE
        glottal = sum(
            weight * math.sin(number * phase)
            for number, weight in enumerate(harmonic_weights, 1)
        ) / total_weight
        if roughness:
            glottal = math.tanh((1.4 + 2.0 * roughness) * glottal)
        if breath:
            glottal = (1.0 - breath) * glottal + breath * rng.uniform(-1.0, 1.0)
        source.append(glottal)

    shaped = [value * 0.22 for value in source]
    for center, q, gain in formants:
        filtered = _biquad_bandpass(source, center, q)
        for index, value in enumerate(filtered):
            shaped[index] += gain * value
    envelope = _envelope(
        duration,
        attack,
        release,
        tremolo_hz=tremolo_hz,
        tremolo_depth=tremolo_depth,
    )
    return _normalize(_apply_envelope(shaped, envelope))


def _chirp(
    duration: float,
    pitch: Sequence[Point],
    *,
    seed: int = 0,
    harmonics: Sequence[Tuple[int, float]] = ((1, 1.0),),
    vibrato_hz: float = 0.0,
    vibrato_depth: float = 0.0,
    attack: float = 0.004,
    release: float = 0.035,
) -> Samples:
    count = max(1, int(round(duration * SAMPLE_RATE)))
    phase = 0.0
    rng = random.Random(seed)
    envelope = _envelope(duration, attack, release)
    weight = sum(abs(gain) for _, gain in harmonics) or 1.0
    output: Samples = []
    for index in range(count):
        ratio = index / max(1, count - 1)
        position = index / SAMPLE_RATE
        frequency = _curve(pitch, ratio)
        if vibrato_hz:
            frequency *= 1.0 + vibrato_depth * math.sin(TAU * vibrato_hz * position)
        frequency *= 1.0 + 0.0005 * rng.uniform(-1.0, 1.0)
        phase += TAU * frequency / SAMPLE_RATE
        value = sum(gain * math.sin(number * phase) for number, gain in harmonics) / weight
        output.append(value * envelope[index])
    return _normalize(output)


def _echo(samples: Sequence[float], delay: float, decay: float) -> Samples:
    offset = max(1, int(round(delay * SAMPLE_RATE)))
    output = list(samples) + [0.0] * offset
    for index, value in enumerate(samples):
        output[index + offset] += decay * value
    return _normalize(output)


def _bark(pitch_hz: float, seed: int, duration: float = 0.22) -> Samples:
    voice = _vocal(
        duration,
        ((0.0, pitch_hz * 1.15), (0.25, pitch_hz), (1.0, pitch_hz * 0.62)),
        formants=((430, 2.2, 1.0), (920, 2.8, 0.75), (1650, 3.2, 0.32)),
        seed=seed,
        harmonics=18,
        roughness=0.32,
        breath=0.12,
        attack=0.006,
        release=duration * 0.55,
    )
    burst = _noise(
        duration,
        seed=seed + 100,
        band_hz=780,
        band_q=0.7,
        attack=0.002,
        release=duration * 0.62,
    )
    return _normalize(_mix_at((voice, 0.0), ([0.32 * value for value in burst], 0.0)))


def _grunt(pitch_hz: float, seed: int, duration: float = 0.32) -> Samples:
    return _vocal(
        duration,
        ((0.0, pitch_hz * 1.08), (0.35, pitch_hz), (1.0, pitch_hz * 0.72)),
        formants=((310, 1.8, 1.0), (690, 2.4, 0.52)),
        seed=seed,
        harmonics=18,
        roughness=0.38,
        breath=0.1,
        attack=0.015,
        release=0.14,
    )


def _cat() -> Samples:
    first = _vocal(
        0.55,
        ((0.0, 520), (0.32, 790), (0.62, 880), (1.0, 430)),
        formants=((850, 3.2, 1.0), (1450, 4.5, 0.58), (2450, 5.0, 0.18)),
        seed=11,
        harmonics=10,
        vibrato_hz=7.5,
        vibrato_depth=0.018,
        breath=0.025,
        attack=0.045,
        release=0.18,
    )
    second = _vocal(
        0.32,
        ((0.0, 670), (0.35, 760), (1.0, 390)),
        formants=((820, 3.0, 1.0), (1370, 4.0, 0.48)),
        seed=12,
        harmonics=9,
        vibrato_hz=8.0,
        vibrato_depth=0.022,
        breath=0.02,
        release=0.13,
    )
    return _concat(first, _silence(0.055), second)


def _kitten() -> Samples:
    return _vocal(
        0.48,
        ((0.0, 920), (0.3, 1320), (0.62, 1180), (1.0, 720)),
        formants=((1250, 3.4, 1.0), (2250, 4.2, 0.42)),
        seed=14,
        harmonics=8,
        vibrato_hz=10.5,
        vibrato_depth=0.025,
        breath=0.02,
        attack=0.025,
        release=0.14,
    )


def _dog() -> Samples:
    return _repeat(lambda index: _bark(185 - 12 * index, 20 + index, 0.23), 2, 0.12)


def _puppy() -> Samples:
    return _repeat(lambda index: _bark(430 + 25 * index, 30 + index, 0.14), 3, 0.08)


def _cow() -> Samples:
    return _vocal(
        1.32,
        ((0.0, 118), (0.22, 126), (0.72, 104), (1.0, 92)),
        formants=((420, 2.2, 1.0), (880, 3.1, 0.74), (1420, 3.8, 0.26)),
        seed=40,
        harmonics=22,
        vibrato_hz=4.4,
        vibrato_depth=0.022,
        tremolo_hz=2.2,
        tremolo_depth=0.12,
        roughness=0.12,
        breath=0.035,
        attack=0.12,
        release=0.27,
    )


def _horse() -> Samples:
    breath = _noise(0.78, seed=49, band_hz=1700, band_q=1.0, attack=0.02, release=0.17)
    voice = _vocal(
        0.82,
        ((0.0, 340), (0.23, 760), (0.45, 1040), (0.72, 760), (1.0, 410)),
        formants=((760, 2.8, 1.0), (1580, 3.6, 0.64), (2750, 5.0, 0.18)),
        seed=50,
        harmonics=13,
        vibrato_hz=12.0,
        vibrato_depth=0.032,
        tremolo_hz=8.0,
        tremolo_depth=0.22,
        roughness=0.08,
        breath=0.04,
        attack=0.025,
        release=0.19,
    )
    return _normalize(_mix_at((voice, 0.0), ([0.18 * value for value in breath], 0.0)))


def _donkey() -> Samples:
    hee = _vocal(
        0.38,
        ((0.0, 430), (0.4, 680), (1.0, 610)),
        formants=((720, 2.4, 1.0), (1480, 3.0, 0.64)),
        seed=55,
        harmonics=16,
        vibrato_hz=7.2,
        vibrato_depth=0.038,
        roughness=0.12,
        breath=0.04,
        release=0.1,
    )
    haw = _vocal(
        0.62,
        ((0.0, 270), (0.25, 210), (1.0, 155)),
        formants=((520, 2.1, 1.0), (1050, 2.8, 0.6)),
        seed=56,
        harmonics=20,
        vibrato_hz=5.4,
        vibrato_depth=0.028,
        roughness=0.24,
        breath=0.06,
        release=0.22,
    )
    return _concat(hee, _silence(0.045), haw)


def _pig() -> Samples:
    return _repeat(lambda index: _grunt(195 + 12 * index, 60 + index, 0.27), 2, 0.09)


def _goat() -> Samples:
    return _vocal(
        0.88,
        ((0.0, 360), (0.25, 410), (0.72, 340), (1.0, 285)),
        formants=((630, 2.4, 1.0), (1280, 3.2, 0.56)),
        seed=65,
        harmonics=15,
        vibrato_hz=8.8,
        vibrato_depth=0.05,
        tremolo_hz=8.8,
        tremolo_depth=0.48,
        roughness=0.14,
        breath=0.04,
        attack=0.045,
        release=0.18,
    )


def _sheep() -> Samples:
    return _vocal(
        1.04,
        ((0.0, 270), (0.28, 310), (0.76, 275), (1.0, 235)),
        formants=((560, 2.5, 1.0), (1120, 3.4, 0.48)),
        seed=68,
        harmonics=14,
        vibrato_hz=6.3,
        vibrato_depth=0.025,
        tremolo_hz=6.3,
        tremolo_depth=0.34,
        roughness=0.07,
        breath=0.025,
        attack=0.075,
        release=0.22,
    )


def _duck() -> Samples:
    def quack(index: int) -> Samples:
        return _vocal(
            0.19,
            ((0.0, 265 + 8 * index), (0.22, 310), (1.0, 155)),
            formants=((780, 1.5, 1.0), (1750, 2.5, 0.72), (2900, 3.6, 0.2)),
            seed=72 + index,
            harmonics=18,
            roughness=0.26,
            breath=0.1,
            attack=0.004,
            release=0.09,
        )
    return _repeat(quack, 3, 0.085)


def _goose() -> Samples:
    return _repeat(
        lambda index: _vocal(
            0.27,
            ((0.0, 220 - 8 * index), (0.25, 265), (1.0, 135)),
            formants=((620, 1.7, 1.0), (1320, 2.4, 0.62)),
            seed=76 + index,
            harmonics=20,
            roughness=0.2,
            breath=0.08,
            attack=0.006,
            release=0.12,
        ),
        2,
        0.13,
    )


def _chicken() -> Samples:
    pitches = ((680, 310), (750, 350), (620, 260), (820, 370), (690, 280))
    return _concat(
        *[
            _concat(
                _vocal(
                    0.105,
                    ((0.0, start), (1.0, end)),
                    formants=((950, 2.0, 1.0), (2100, 3.2, 0.42)),
                    seed=80 + index,
                    harmonics=10,
                    roughness=0.18,
                    breath=0.06,
                    attack=0.003,
                    release=0.045,
                ),
                _silence(0.045),
            )
            for index, (start, end) in enumerate(pitches)
        ]
    )


def _rooster() -> Samples:
    one = _vocal(
        0.24,
        ((0.0, 510), (1.0, 850)),
        formants=((920, 2.2, 1.0), (1850, 3.4, 0.55)),
        seed=88,
        harmonics=15,
        vibrato_hz=8.5,
        vibrato_depth=0.024,
        roughness=0.12,
        breath=0.04,
        release=0.06,
    )
    two = _vocal(
        0.28,
        ((0.0, 760), (0.55, 1120), (1.0, 980)),
        formants=((1050, 2.4, 1.0), (2150, 3.7, 0.46)),
        seed=89,
        harmonics=12,
        vibrato_hz=9.0,
        vibrato_depth=0.025,
        tremolo_hz=7.5,
        tremolo_depth=0.15,
        breath=0.03,
        release=0.07,
    )
    three = _vocal(
        0.66,
        ((0.0, 930), (0.22, 1050), (1.0, 430)),
        formants=((900, 2.2, 1.0), (1850, 3.5, 0.48)),
        seed=90,
        harmonics=14,
        vibrato_hz=7.7,
        vibrato_depth=0.03,
        tremolo_hz=7.7,
        tremolo_depth=0.27,
        roughness=0.1,
        breath=0.04,
        release=0.2,
    )
    return _concat(one, _silence(0.025), two, _silence(0.025), three)


def _turkey() -> Samples:
    return _vocal(
        0.92,
        ((0.0, 175), (0.4, 155), (1.0, 125)),
        formants=((430, 1.8, 1.0), (920, 2.6, 0.58)),
        seed=94,
        harmonics=22,
        vibrato_hz=15.5,
        vibrato_depth=0.048,
        tremolo_hz=15.5,
        tremolo_depth=0.7,
        roughness=0.25,
        breath=0.06,
        attack=0.02,
        release=0.16,
    )


def _wolf() -> Samples:
    return _vocal(
        1.52,
        ((0.0, 245), (0.23, 390), (0.48, 455), (0.78, 420), (1.0, 325)),
        formants=((520, 3.0, 1.0), (1080, 4.0, 0.5), (2100, 5.0, 0.12)),
        seed=100,
        harmonics=12,
        vibrato_hz=5.1,
        vibrato_depth=0.018,
        tremolo_hz=2.1,
        tremolo_depth=0.1,
        roughness=0.045,
        breath=0.025,
        attack=0.18,
        release=0.32,
    )


def _fox() -> Samples:
    return _repeat(
        lambda index: _vocal(
            0.22,
            ((0.0, 760 + 50 * index), (0.32, 1160 + 80 * index), (1.0, 620)),
            formants=((1200, 2.8, 1.0), (2450, 4.0, 0.52)),
            seed=105 + index,
            harmonics=9,
            vibrato_hz=10.5,
            vibrato_depth=0.03,
            roughness=0.12,
            breath=0.06,
            attack=0.008,
            release=0.09,
        ),
        3,
        0.11,
    )


def _roar(pitch_hz: float, seed: int, duration: float, formant: float) -> Samples:
    voice = _vocal(
        duration,
        ((0.0, pitch_hz * 1.18), (0.32, pitch_hz), (1.0, pitch_hz * 0.65)),
        formants=((formant, 1.5, 1.0), (formant * 2.1, 2.2, 0.7), (formant * 3.7, 3.1, 0.25)),
        seed=seed,
        harmonics=30,
        vibrato_hz=3.2,
        vibrato_depth=0.02,
        tremolo_hz=4.2,
        tremolo_depth=0.18,
        roughness=0.55,
        breath=0.16,
        attack=0.055,
        release=duration * 0.3,
    )
    texture = _noise(
        duration,
        seed=seed + 1,
        band_hz=formant * 1.25,
        band_q=0.75,
        attack=0.035,
        release=duration * 0.34,
        tremolo_hz=16,
        tremolo_depth=0.32,
    )
    return _normalize(_mix_at((voice, 0.0), ([0.34 * value for value in texture], 0.0)))


def _lion() -> Samples:
    return _roar(92, 110, 1.28, 310)


def _elephant() -> Samples:
    # A lip-reed-like harmonic source through three trunk resonances. The
    # continuous rising pitch and low breath component create a trumpet rather
    # than the broadband-noise texture of a generic roar.
    trumpet = _vocal(
        1.34,
        ((0.0, 205), (0.12, 260), (0.34, 470), (0.53, 690), (0.74, 735), (1.0, 430)),
        formants=((680, 2.8, 1.0), (1280, 3.8, 0.72), (2380, 5.2, 0.32), (3600, 6.0, 0.1)),
        seed=120,
        harmonics=24,
        vibrato_hz=7.0,
        vibrato_depth=0.012,
        tremolo_hz=3.6,
        tremolo_depth=0.1,
        roughness=0.035,
        breath=0.018,
        attack=0.035,
        release=0.24,
    )
    trunk_air = _noise(
        1.18,
        seed=121,
        band_hz=1450,
        band_q=1.7,
        attack=0.03,
        release=0.24,
    )
    return _normalize(_mix_at((trumpet, 0.0), ([0.055 * value for value in trunk_air], 0.06)))


def _monkey() -> Samples:
    pitches = ((690, 990), (880, 620), (720, 1080), (940, 680), (790, 1100))
    parts: List[Samples] = []
    for index, (start, end) in enumerate(pitches):
        parts.append(
            _vocal(
                0.105,
                ((0.0, start), (1.0, end)),
                formants=((1180, 2.4, 1.0), (2400, 3.8, 0.42)),
                seed=130 + index,
                harmonics=10,
                roughness=0.1,
                breath=0.035,
                attack=0.004,
                release=0.045,
            )
        )
        parts.append(_silence(0.035))
    return _concat(*parts)


def _bear() -> Samples:
    return _roar(68, 140, 1.05, 240)


def _crocodile() -> Samples:
    rumble = _vocal(
        1.12,
        ((0.0, 58), (0.45, 52), (1.0, 44)),
        formants=((180, 1.2, 1.0), (410, 1.8, 0.52)),
        seed=150,
        harmonics=28,
        tremolo_hz=2.7,
        tremolo_depth=0.42,
        roughness=0.48,
        breath=0.08,
        attack=0.07,
        release=0.28,
    )
    hiss = _noise(
        0.82,
        seed=151,
        highpass_hz=1600,
        lowpass_hz=7600,
        attack=0.035,
        release=0.18,
        tremolo_hz=8.5,
        tremolo_depth=0.2,
    )
    return _normalize(_mix_at((rumble, 0.0), ([0.32 * value for value in hiss], 0.18)))


def _hyena() -> Samples:
    pitches = ((610, 880), (760, 1080), (690, 930), (840, 1220), (770, 990))
    return _concat(
        *[
            _concat(
                _vocal(
                    0.15,
                    ((0.0, start), (0.65, end), (1.0, end * 0.88)),
                    formants=((1120, 2.5, 1.0), (2280, 3.7, 0.46)),
                    seed=160 + index,
                    harmonics=11,
                    vibrato_hz=12.0,
                    vibrato_depth=0.04,
                    roughness=0.11,
                    breath=0.05,
                    attack=0.005,
                    release=0.065,
                ),
                _silence(0.055),
            )
            for index, (start, end) in enumerate(pitches)
        ]
    )


def _camel() -> Samples:
    first = _vocal(
        0.52,
        ((0.0, 205), (0.42, 128), (1.0, 165)),
        formants=((470, 1.8, 1.0), (980, 2.7, 0.6)),
        seed=170,
        harmonics=22,
        vibrato_hz=5.8,
        vibrato_depth=0.045,
        tremolo_hz=6.2,
        tremolo_depth=0.35,
        roughness=0.28,
        breath=0.08,
        attack=0.035,
        release=0.14,
    )
    second = _vocal(
        0.64,
        ((0.0, 150), (0.36, 235), (1.0, 175)),
        formants=((520, 1.9, 1.0), (1090, 2.8, 0.55)),
        seed=171,
        harmonics=20,
        vibrato_hz=5.0,
        vibrato_depth=0.04,
        roughness=0.25,
        breath=0.07,
        release=0.22,
    )
    return _concat(first, _silence(0.05), second)


def _raccoon() -> Samples:
    pitches = ((470, 720), (650, 390), (520, 840), (710, 470), (580, 880), (760, 520))
    return _concat(
        *[
            _concat(
                _vocal(
                    0.08,
                    ((0.0, start), (1.0, end)),
                    formants=((980, 2.1, 1.0), (2050, 3.3, 0.4)),
                    seed=180 + index,
                    harmonics=12,
                    roughness=0.18,
                    breath=0.05,
                    attack=0.003,
                    release=0.032,
                ),
                _silence(0.035),
            )
            for index, (start, end) in enumerate(pitches)
        ]
    )


def _hippo() -> Samples:
    return _repeat(lambda index: _grunt(82 - 4 * index, 190 + index, 0.3), 3, 0.105)


def _snake() -> Samples:
    return _noise(
        1.08,
        seed=200,
        highpass_hz=1700,
        lowpass_hz=9000,
        attack=0.04,
        release=0.16,
        tremolo_hz=9.0,
        tremolo_depth=0.28,
    )


def _owl() -> Samples:
    return _repeat(
        lambda index: _vocal(
            0.39,
            ((0.0, 350 - 18 * index), (0.45, 315 - 15 * index), (1.0, 250 - 12 * index)),
            formants=((430, 3.0, 1.0), (820, 4.0, 0.42)),
            seed=210 + index,
            harmonics=12,
            vibrato_hz=4.2,
            vibrato_depth=0.012,
            breath=0.018,
            attack=0.07,
            release=0.15,
        ),
        2,
        0.18,
    )


def _crow() -> Samples:
    return _repeat(
        lambda index: _vocal(
            0.28,
            ((0.0, 520 - 25 * index), (0.26, 610), (1.0, 245)),
            formants=((760, 1.7, 1.0), (1580, 2.5, 0.56)),
            seed=220 + index,
            harmonics=18,
            roughness=0.44,
            breath=0.15,
            attack=0.008,
            release=0.12,
        ),
        2,
        0.14,
    )


def _sparrow() -> Samples:
    pitches = ((2600, 4100), (3500, 2400), (2850, 4700), (4200, 3050), (3100, 4400))
    return _concat(
        *[
            _concat(
                _chirp(0.06, ((0.0, start), (1.0, end)), seed=230 + index, release=0.018),
                _silence(0.035),
            )
            for index, (start, end) in enumerate(pitches)
        ]
    )


def _eagle() -> Samples:
    return _vocal(
        0.78,
        ((0.0, 790), (0.26, 1560), (0.48, 1710), (1.0, 610)),
        formants=((1280, 2.8, 1.0), (2850, 4.2, 0.38)),
        seed=240,
        harmonics=9,
        vibrato_hz=10.5,
        vibrato_depth=0.03,
        roughness=0.08,
        breath=0.035,
        attack=0.025,
        release=0.18,
    )


def _peacock() -> Samples:
    first = _vocal(
        0.38,
        ((0.0, 650), (0.52, 1040), (1.0, 920)),
        formants=((1080, 2.5, 1.0), (2250, 3.8, 0.43)),
        seed=250,
        harmonics=11,
        vibrato_hz=8.0,
        vibrato_depth=0.025,
        roughness=0.08,
        breath=0.03,
        release=0.12,
    )
    second = _vocal(
        0.53,
        ((0.0, 960), (0.38, 1120), (1.0, 590)),
        formants=((1040, 2.4, 1.0), (2170, 3.6, 0.42)),
        seed=251,
        harmonics=12,
        vibrato_hz=7.5,
        vibrato_depth=0.03,
        roughness=0.08,
        breath=0.03,
        release=0.18,
    )
    return _concat(first, _silence(0.07), second)


def _penguin() -> Samples:
    first = _vocal(
        0.28,
        ((0.0, 330), (1.0, 530)),
        formants=((650, 1.9, 1.0), (1370, 2.8, 0.58)),
        seed=260,
        harmonics=17,
        tremolo_hz=7.0,
        tremolo_depth=0.27,
        roughness=0.2,
        breath=0.06,
        release=0.08,
    )
    second = _vocal(
        0.44,
        ((0.0, 510), (1.0, 245)),
        formants=((610, 1.8, 1.0), (1280, 2.7, 0.54)),
        seed=261,
        harmonics=18,
        tremolo_hz=6.0,
        tremolo_depth=0.23,
        roughness=0.22,
        breath=0.06,
        release=0.16,
    )
    return _concat(first, _silence(0.045), second)


def _frog() -> Samples:
    def croak(index: int) -> Samples:
        voice = _vocal(
            0.24,
            ((0.0, 105 - 4 * index), (0.35, 88), (1.0, 68 - 2 * index)),
            formants=((230, 1.2, 1.0), (480, 1.7, 0.48)),
            seed=270 + index,
            harmonics=24,
            tremolo_hz=18,
            tremolo_depth=0.65,
            roughness=0.22,
            breath=0.04,
            attack=0.015,
            release=0.1,
        )
        return voice
    return _repeat(croak, 3, 0.12)


def _cricket() -> Samples:
    return _repeat(
        lambda index: _chirp(
            0.046,
            ((0.0, 4300 + 70 * index), (1.0, 4850 + 35 * index)),
            seed=280 + index,
            attack=0.002,
            release=0.012,
        ),
        9,
        0.034,
    )


def _buzz(
    duration: float,
    start_hz: float,
    end_hz: float,
    seed: int,
    *,
    flyby: bool = False,
) -> Samples:
    base = _chirp(
        duration,
        ((0.0, start_hz), (0.5, (start_hz + end_hz) * 0.56), (1.0, end_hz)),
        seed=seed,
        harmonics=((1, 1.0), (2, 0.42), (3, 0.2), (4, 0.1)),
        vibrato_hz=7.0,
        vibrato_depth=0.055,
        attack=0.06,
        release=0.15,
    )
    count = len(base)
    output: Samples = []
    for index, value in enumerate(base):
        ratio = index / max(1, count - 1)
        motion = 0.58 + 0.42 * math.sin(math.pi * ratio) if flyby else 0.84 + 0.16 * math.sin(TAU * 1.8 * ratio)
        output.append(value * motion)
    return _normalize(output)


def _bee() -> Samples:
    return _buzz(1.04, 175, 215, 290)


def _mosquito() -> Samples:
    return _buzz(1.18, 520, 880, 300, flyby=True)


def _dolphin() -> Samples:
    clicks = _repeat(
        lambda index: _chirp(
            0.012,
            ((0.0, 7200 + 180 * index), (1.0, 4800)),
            seed=310 + index,
            attack=0.001,
            release=0.004,
        ),
        7,
        0.023,
    )
    whistle = _chirp(
        0.66,
        ((0.0, 2450), (0.32, 3900), (0.68, 6100), (1.0, 5200)),
        seed=318,
        vibrato_hz=9.2,
        vibrato_depth=0.022,
        attack=0.045,
        release=0.14,
    )
    return _concat(clicks, _silence(0.075), whistle)


def _seal() -> Samples:
    return _repeat(lambda index: _bark(390 - 22 * index, 320 + index, 0.19), 3, 0.11)


def _whale() -> Samples:
    call = _vocal(
        1.58,
        ((0.0, 125), (0.28, 245), (0.52, 315), (0.77, 225), (1.0, 112)),
        formants=((310, 3.2, 1.0), (620, 4.1, 0.36), (1180, 5.0, 0.1)),
        seed=330,
        harmonics=10,
        vibrato_hz=2.8,
        vibrato_depth=0.018,
        roughness=0.025,
        breath=0.018,
        attack=0.17,
        release=0.34,
    )
    return _echo(call, 0.23, 0.28)


RECIPES: Dict[str, Callable[[], Samples]] = {
    "cat": _cat,
    "kitten": _kitten,
    "dog": _dog,
    "puppy": _puppy,
    "cow": _cow,
    "horse": _horse,
    "donkey": _donkey,
    "pig": _pig,
    "goat": _goat,
    "sheep": _sheep,
    "duck": _duck,
    "goose": _goose,
    "chicken": _chicken,
    "rooster": _rooster,
    "turkey": _turkey,
    "wolf": _wolf,
    "fox": _fox,
    "lion": _lion,
    "elephant": _elephant,
    "monkey": _monkey,
    "bear": _bear,
    "crocodile": _crocodile,
    "hyena": _hyena,
    "camel": _camel,
    "raccoon": _raccoon,
    "hippo": _hippo,
    "snake": _snake,
    "owl": _owl,
    "crow": _crow,
    "sparrow": _sparrow,
    "eagle": _eagle,
    "peacock": _peacock,
    "penguin": _penguin,
    "frog": _frog,
    "cricket": _cricket,
    "bee": _bee,
    "mosquito": _mosquito,
    "dolphin": _dolphin,
    "seal": _seal,
    "whale": _whale,
}


def synthesize(sound_id: str) -> Samples:
    """Return a deterministic waveform for one catalog sound."""
    try:
        recipe = RECIPES[sound_id]
    except KeyError as exc:
        raise ValueError("Unknown sound: {0}".format(sound_id)) from exc
    return _normalize(recipe())


def render_wav(sound_id: str, path: Path, volume: float = 0.7) -> Path:
    """Render one original sound as mono 16-bit 44.1 kHz PCM WAV."""
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
