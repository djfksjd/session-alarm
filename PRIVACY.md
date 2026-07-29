# Privacy

Session Alarm runs locally and does not include analytics, telemetry, accounts, advertising, or
network requests.

The lifecycle hooks receive event data from Codex or Claude Code. Session Alarm uses only:

- the hook event name;
- the notification subtype, when provided;
- the final assistant message solely to distinguish a question from a completed turn; and
- whether background work is still active.

Conversation text, prompts, file contents, repository data, and hook payloads are not stored or
transmitted. The final assistant message is evaluated in memory and discarded.

Configuration is stored locally:

- macOS and Linux: `~/.config/session-alarm/config.json`, or
  `$XDG_CONFIG_HOME/session-alarm/config.json`
- Windows: `%APPDATA%\session-alarm\config.json`
- Tests and advanced setups may override the directory with `SESSION_ALARM_HOME`.

Generated WAV cache files, user-imported custom WAVs, and a small deduplication timestamp are
stored beside the configuration. Imported audio is normalized locally and never uploaded.
Desktop notifications contain only generic status text such as “Claude Code needs your input.”
