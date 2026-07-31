"""Command-line interface for Session Alarm."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shlex
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from . import __version__
from .catalog import (
    GROUP_NAMES,
    SOUNDS,
    SOUND_BY_ID,
    localized_description,
    localized_name,
)
from .custom import (
    CustomSoundError,
    import_custom_sound,
    load_custom_sounds,
    normalize_custom_id,
    remove_custom_sound,
)
from .core import (
    ConfigError,
    EVENTS,
    config_path,
    default_config,
    detect_language,
    ensure_sound,
    load_config,
    notify_event,
    play_file,
    play_file_blocking,
    reset_config,
    run_hook,
    save_config,
    sound_exists,
    sound_name,
    state_dir,
)


EVENT_NAMES = {
    "en": {
        "attention": "Needs input",
        "complete": "Work complete",
        "error": "Error",
        "session_end": "Session ended",
    },
    "ko": {
        "attention": "사용자 입력 필요",
        "complete": "작업 완료",
        "error": "오류 발생",
        "session_end": "세션 종료",
    },
}


def _print(message: str = "") -> None:
    print(message)


def _error(message: str) -> None:
    print(message, file=sys.stderr)


def _language(value: Optional[str]) -> str:
    return value if value in ("ko", "en") else detect_language()


def _parse_volume(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("volume must be a number from 0 to 100") from exc
    if number > 1.0:
        number /= 100.0
    if not 0.0 <= number <= 1.0:
        raise argparse.ArgumentTypeError("volume must be from 0 to 100")
    return number


def _parse_toggle(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in ("on", "true", "yes", "1", "켜기", "사용"):
        return True
    if normalized in ("off", "false", "no", "0", "끄기", "미사용"):
        return False
    raise argparse.ArgumentTypeError("expected on or off")


def _catalog_rows(language: str) -> List[Dict[str, str]]:
    rows = []
    for sound in SOUNDS:
        rows.append(
            {
                "id": sound.sound_id,
                "group": sound.group,
                "name": localized_name(sound, language),
                "description": localized_description(sound, language),
            }
        )
    return rows


def _custom_rows() -> List[Dict[str, str]]:
    rows = []
    for sound_id, metadata in sorted(
        load_custom_sounds(state_dir()).items(),
        key=lambda item: (str(item[1]["name"]).casefold(), item[0]),
    ):
        rows.append(
            {
                "id": sound_id,
                "group": "custom",
                "name": str(metadata["name"]),
                "description": "사용자 WAV" if detect_language() == "ko" else "User WAV",
            }
        )
    return rows


def _all_rows(language: str) -> List[Dict[str, str]]:
    rows = _catalog_rows(language)
    for row in _custom_rows():
        row["description"] = "사용자 WAV" if language == "ko" else "User WAV"
        rows.append(row)
    return rows


def _show_catalog(language: str) -> None:
    rows = _all_rows(language)
    current_group = None
    for index, row in enumerate(rows, 1):
        if row["group"] != current_group:
            current_group = row["group"]
            group_label = (
                "내 사운드" if language == "ko" else "My sounds"
            ) if current_group == "custom" else GROUP_NAMES[current_group][
                1 if language == "ko" else 0
            ]
            _print("\n[{0}]".format(group_label))
        _print(
            "{0:>2}. {1:<12} {2} — {3}".format(
                index,
                row["id"],
                row["name"],
                row["description"],
            )
        )


def command_catalog(args: argparse.Namespace) -> int:
    language = _language(args.language)
    rows = _all_rows(language)
    if args.json:
        _print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        _print(
            "12 short CC0 recordings of real animals"
            if language == "en"
            else "실제 동물을 녹음한 짧은 CC0 알림음 12종"
        )
        _show_catalog(language)
    return 0


def _preview(sound_id: str, volume: float) -> bool:
    path = ensure_sound(sound_id, volume)
    played, reason = play_file(path)
    if not played:
        _error("Could not play {0}: {1}".format(sound_id, reason))
    return played


def command_preview(args: argparse.Namespace) -> int:
    if not sound_exists(args.sound):
        _error("Unknown sound: {0}".format(args.sound))
        return 2
    volume = _parse_volume(args.volume)
    _print("Previewing {0} at {1}%".format(args.sound, int(round(volume * 100))))
    return 0 if _preview(args.sound, volume) else 1


def command_preview_all(args: argparse.Namespace) -> int:
    language = _language(args.language)
    volume = _parse_volume(args.volume)
    if args.gap < 0.0 or args.gap > 5.0:
        _error("--gap must be between 0 and 5 seconds")
        return 2
    selected = [
        sound for sound in SOUNDS
        if args.group == "all" or sound.group == args.group
    ]
    _print(
        "{0}개 사운드를 순서대로 재생합니다. 중단: Ctrl+C".format(len(selected))
        if language == "ko"
        else "Playing {0} sounds in order. Press Ctrl+C to stop.".format(len(selected))
    )
    try:
        for index, sound in enumerate(selected, 1):
            _print(
                "[{0:02d}/{1:02d}] {2} ({3})".format(
                    index,
                    len(selected),
                    localized_name(sound, language),
                    sound.sound_id,
                )
            )
            path = ensure_sound(sound.sound_id, volume)
            played, reason = play_file_blocking(path)
            if not played:
                _error("Could not play {0}: {1}".format(sound.sound_id, reason))
                return 1
            if args.gap and index != len(selected):
                time.sleep(args.gap)
    except KeyboardInterrupt:
        _print("\n재생을 중단했습니다." if language == "ko" else "\nPreview stopped.")
        return 130
    _print("전체 재생 완료" if language == "ko" else "Preview complete.")
    return 0


def _prompt(prompt: str, default: Optional[str] = None) -> str:
    suffix = " [{0}]".format(default) if default is not None else ""
    value = input("{0}{1}: ".format(prompt, suffix)).strip()
    return value or (default or "")


def _prompt_yes_no(prompt_en: str, prompt_ko: str, default: bool, language: str) -> bool:
    prompt = prompt_ko if language == "ko" else prompt_en
    marker = "Y/n" if default else "y/N"
    while True:
        value = input("{0} [{1}]: ".format(prompt, marker)).strip().lower()
        if not value:
            return default
        if value in ("y", "yes", "예", "네", "ㅇ"):
            return True
        if value in ("n", "no", "아니오", "아니요", "ㄴ"):
            return False
        _print("y/n으로 답해주세요." if language == "ko" else "Please answer y or n.")


def _choose_sound(
    event: str,
    current: str,
    volume: float,
    language: str,
) -> str:
    rows = _all_rows(language)
    event_name = EVENT_NAMES[language][event]
    instructions = (
        "번호로 선택, 'p 번호'로 미리 듣기, 'a WAV경로'로 내 소리 추가, 'l'로 목록, 'q'로 취소"
        if language == "ko"
        else "Choose a number, 'p NUMBER' to preview, 'a WAV_PATH' to add your sound, "
        "'l' to list, or 'q' to cancel"
    )
    _print("\n{0} — {1}".format(event_name, instructions))
    current_index = next(
        index for index, row in enumerate(rows, 1) if row["id"] == current
    )
    while True:
        value = _prompt(
            "사운드" if language == "ko" else "Sound",
            str(current_index),
        )
        if value.lower() == "q":
            raise KeyboardInterrupt
        if value.lower() == "l":
            _show_catalog(language)
            rows = _all_rows(language)
            continue
        add_match = re.match(r"^(?:a|add)\s+(.+)$", value, re.IGNORECASE)
        if add_match:
            try:
                path_parts = shlex.split(add_match.group(1))
                if len(path_parts) != 1:
                    raise CustomSoundError("enter one WAV file path")
                metadata = import_custom_sound(state_dir(), Path(path_parts[0]))
                _print(
                    "내 사운드를 추가했습니다: {0} ({1})".format(
                        metadata["name"], metadata["id"]
                    )
                    if language == "ko"
                    else "Added your sound: {0} ({1})".format(
                        metadata["name"], metadata["id"]
                    )
                )
                _preview(str(metadata["id"]), volume)
                return str(metadata["id"])
            except (CustomSoundError, OSError, ValueError) as exc:
                _print(
                    "추가할 수 없습니다: {0}".format(exc)
                    if language == "ko"
                    else "Could not add sound: {0}".format(exc)
                )
            continue
        preview_match = re.fullmatch(r"p\s*(\d+)", value.lower())
        if preview_match:
            number = int(preview_match.group(1))
            if 1 <= number <= len(rows):
                _preview(rows[number - 1]["id"], volume)
            else:
                _print("1-{0}".format(len(rows)))
            continue
        if value.isdigit() and 1 <= int(value) <= len(rows):
            selected = rows[int(value) - 1]["id"]
            _preview(selected, volume)
            return selected
        if sound_exists(value):
            _preview(value, volume)
            return value
        _print(
            "올바른 번호 또는 사운드 ID를 입력하세요."
            if language == "ko"
            else "Enter a valid number or sound ID."
        )


def _prompt_volume(current: float, language: str) -> float:
    while True:
        value = _prompt(
            "음량 (0-100)" if language == "ko" else "Volume (0-100)",
            str(int(round(current * 100))),
        )
        try:
            return _parse_volume(value)
        except argparse.ArgumentTypeError as exc:
            _print(str(exc))


def _prompt_time(label_en: str, label_ko: str, current: str, language: str) -> str:
    while True:
        value = _prompt(label_ko if language == "ko" else label_en, current)
        if re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
            return value
        _print("HH:MM 형식으로 입력하세요." if language == "ko" else "Use HH:MM format.")


def _prepare_sounds(config: Dict[str, Any]) -> None:
    for sound_id in set(config["sounds"].values()):
        ensure_sound(sound_id, config["volume"])


def command_setup(args: argparse.Namespace) -> int:
    if not sys.stdin.isatty():
        _error(
            "Interactive setup needs a terminal. Use 'configure' for non-interactive setup."
        )
        return 2
    language = _language(args.language)
    existing = load_config()
    config = existing or default_config(language)
    config["language"] = language

    if language == "ko":
        _print("Session Alarm 최초 설정")
        _print("실제 동물 CC0 알림음 12종과 직접 만든 또는 허가받은 WAV를 사용할 수 있습니다.")
    else:
        _print("Session Alarm first-run setup")
        _print("Choose from 12 real-animal CC0 recordings or add a WAV you may use.")
    _show_catalog(language)

    try:
        config["volume"] = _prompt_volume(config["volume"], language)
        for event in EVENTS:
            config["sounds"][event] = _choose_sound(
                event,
                config["sounds"][event],
                config["volume"],
                language,
            )
        config["desktop_notifications"] = _prompt_yes_no(
            "Show desktop notifications too?",
            "데스크톱 알림도 표시할까요?",
            config["desktop_notifications"],
            language,
        )
        quiet_enabled = _prompt_yes_no(
            "Enable quiet hours?",
            "방해금지 시간을 사용할까요?",
            config["quiet_hours"]["enabled"],
            language,
        )
        config["quiet_hours"]["enabled"] = quiet_enabled
        if quiet_enabled:
            config["quiet_hours"]["start"] = _prompt_time(
                "Quiet hours start",
                "방해금지 시작",
                config["quiet_hours"]["start"],
                language,
            )
            config["quiet_hours"]["end"] = _prompt_time(
                "Quiet hours end",
                "방해금지 종료",
                config["quiet_hours"]["end"],
                language,
            )
    except (EOFError, KeyboardInterrupt):
        _print("\n설정을 취소했습니다." if language == "ko" else "\nSetup cancelled.")
        return 130

    config["configured_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    path = save_config(config)
    _prepare_sounds(config)
    _print(
        "\n설정을 저장했습니다: {0}".format(path)
        if language == "ko"
        else "\nConfiguration saved: {0}".format(path)
    )
    return 0


def _parse_quiet_hours(value: str) -> Dict[str, Any]:
    if value.lower() == "off":
        return {"enabled": False, "start": "22:00", "end": "08:00"}
    match = re.fullmatch(
        r"((?:[01]\d|2[0-3]):[0-5]\d)-((?:[01]\d|2[0-3]):[0-5]\d)",
        value,
    )
    if not match:
        raise argparse.ArgumentTypeError(
            "quiet hours must be 'off' or HH:MM-HH:MM"
        )
    return {"enabled": True, "start": match.group(1), "end": match.group(2)}


def command_configure(args: argparse.Namespace) -> int:
    config = load_config() or default_config(args.language)
    if args.language:
        config["language"] = args.language
    if args.volume is not None:
        config["volume"] = _parse_volume(args.volume)
    if args.notifications is not None:
        config["desktop_notifications"] = _parse_toggle(args.notifications)
    if args.enabled is not None:
        config["enabled"] = _parse_toggle(args.enabled)
    if args.quiet_hours is not None:
        config["quiet_hours"] = _parse_quiet_hours(args.quiet_hours)
    for event in EVENTS:
        value = getattr(args, event)
        if value is not None:
            if not sound_exists(value):
                _error("Unknown sound for {0}: {1}".format(event, value))
                return 2
            config["sounds"][event] = value
    config["configured_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        path = save_config(config)
    except ConfigError as exc:
        _error(str(exc))
        return 2
    _prepare_sounds(config)
    _print(str(path))
    return 0


def command_status(args: argparse.Namespace) -> int:
    config = load_config()
    payload = {
        "configured": config is not None,
        "config_path": str(config_path()),
        "state_dir": str(state_dir()),
        "config": config,
        "catalog_size": len(SOUNDS),
    }
    if args.json:
        _print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if config is None:
        _print("Session Alarm is not configured.")
        _print("Run: session-alarm setup")
        return 1
    language = config["language"]
    _print("Session Alarm {0}".format(__version__))
    _print("Config: {0}".format(config_path()))
    _print("Enabled: {0}".format(config["enabled"]))
    _print("Volume: {0}%".format(int(round(config["volume"] * 100))))
    _print("Desktop notifications: {0}".format(config["desktop_notifications"]))
    _print("Sounds:")
    for event in EVENTS:
        sound_id = config["sounds"][event]
        if sound_id in SOUND_BY_ID:
            sound = SOUND_BY_ID[sound_id]
            label = localized_name(sound, language)
        else:
            label = sound_name(sound_id)
        _print(
            "  {0}: {1} ({2})".format(
                EVENT_NAMES[language][event],
                label,
                sound_id,
            )
        )
    quiet = config["quiet_hours"]
    quiet_text = (
        "{0}-{1}".format(quiet["start"], quiet["end"])
        if quiet["enabled"]
        else "off"
    )
    _print("Quiet hours: {0}".format(quiet_text))
    return 0


def command_test(args: argparse.Namespace) -> int:
    config = load_config()
    if config is None:
        _error("Session Alarm is not configured. Run setup first.")
        return 2
    events: Iterable[str] = EVENTS if args.event == "all" else (args.event,)
    result = 0
    for event in events:
        played, reason = notify_event(event, "manual", force=True, config=config)
        _print("{0}: {1}".format(event, reason))
        if not played:
            result = 1
    return result


def command_reset(args: argparse.Namespace) -> int:
    if not args.yes:
        _error("Refusing to reset without --yes.")
        return 2
    removed = reset_config()
    _print("Configuration removed." if removed else "No configuration found.")
    return 0


def command_custom_add(args: argparse.Namespace) -> int:
    try:
        metadata = import_custom_sound(
            state_dir(),
            Path(args.file),
            name=args.name,
            requested_id=args.id,
        )
    except (CustomSoundError, OSError) as exc:
        _error(str(exc))
        return 2
    _print(
        json.dumps(metadata, ensure_ascii=False, indent=2)
        if args.json
        else "Added {0} as {1}".format(metadata["name"], metadata["id"])
    )
    if args.preview:
        return 0 if _preview(str(metadata["id"]), _parse_volume(args.volume)) else 1
    return 0


def command_custom_list(args: argparse.Namespace) -> int:
    sounds = list(load_custom_sounds(state_dir()).values())
    sounds.sort(key=lambda item: (str(item["name"]).casefold(), str(item["id"])))
    if args.json:
        _print(json.dumps(sounds, ensure_ascii=False, indent=2))
        return 0
    if not sounds:
        _print("No custom sounds.")
        return 0
    for metadata in sounds:
        _print(
            "{0:<28} {1} ({2:.2f}s)".format(
                metadata["id"],
                metadata["name"],
                float(metadata["duration_seconds"]),
            )
        )
    return 0


def command_custom_remove(args: argparse.Namespace) -> int:
    try:
        sound_id = normalize_custom_id(args.sound)
    except CustomSoundError as exc:
        _error(str(exc))
        return 2
    config = load_config()
    assigned = [
        event
        for event in EVENTS
        if config is not None and config["sounds"].get(event) == sound_id
    ]
    if assigned:
        _error(
            "Cannot remove {0}; it is assigned to: {1}. Reconfigure those events first.".format(
                sound_id,
                ", ".join(assigned),
            )
        )
        return 2
    if not args.yes:
        _error("Refusing to remove a custom sound without --yes.")
        return 2
    try:
        removed = remove_custom_sound(state_dir(), sound_id)
    except (CustomSoundError, OSError) as exc:
        _error(str(exc))
        return 2
    if removed is None:
        _error("Unknown custom sound: {0}".format(sound_id))
        return 2
    _print("Removed {0} ({1}).".format(removed["name"], sound_id))
    return 0


def command_hook(args: argparse.Namespace) -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            payload = {}
        output = run_hook(payload, args.source)
    except Exception:
        # Hook failures must never block Codex or Claude.
        output = {}
    _print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="session-alarm",
        description="Local animal-sound notifications for Codex and Claude Code.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup = subparsers.add_parser("setup", help="run the interactive first-use wizard")
    setup.add_argument("--language", choices=("en", "ko"))
    setup.set_defaults(func=command_setup)

    catalog = subparsers.add_parser("catalog", help="list all available animal sounds")
    catalog.add_argument("--language", choices=("en", "ko"))
    catalog.add_argument("--json", action="store_true")
    catalog.set_defaults(func=command_catalog)

    preview = subparsers.add_parser("preview", help="preview one animal sound")
    preview.add_argument("sound")
    preview.add_argument("--volume", default=70)
    preview.set_defaults(func=command_preview)

    preview_all = subparsers.add_parser(
        "preview-all",
        help="play the catalog sequentially",
    )
    preview_all.add_argument("--volume", default=45)
    preview_all.add_argument("--language", choices=("en", "ko"))
    preview_all.add_argument(
        "--group",
        choices=("all",) + tuple(GROUP_NAMES),
        default="all",
    )
    preview_all.add_argument("--gap", type=float, default=0.2)
    preview_all.set_defaults(func=command_preview_all)

    custom = subparsers.add_parser(
        "custom",
        help="import and manage your own local WAV notification sounds",
    )
    custom_subparsers = custom.add_subparsers(dest="custom_command", required=True)

    custom_add = custom_subparsers.add_parser("add", help="import a local PCM WAV")
    custom_add.add_argument("file")
    custom_add.add_argument("--name")
    custom_add.add_argument("--id")
    custom_add.add_argument("--preview", action="store_true")
    custom_add.add_argument("--volume", default=70)
    custom_add.add_argument("--json", action="store_true")
    custom_add.set_defaults(func=command_custom_add)

    custom_list = custom_subparsers.add_parser("list", help="list imported sounds")
    custom_list.add_argument("--json", action="store_true")
    custom_list.set_defaults(func=command_custom_list)

    custom_remove = custom_subparsers.add_parser("remove", help="remove an imported sound")
    custom_remove.add_argument("sound")
    custom_remove.add_argument("--yes", action="store_true")
    custom_remove.set_defaults(func=command_custom_remove)

    configure = subparsers.add_parser(
        "configure",
        help="write configuration without the interactive wizard",
    )
    configure.add_argument("--language", choices=("en", "ko"))
    configure.add_argument("--volume")
    configure.add_argument("--notifications", choices=("on", "off"))
    configure.add_argument("--enabled", choices=("on", "off"))
    configure.add_argument("--quiet-hours", help="'off' or HH:MM-HH:MM")
    for event in EVENTS:
        configure.add_argument(
            "--{0}".format(event.replace("_", "-")),
            dest=event,
        )
    configure.set_defaults(func=command_configure)

    status = subparsers.add_parser("status", help="show current configuration")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=command_status)

    test = subparsers.add_parser("test", help="play one configured event or all events")
    test.add_argument("event", nargs="?", choices=EVENTS + ("all",), default="all")
    test.set_defaults(func=command_test)

    reset = subparsers.add_parser("reset", help="remove the saved configuration")
    reset.add_argument("--yes", action="store_true")
    reset.set_defaults(func=command_reset)

    hook = subparsers.add_parser("hook", help=argparse.SUPPRESS)
    hook.add_argument("--source", required=True, choices=("codex", "claude"))
    hook.set_defaults(func=command_hook)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ConfigError as exc:
        _error("Configuration error: {0}".format(exc))
        return 2
    except OSError as exc:
        _error("System error: {0}".format(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
