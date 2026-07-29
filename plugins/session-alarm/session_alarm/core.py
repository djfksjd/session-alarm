"""Configuration, event classification, playback, and local notifications."""

from __future__ import annotations

import datetime as dt
import json
import locale
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from . import __version__
from .catalog import SOUND_BY_ID, SOUND_PACK_VERSION, render_wav
from .custom import (
    CUSTOM_PREFIX,
    CustomSoundError,
    custom_sound,
    normalize_custom_id,
    render_custom_sound,
)


SCHEMA_VERSION = 1
EVENTS = ("attention", "complete", "error", "session_end")
DEFAULT_SOUNDS = {
    "attention": "duck",
    "complete": "rooster",
    "error": "frog",
    "session_end": "owl",
}

EVENT_COPY = {
    "en": {
        "attention": ("Session Alarm", "{source} needs your input"),
        "complete": ("Session Alarm", "{source} finished working"),
        "error": ("Session Alarm", "{source} stopped with an error"),
        "session_end": ("Session Alarm", "{source} session ended"),
    },
    "ko": {
        "attention": ("Session Alarm", "{source}에서 사용자 입력이 필요합니다"),
        "complete": ("Session Alarm", "{source} 작업이 완료되었습니다"),
        "error": ("Session Alarm", "{source} 작업이 오류로 중단되었습니다"),
        "session_end": ("Session Alarm", "{source} 세션이 종료되었습니다"),
    },
}

SOURCE_NAMES = {
    "codex": "Codex",
    "claude": "Claude Code",
    "manual": "Session Alarm",
}


class ConfigError(ValueError):
    """Raised when persisted configuration is invalid."""


def detect_language() -> str:
    override = os.environ.get("SESSION_ALARM_LANGUAGE", "").strip().lower()
    if override in ("ko", "en"):
        return override
    candidates = [
        os.environ.get("LC_ALL", ""),
        os.environ.get("LC_MESSAGES", ""),
        os.environ.get("LANG", ""),
    ]
    try:
        candidates.append(locale.getdefaultlocale()[0] or "")
    except (AttributeError, ValueError):
        pass
    return "ko" if any(value.lower().startswith("ko") for value in candidates) else "en"


def state_dir() -> Path:
    override = os.environ.get("SESSION_ALARM_HOME")
    if override:
        return Path(override).expanduser().resolve()
    if os.name == "nt":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / "session-alarm"
        return Path.home() / "AppData" / "Roaming" / "session-alarm"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg).expanduser() / "session-alarm"
    return Path.home() / ".config" / "session-alarm"


def config_path() -> Path:
    return state_dir() / "config.json"


def runtime_path() -> Path:
    return state_dir() / "runtime.json"


def sound_exists(sound_id: Any) -> bool:
    if not isinstance(sound_id, str):
        return False
    if sound_id in SOUND_BY_ID:
        return True
    if not sound_id.startswith(CUSTOM_PREFIX):
        return False
    try:
        if normalize_custom_id(sound_id) != sound_id:
            return False
        metadata = custom_sound(state_dir(), sound_id)
    except CustomSoundError:
        return False
    return metadata is not None and Path(metadata["path"]).is_file()


def sound_name(sound_id: str) -> str:
    if sound_id in SOUND_BY_ID:
        return sound_id
    try:
        metadata = custom_sound(state_dir(), sound_id)
    except CustomSoundError:
        metadata = None
    return str(metadata["name"]) if metadata else sound_id


def default_config(language: Optional[str] = None) -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "version": __version__,
        "language": language or detect_language(),
        "enabled": True,
        "volume": 0.7,
        "desktop_notifications": True,
        "sounds": dict(DEFAULT_SOUNDS),
        "quiet_hours": {
            "enabled": False,
            "start": "22:00",
            "end": "08:00",
        },
        "configured_at": None,
    }


def _validate_time(value: str, field_name: str) -> None:
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
        raise ConfigError("{0} must use 24-hour HH:MM format".format(field_name))


def validate_config(value: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError("configuration must be a JSON object")
    config = default_config(value.get("language") if isinstance(value.get("language"), str) else None)
    config.update(value)

    if config.get("schema_version") != SCHEMA_VERSION:
        raise ConfigError("unsupported schema_version")
    if config.get("language") not in ("en", "ko"):
        raise ConfigError("language must be 'en' or 'ko'")
    if not isinstance(config.get("enabled"), bool):
        raise ConfigError("enabled must be boolean")
    if not isinstance(config.get("desktop_notifications"), bool):
        raise ConfigError("desktop_notifications must be boolean")

    try:
        volume = float(config.get("volume"))
    except (TypeError, ValueError) as exc:
        raise ConfigError("volume must be a number") from exc
    if not 0.0 <= volume <= 1.0:
        raise ConfigError("volume must be between 0.0 and 1.0")
    config["volume"] = volume

    sounds = config.get("sounds")
    if not isinstance(sounds, dict):
        raise ConfigError("sounds must be an object")
    normalized_sounds: Dict[str, str] = {}
    for event in EVENTS:
        sound_id = sounds.get(event)
        if not sound_exists(sound_id):
            raise ConfigError("unknown sound for {0}: {1}".format(event, sound_id))
        normalized_sounds[event] = sound_id
    config["sounds"] = normalized_sounds

    quiet = config.get("quiet_hours")
    if not isinstance(quiet, dict):
        raise ConfigError("quiet_hours must be an object")
    quiet_enabled = quiet.get("enabled")
    if not isinstance(quiet_enabled, bool):
        raise ConfigError("quiet_hours.enabled must be boolean")
    quiet_start = str(quiet.get("start", "22:00"))
    quiet_end = str(quiet.get("end", "08:00"))
    _validate_time(quiet_start, "quiet_hours.start")
    _validate_time(quiet_end, "quiet_hours.end")
    config["quiet_hours"] = {
        "enabled": quiet_enabled,
        "start": quiet_start,
        "end": quiet_end,
    }
    return config


def load_config() -> Optional[Dict[str, Any]]:
    path = config_path()
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError("could not read {0}: {1}".format(path, exc)) from exc
    return validate_config(value)


def save_config(config: Dict[str, Any]) -> Path:
    validated = validate_config(config)
    directory = state_dir()
    directory.mkdir(parents=True, exist_ok=True)
    target = config_path()
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".config-",
        suffix=".json",
        dir=str(directory),
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(validated, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, target)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise
    return target


def reset_config() -> bool:
    path = config_path()
    if not path.exists():
        return False
    path.unlink()
    return True


def _parse_clock(value: str) -> int:
    hours, minutes = value.split(":", 1)
    return int(hours) * 60 + int(minutes)


def quiet_now(config: Dict[str, Any], now: Optional[dt.datetime] = None) -> bool:
    quiet = config["quiet_hours"]
    if not quiet["enabled"]:
        return False
    current = now or dt.datetime.now()
    minute = current.hour * 60 + current.minute
    start = _parse_clock(quiet["start"])
    end = _parse_clock(quiet["end"])
    if start == end:
        return True
    if start < end:
        return start <= minute < end
    return minute >= start or minute < end


def sound_path(sound_id: str, volume: float) -> Path:
    volume_key = int(round(volume * 100))
    if sound_id.startswith(CUSTOM_PREFIX):
        try:
            if normalize_custom_id(sound_id) != sound_id:
                raise ConfigError("invalid custom sound ID: {0}".format(sound_id))
        except CustomSoundError as exc:
            raise ConfigError(str(exc)) from exc
        filename = "custom-{0}.wav".format(sound_id[len(CUSTOM_PREFIX):])
    elif sound_id in SOUND_BY_ID:
        filename = "{0}.wav".format(sound_id)
    else:
        raise ConfigError("unknown sound: {0}".format(sound_id))
    return (
        state_dir()
        / "sounds"
        / "pack-v{0}".format(SOUND_PACK_VERSION)
        / "v{0:03d}".format(volume_key)
        / filename
    )


def ensure_sound(sound_id: str, volume: float) -> Path:
    if not 0.0 <= volume <= 1.0:
        raise ValueError("volume must be between 0.0 and 1.0")
    path = sound_path(sound_id, volume)
    if not path.exists():
        if sound_id in SOUND_BY_ID:
            render_wav(sound_id, path, volume)
        elif sound_id.startswith(CUSTOM_PREFIX):
            try:
                render_custom_sound(state_dir(), sound_id, path, volume)
            except CustomSoundError as exc:
                raise ConfigError(str(exc)) from exc
        else:
            raise ConfigError("unknown sound: {0}".format(sound_id))
    return path


def _detached_kwargs() -> Dict[str, Any]:
    kwargs: Dict[str, Any] = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if os.name == "nt":
        kwargs["creationflags"] = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "DETACHED_PROCESS", 0)
        )
    else:
        kwargs["start_new_session"] = True
    return kwargs


def _player_command(path: Path) -> Optional[list]:
    command = None
    if sys.platform == "darwin" and shutil.which("afplay"):
        command = ["afplay", str(path)]
    elif os.name == "nt":
        worker = (
            "import sys,winsound;"
            "winsound.PlaySound(sys.argv[1],winsound.SND_FILENAME)"
        )
        command = [sys.executable, "-c", worker, str(path)]
    elif shutil.which("paplay"):
        command = ["paplay", str(path)]
    elif shutil.which("aplay"):
        command = ["aplay", "-q", str(path)]
    elif shutil.which("ffplay"):
        command = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)]
    return command


def play_file(path: Path) -> Tuple[bool, str]:
    if os.environ.get("SESSION_ALARM_DISABLE_AUDIO") == "1":
        return True, "audio disabled by environment"

    command = _player_command(path)
    if command is None:
        return False, "no supported audio player found"
    try:
        subprocess.Popen(command, **_detached_kwargs())
    except OSError as exc:
        return False, str(exc)
    return True, "playing"


def play_file_blocking(path: Path) -> Tuple[bool, str]:
    """Play a WAV to completion, used for ordered catalog previews."""
    if os.environ.get("SESSION_ALARM_DISABLE_AUDIO") == "1":
        return True, "audio disabled by environment"

    command = _player_command(path)
    if command is None:
        return False, "no supported audio player found"
    try:
        completed = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError as exc:
        return False, str(exc)
    if completed.returncode != 0:
        return False, "player exited with status {0}".format(completed.returncode)
    return True, "played"


def _escape_applescript(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def show_desktop_notification(title: str, message: str) -> Tuple[bool, str]:
    if os.environ.get("SESSION_ALARM_DISABLE_NOTIFICATIONS") == "1":
        return True, "desktop notifications disabled by environment"

    command = None
    if sys.platform == "darwin" and shutil.which("osascript"):
        script = 'display notification "{0}" with title "{1}"'.format(
            _escape_applescript(message),
            _escape_applescript(title),
        )
        command = ["osascript", "-e", script]
    elif os.name == "nt" and shutil.which("powershell.exe"):
        safe_title = title.replace("'", "''")
        safe_message = message.replace("'", "''")
        script = (
            "[Windows.UI.Notifications.ToastNotificationManager, "
            "Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; "
            "$xml = New-Object Windows.Data.Xml.Dom.XmlDocument; "
            "$xml.LoadXml(\"<toast><visual><binding template='ToastGeneric'>"
            "<text>{0}</text><text>{1}</text></binding></visual></toast>\"); "
            "$toast = [Windows.UI.Notifications.ToastNotification]::new($xml); "
            "[Windows.UI.Notifications.ToastNotificationManager]::"
            "CreateToastNotifier('Session Alarm').Show($toast)"
        ).format(safe_title, safe_message)
        command = ["powershell.exe", "-NoProfile", "-Command", script]
    elif shutil.which("notify-send"):
        command = ["notify-send", title, message]

    if command is None:
        return False, "no supported desktop notification command found"
    try:
        subprocess.Popen(command, **_detached_kwargs())
    except OSError as exc:
        return False, str(exc)
    return True, "notifying"


def _read_runtime() -> Dict[str, Any]:
    try:
        with runtime_path().open("r", encoding="utf-8") as handle:
            value = json.load(handle)
            return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _write_runtime(value: Dict[str, Any]) -> None:
    directory = state_dir()
    directory.mkdir(parents=True, exist_ok=True)
    target = runtime_path()
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".runtime-",
        suffix=".json",
        dir=str(directory),
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False)
            handle.write("\n")
        os.replace(temporary_name, target)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def is_duplicate(event: str, source: str, *, window_seconds: float = 1.5) -> bool:
    now = time.time()
    previous = _read_runtime()
    duplicate = (
        previous.get("event") == event
        and previous.get("source") == source
        and isinstance(previous.get("timestamp"), (int, float))
        and now - float(previous["timestamp"]) < window_seconds
    )
    _write_runtime({"event": event, "source": source, "timestamp": now})
    return duplicate


def notify_event(
    event: str,
    source: str,
    *,
    force: bool = False,
    config: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    if event not in EVENTS:
        return False, "unknown event: {0}".format(event)
    active = config if config is not None else load_config()
    if active is None:
        return False, "not configured"
    if not active["enabled"] and not force:
        return False, "disabled"
    if quiet_now(active) and not force:
        return False, "quiet hours"
    if is_duplicate(event, source) and not force:
        return False, "duplicate"

    sound_id = active["sounds"][event]
    path = ensure_sound(sound_id, active["volume"])
    played, play_reason = play_file(path)

    notification_reason = "disabled"
    if active["desktop_notifications"]:
        language = active["language"]
        title, message_template = EVENT_COPY[language][event]
        source_name = SOURCE_NAMES.get(source, source.title())
        _, notification_reason = show_desktop_notification(
            title,
            message_template.format(source=source_name),
        )
    return played, "{0}; notification: {1}".format(play_reason, notification_reason)


_QUESTION_PATTERNS = (
    r"\?$",
    r"\?\s*(?:\n|$)",
    r"\b(?:please choose|which do you prefer|which would you like|let me know|"
    r"should i|would you like|can you confirm|need your input)\b",
    r"(?:선택해\s*주세요|골라\s*주세요|알려\s*주세요|확인해\s*주세요|"
    r"어느\s+것|무엇으로|어떻게\s+할까요|진행할까요|괜찮을까요|하시겠어요)",
)


def stop_needs_input(message: Any) -> bool:
    if not isinstance(message, str) or not message.strip():
        return False
    tail = message.strip()[-700:].lower()
    return any(re.search(pattern, tail, re.IGNORECASE | re.MULTILINE) for pattern in _QUESTION_PATTERNS)


_ERROR_PATTERNS = (
    r"^(?:error|failure|failed)\s*:",
    r"\b(?:task|build|test|command|request|operation|deployment|installation)\s+"
    r"(?:has\s+)?(?:failed|errored)\b",
    r"\b(?:could not|couldn't|unable to)\s+(?:finish|complete|continue|proceed)\b",
    r"(?:작업|빌드|테스트|명령|요청|배포|설치).{0,18}(?:실패|오류|중단)",
    r"(?:완료|진행|계속).{0,8}(?:하지 못|할 수 없)",
    r"오류로.{0,12}(?:중단|종료)",
)


def stop_has_error(message: Any) -> bool:
    if not isinstance(message, str) or not message.strip():
        return False
    tail = message.strip()[-700:].lower()
    return any(re.search(pattern, tail, re.IGNORECASE | re.MULTILINE) for pattern in _ERROR_PATTERNS)


def event_from_hook(payload: Dict[str, Any]) -> Optional[str]:
    hook_name = payload.get("hook_event_name")
    if hook_name == "PermissionRequest":
        return "attention"
    if hook_name == "StopFailure":
        return "error"
    if hook_name == "SessionEnd":
        return "session_end"
    if hook_name == "Notification":
        notification_type = payload.get("notification_type")
        if notification_type in (
            "permission_prompt",
            "elicitation_dialog",
            "agent_needs_input",
        ):
            return "attention"
        if notification_type == "agent_completed":
            return "complete"
        return None
    if hook_name == "Stop":
        if payload.get("stop_hook_active"):
            return None
        if payload.get("background_tasks") or payload.get("session_crons"):
            return None
        if stop_needs_input(payload.get("last_assistant_message")):
            return "attention"
        if stop_has_error(payload.get("last_assistant_message")):
            return "error"
        return "complete"
    return None


def first_run_context(source: str, language: str) -> str:
    if language == "ko":
        return (
            "Session Alarm이 설치되었지만 아직 최초 설정이 완료되지 않았습니다. "
            "본 작업을 시작하기 전에 사용자에게 지금 설정할지 한 번 물어보세요. "
            "동의하면 번들된 session-alarm 스킬을 사용해 네 가지 이벤트의 내장 동물 "
            "소리 또는 사용자의 WAV 파일, 음량, 데스크톱 알림과 방해금지 시간을 "
            "선택하고 설정을 저장하세요."
        )
    return (
        "Session Alarm is installed but its first-run setup is incomplete. "
        "Before starting the requested work, ask once whether the user wants to configure it now. "
        "If they agree, use the bundled session-alarm skill to choose built-in animal sounds or "
        "the user's own WAV files for all four events, volume, desktop notifications, and quiet "
        "hours, then save the configuration."
    )


def run_hook(payload: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Handle one Codex or Claude hook payload and return valid hook JSON."""
    try:
        config = load_config()
    except ConfigError:
        config = None

    hook_name = payload.get("hook_event_name")
    if config is None:
        if hook_name == "SessionStart":
            language = detect_language()
            return {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": first_run_context(source, language),
                }
            }
        return {}

    event = event_from_hook(payload)
    if event is not None:
        try:
            notify_event(event, source, config=config)
        except (ConfigError, OSError, ValueError):
            # Notifications must never block or alter the agent loop.
            pass
    return {}
