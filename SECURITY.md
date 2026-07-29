# Security policy

## Supported versions

Security fixes are provided for the latest release on `main`.

## Reporting a vulnerability

Please use GitHub's private **Security advisory** flow instead of opening a public issue. Include the
affected version, operating system, agent host, reproduction steps, and expected impact.

## Hook security model

Session Alarm hooks execute a bundled local Python script with the current user's permissions.
Review the hook definitions before trusting them:

- Codex: `plugins/session-alarm/hooks/hooks.json`
- Claude Code: `plugins/session-alarm/hooks/claude.json`

The hook engine does not execute values from hook payloads, invoke a shell with payload content,
read transcripts from disk, or make network requests.
