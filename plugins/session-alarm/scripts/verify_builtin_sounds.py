#!/usr/bin/env python3
"""Verify the committed CC0 real-animal sound pack without network access."""

from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
import wave
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = PLUGIN_ROOT / "assets" / "sounds"
MANIFEST_PATH = ASSET_DIR / "sources.json"
EXPECTED_LICENSE = "CC0 1.0 Universal"
EXPECTED_LICENSE_URL = "https://creativecommons.org/publicdomain/zero/1.0/"
EXPECTED_SOURCE_KIND = "freesound_public_hq_mp3_preview"

sys.path.insert(0, str(PLUGIN_ROOT))
from session_alarm.catalog import SAMPLE_RATE, SOUNDS  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_assets() -> int:
    errors: list[str] = []
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"invalid or missing manifest: {exc}", file=sys.stderr)
        return 1

    if manifest.get("schema_version") != 3:
        errors.append("sources.json schema_version must be 3")

    entries = manifest.get("sounds")
    if not isinstance(entries, list):
        entries = []
        errors.append("sources.json sounds must be an array")

    catalog_ids = {sound.sound_id for sound in SOUNDS}
    manifest_ids = {
        entry.get("id")
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }
    if manifest_ids != catalog_ids:
        errors.append(
            "manifest/catalog IDs differ: "
            f"manifest={sorted(manifest_ids)} catalog={sorted(catalog_ids)}"
        )

    expected_files = {f"{sound_id}.wav" for sound_id in catalog_ids}
    actual_files = {path.name for path in ASSET_DIR.glob("*.wav")}
    if actual_files != expected_files:
        errors.append(
            "bundled WAV set differs: "
            f"actual={sorted(actual_files)} expected={sorted(expected_files)}"
        )

    required_fields = {
        "id",
        "file",
        "sha256",
        "provenance",
        "freesound_id",
        "title",
        "contributor",
        "source_page",
        "original_filename",
        "source_asset_kind",
        "source_preview_url",
        "source_preview_sha256",
        "clip_start_seconds",
        "clip_duration_seconds",
        "retrieved_at",
        "license_name",
        "license_url",
        "attribution_required",
    }

    seen_ids: set[str] = set()
    seen_files: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("manifest entry must be an object")
            continue
        sound_id = str(entry.get("id", ""))
        missing = sorted(required_fields - set(entry))
        if missing:
            errors.append(f"{sound_id or '<unknown>'}: missing fields {missing}")
            continue
        if sound_id in seen_ids:
            errors.append(f"duplicate sound ID: {sound_id}")
        seen_ids.add(sound_id)

        filename = str(entry["file"])
        if filename in seen_files:
            errors.append(f"duplicate sound file: {filename}")
        seen_files.add(filename)
        if filename != f"{sound_id}.wav":
            errors.append(f"{sound_id}: file must be {sound_id}.wav")

        if entry["provenance"] != "freesound_cc0_recording":
            errors.append(f"{sound_id}: unexpected provenance")
        if entry["license_name"] != EXPECTED_LICENSE:
            errors.append(f"{sound_id}: unexpected license name")
        if entry["license_url"] != EXPECTED_LICENSE_URL:
            errors.append(f"{sound_id}: unexpected license URL")
        if entry["attribution_required"] is not False:
            errors.append(f"{sound_id}: attribution_required must be false")
        if entry["source_asset_kind"] != EXPECTED_SOURCE_KIND:
            errors.append(f"{sound_id}: source must identify the public HQ preview")

        freesound_id = entry["freesound_id"]
        expected_page_suffix = f"/sounds/{freesound_id}/"
        if (
            not str(entry["source_page"]).startswith("https://freesound.org/people/")
            or not str(entry["source_page"]).endswith(expected_page_suffix)
        ):
            errors.append(f"{sound_id}: source_page is not an individual Freesound page")
        if not str(entry["source_preview_url"]).startswith(
            f"https://cdn.freesound.org/previews/{str(freesound_id)[:3]}/{freesound_id}_"
        ):
            errors.append(f"{sound_id}: source_preview_url does not match Freesound ID")
        if len(str(entry["source_preview_sha256"])) != 64:
            errors.append(f"{sound_id}: source preview SHA-256 is invalid")

        path = ASSET_DIR / filename
        if not path.is_file():
            errors.append(f"{sound_id}: missing WAV file")
            continue
        if _sha256(path) != entry["sha256"]:
            errors.append(f"{sound_id}: WAV SHA-256 mismatch")

        try:
            with wave.open(str(path), "rb") as source:
                channels = source.getnchannels()
                sample_width = source.getsampwidth()
                sample_rate = source.getframerate()
                compression = source.getcomptype()
                frame_count = source.getnframes()
                frames = source.readframes(frame_count)
        except (OSError, EOFError, wave.Error) as exc:
            errors.append(f"{sound_id}: invalid WAV ({exc})")
            continue

        if (channels, sample_width, sample_rate, compression) != (
            1,
            2,
            SAMPLE_RATE,
            "NONE",
        ):
            errors.append(f"{sound_id}: expected mono 16-bit {SAMPLE_RATE} Hz PCM WAV")
        duration = frame_count / max(sample_rate, 1)
        if not 0.2 < duration < 3.0:
            errors.append(f"{sound_id}: duration {duration:.3f}s is outside 0.2–3.0s")
        samples = [
            value[0] / 32768.0 for value in struct.iter_unpack("<h", frames)
        ]
        if not samples or max(abs(value) for value in samples) <= 0.01:
            errors.append(f"{sound_id}: WAV is silent")
        if samples and (
            not all(math.isfinite(value) for value in samples)
            or abs(sum(samples) / len(samples)) >= 0.08
        ):
            errors.append(f"{sound_id}: WAV sample statistics are invalid")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"Verified {len(entries)} CC0 real-animal WAVs and file-level provenance")
    return 0


if __name__ == "__main__":
    raise SystemExit(check_assets())
