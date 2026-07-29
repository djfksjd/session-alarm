"""Safe local import and rendering for user-provided notification sounds."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import struct
import tempfile
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


CUSTOM_PREFIX = "custom:"
CUSTOM_REGISTRY_VERSION = 1
TARGET_RATE = 44_100
MAX_DURATION_SECONDS = 30.0
MAX_SOURCE_BYTES = 32 * 1024 * 1024
_SLUG_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]{0,47}")


class CustomSoundError(ValueError):
    """Raised when a custom sound cannot be safely imported or resolved."""


def registry_path(root: Path) -> Path:
    return root / "custom-sounds.json"


def custom_audio_dir(root: Path) -> Path:
    return root / "custom"


def _clean_name(value: str) -> str:
    cleaned = " ".join(value.replace("\x00", "").split()).strip()
    if not cleaned:
        raise CustomSoundError("custom sound name cannot be empty")
    return cleaned[:80]


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        slug = "sound"
    if not slug[0].isalnum():
        slug = "sound-" + slug
    return slug[:48].rstrip("-")


def normalize_custom_id(value: str) -> str:
    candidate = value.strip().lower()
    if candidate.startswith(CUSTOM_PREFIX):
        candidate = candidate[len(CUSTOM_PREFIX):]
    candidate = _slugify(candidate)
    if not _SLUG_PATTERN.fullmatch(candidate):
        raise CustomSoundError(
            "custom sound IDs must use 1-48 lowercase letters, numbers, or hyphens"
        )
    return CUSTOM_PREFIX + candidate


def _empty_registry() -> Dict[str, Any]:
    return {"schema_version": CUSTOM_REGISTRY_VERSION, "sounds": {}}


def load_custom_sounds(root: Path) -> Dict[str, Dict[str, Any]]:
    path = registry_path(root)
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise CustomSoundError("could not read custom sound registry: {0}".format(exc)) from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != CUSTOM_REGISTRY_VERSION:
        raise CustomSoundError("unsupported custom sound registry")
    sounds = payload.get("sounds")
    if not isinstance(sounds, dict):
        raise CustomSoundError("custom sound registry is malformed")

    result: Dict[str, Dict[str, Any]] = {}
    for slug, metadata in sounds.items():
        if not isinstance(slug, str) or not _SLUG_PATTERN.fullmatch(slug):
            raise CustomSoundError("custom sound registry contains an invalid ID")
        if not isinstance(metadata, dict) or not isinstance(metadata.get("name"), str):
            raise CustomSoundError("custom sound registry contains invalid metadata")
        sound_id = CUSTOM_PREFIX + slug
        item = dict(metadata)
        item["id"] = sound_id
        item["path"] = str(custom_audio_dir(root) / (slug + ".wav"))
        result[sound_id] = item
    return result


def _write_registry(root: Path, sounds: Dict[str, Dict[str, Any]]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    serializable: Dict[str, Dict[str, Any]] = {}
    for sound_id, metadata in sounds.items():
        slug = sound_id[len(CUSTOM_PREFIX):]
        serializable[slug] = {
            key: value
            for key, value in metadata.items()
            if key not in ("id", "path")
        }
    payload = {
        "schema_version": CUSTOM_REGISTRY_VERSION,
        "sounds": serializable,
    }
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".custom-sounds-",
        suffix=".json",
        dir=str(root),
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, registry_path(root))
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def _decode_sample(raw: bytes, width: int) -> float:
    if width == 1:
        return (raw[0] - 128) / 128.0
    value = int.from_bytes(raw, byteorder="little", signed=True)
    scale = float(1 << (width * 8 - 1))
    return max(-1.0, min(1.0, value / scale))


def _decode_mono(frames: bytes, channels: int, width: int) -> List[float]:
    stride = channels * width
    decoded: List[float] = []
    for offset in range(0, len(frames), stride):
        frame = frames[offset:offset + stride]
        if len(frame) != stride:
            break
        total = 0.0
        for channel in range(channels):
            start = channel * width
            total += _decode_sample(frame[start:start + width], width)
        decoded.append(total / channels)
    return decoded


def _resample(samples: Sequence[float], source_rate: int) -> List[float]:
    if source_rate == TARGET_RATE:
        return list(samples)
    output_length = max(1, int(round(len(samples) * TARGET_RATE / source_rate)))
    if len(samples) == 1:
        return [samples[0]] * output_length
    scale = source_rate / TARGET_RATE
    output: List[float] = []
    final_index = len(samples) - 1
    for index in range(output_length):
        position = min(index * scale, final_index)
        left = int(position)
        right = min(left + 1, final_index)
        fraction = position - left
        output.append(samples[left] * (1.0 - fraction) + samples[right] * fraction)
    return output


def _write_pcm16(path: Path, samples: Sequence[float], volume: float = 1.0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".custom-audio-",
        suffix=".wav",
        dir=str(path.parent),
    )
    os.close(descriptor)
    try:
        with wave.open(temporary_name, "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(TARGET_RATE)
            chunk = bytearray()
            for sample in samples:
                value = max(-1.0, min(1.0, sample * volume))
                chunk.extend(struct.pack("<h", int(round(value * 32767.0))))
                if len(chunk) >= 64 * 1024:
                    output.writeframesraw(bytes(chunk))
                    chunk.clear()
            if chunk:
                output.writeframesraw(bytes(chunk))
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def _read_canonical(path: Path) -> List[float]:
    try:
        with wave.open(str(path), "rb") as source:
            if (
                source.getnchannels() != 1
                or source.getsampwidth() != 2
                or source.getframerate() != TARGET_RATE
                or source.getcomptype() != "NONE"
            ):
                raise CustomSoundError("stored custom sound is not canonical PCM WAV")
            return _decode_mono(source.readframes(source.getnframes()), 1, 2)
    except (OSError, EOFError, wave.Error) as exc:
        raise CustomSoundError("could not read stored custom sound: {0}".format(exc)) from exc


def import_custom_sound(
    root: Path,
    source_path: Path,
    *,
    name: Optional[str] = None,
    requested_id: Optional[str] = None,
) -> Dict[str, Any]:
    source = source_path.expanduser().resolve()
    if not source.is_file():
        raise CustomSoundError("sound file does not exist: {0}".format(source_path))
    if source.suffix.lower() != ".wav":
        raise CustomSoundError(
            "only WAV files are supported so playback works on macOS, Windows, and Linux"
        )
    if source.stat().st_size > MAX_SOURCE_BYTES:
        raise CustomSoundError("custom sound must be 32 MB or smaller")

    try:
        with wave.open(str(source), "rb") as input_wav:
            channels = input_wav.getnchannels()
            width = input_wav.getsampwidth()
            rate = input_wav.getframerate()
            frames_count = input_wav.getnframes()
            if input_wav.getcomptype() != "NONE":
                raise CustomSoundError("compressed WAV files are not supported")
            if channels < 1 or channels > 8:
                raise CustomSoundError("WAV must have between 1 and 8 channels")
            if width not in (1, 2, 3, 4):
                raise CustomSoundError("WAV must use 8, 16, 24, or 32-bit PCM")
            if rate < 8_000 or rate > 192_000:
                raise CustomSoundError("WAV sample rate must be between 8 kHz and 192 kHz")
            duration = frames_count / float(rate)
            if duration <= 0.0 or duration > MAX_DURATION_SECONDS:
                raise CustomSoundError("custom sound must be longer than 0 and at most 30 seconds")
            frames = input_wav.readframes(frames_count)
    except CustomSoundError:
        raise
    except (OSError, EOFError, wave.Error) as exc:
        raise CustomSoundError("could not read PCM WAV: {0}".format(exc)) from exc

    samples = _resample(_decode_mono(frames, channels, width), rate)
    peak = max((abs(sample) for sample in samples), default=0.0)
    if peak < 1e-5:
        raise CustomSoundError("custom sound is silent")
    normalization = 0.95 / peak
    normalized = [max(-0.95, min(0.95, sample * normalization)) for sample in samples]

    display_name = _clean_name(name or source.stem)
    sounds = load_custom_sounds(root)
    if requested_id:
        sound_id = normalize_custom_id(requested_id)
        if sound_id in sounds:
            raise CustomSoundError("custom sound already exists: {0}".format(sound_id))
    else:
        base = _slugify(display_name)
        sound_id = CUSTOM_PREFIX + base
        suffix = 2
        while sound_id in sounds:
            tail = "-{0}".format(suffix)
            sound_id = CUSTOM_PREFIX + base[:48 - len(tail)].rstrip("-") + tail
            suffix += 1

    slug = sound_id[len(CUSTOM_PREFIX):]
    target = custom_audio_dir(root) / (slug + ".wav")
    _write_pcm16(target, normalized)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    metadata = {
        "id": sound_id,
        "name": display_name,
        "original_filename": source.name,
        "duration_seconds": round(len(normalized) / TARGET_RATE, 3),
        "sample_rate": TARGET_RATE,
        "sha256": digest,
        "imported_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "path": str(target),
    }
    sounds[sound_id] = metadata
    try:
        _write_registry(root, sounds)
    except Exception:
        try:
            target.unlink()
        except OSError:
            pass
        raise
    return metadata


def custom_sound(root: Path, sound_id: str) -> Optional[Dict[str, Any]]:
    try:
        normalized = normalize_custom_id(sound_id)
    except CustomSoundError:
        return None
    return load_custom_sounds(root).get(normalized)


def render_custom_sound(root: Path, sound_id: str, path: Path, volume: float) -> Path:
    metadata = custom_sound(root, sound_id)
    if metadata is None:
        raise CustomSoundError("unknown custom sound: {0}".format(sound_id))
    source = Path(metadata["path"])
    if not source.is_file():
        raise CustomSoundError("custom sound file is missing: {0}".format(sound_id))
    _write_pcm16(path, _read_canonical(source), volume)
    return path


def remove_custom_sound(root: Path, sound_id: str) -> Optional[Dict[str, Any]]:
    normalized = normalize_custom_id(sound_id)
    sounds = load_custom_sounds(root)
    metadata = sounds.pop(normalized, None)
    if metadata is None:
        return None
    _write_registry(root, sounds)
    source = Path(metadata["path"])
    try:
        source.unlink()
    except FileNotFoundError:
        pass
    cache_name = "custom-{0}.wav".format(normalized[len(CUSTOM_PREFIX):])
    sounds_cache = root / "sounds"
    if sounds_cache.is_dir():
        for cached in sounds_cache.rglob(cache_name):
            try:
                cached.unlink()
            except FileNotFoundError:
                pass
    return metadata
