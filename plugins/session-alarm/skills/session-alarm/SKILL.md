---
name: session-alarm
description: Configure, preview, test, enable, disable, or troubleshoot the Session Alarm plugin. Use for Session Alarm first-run setup and settings changes; do not invoke for ordinary coding-agent notifications because lifecycle hooks handle those automatically.
---

# Session Alarm configuration

Use the bundled local CLI to manage Session Alarm. Notifications themselves are hook-driven;
this skill exists only for explicit configuration, preview, status, testing, and troubleshooting.

## Locate the CLI

Resolve the plugin root from this `SKILL.md` location: it is two directories above this file.
The entry point is `<plugin-root>/scripts/session_alarm.py`.

- In Claude Code, prefer `session-alarm` when the plugin-provided `bin/` directory is on `PATH`.
- Otherwise run `python3 <absolute-plugin-root>/scripts/session_alarm.py`.
- On Windows, use `py -3 <absolute-plugin-root>\scripts\session_alarm.py`.
- Never download audio or send configuration to a remote service.

## First-run setup

1. Run `catalog --json --language <ko|en>` and use the returned built-in catalog plus any
   previously imported custom sounds.
2. Ask the user to choose one sound for each event:
   - `attention`: the agent needs input or permission.
   - `complete`: the current work or turn finished.
   - `error`: the agent stopped because of an error.
   - `session_end`: the agent session ended.
3. Also ask for volume from 0 to 100, desktop notifications on/off, and optional quiet hours.
   Keep the questions compact and group them in one message when the host supports it.
4. Offer `preview <sound-id> --volume <0-100>` whenever the user wants to hear a candidate.
   If the user wants their own sound, import a local PCM WAV (30 seconds/32 MB maximum) with
   `custom add <path> --name <label> --preview`. Never infer that the user owns rights to an
   arbitrary file; remind them to use audio they created or are licensed to use.
5. Save the choices with one command:

```text
configure --attention <id> --complete <id> --error <id> --session-end <id> \
  --volume <0-100> --notifications <on|off> --quiet-hours <off|HH:MM-HH:MM> \
  --language <ko|en>
```

6. Run `status` and then `test all`. If the environment has no supported audio player, explain
the exact status without changing system packages unless the user asks.

The built-in assets come from Pixabay under the Pixabay Content License and may be used
commercially subject to its prohibited uses. Do not describe them as created by Session Alarm,
public-domain, CC0, or covered by MIT. Direct users to `SOUND_LICENSE.md` for provenance.

## Other operations

- Show settings: `status` or `status --json`
- List sounds: `catalog`
- Preview one sound: `preview <sound-id>`
- Add a local WAV: `custom add <path> --name <label> --preview`
- List imported sounds: `custom list`
- Remove an unassigned imported sound: `custom remove <custom:id> --yes`
- Test configured mappings: `test <attention|complete|error|session_end|all>`
- Temporarily disable: `configure --enabled off`
- Re-enable: `configure --enabled on`
- Reset first-run state: `reset --yes`

Do not edit `config.json` by hand. Use the CLI so settings are validated and written atomically.
