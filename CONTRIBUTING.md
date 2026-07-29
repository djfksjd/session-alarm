# Contributing

Contributions are welcome.

1. Create a feature branch.
2. Keep the runtime dependency-free and compatible with Python 3.9 or newer.
3. Add or update `unittest` coverage.
4. Run `python3 -m unittest discover -s tests -v`.
5. Run both plugin validators described in `README.md`.
6. Open a pull request against `main`.

## Sound contributions

New bundled sounds must come from an exact Pixabay asset page that explicitly displays the
Pixabay Content License. Add the contributor, asset URL, verification date, SHA-256 checksum, and
commercial-use status to `plugins/session-alarm/assets/sounds/sources.json`.

Do not submit media copied from search engines, social networks, broadcasts, videos, celebrity
voices, or any source whose commercial-use and application-integration rights are unclear.
Pixabay files must not be presented as original Session Alarm creations or redistributed as a
standalone sound library. Add localized catalog metadata and tests with each asset.

## Pull requests

`main` is protected. Changes must arrive through a pull request and pass the required CI check.
