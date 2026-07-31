# Contributing

Contributions are welcome.

1. Create a feature branch.
2. Keep the runtime dependency-free and compatible with Python 3.9 or newer.
3. Add or update `unittest` coverage.
4. Run `python3 -m unittest discover -s tests -v`.
5. Run both plugin validators described in `README.md`.
6. Open a pull request against `main`.

## Sound contributions

Prefer deterministic project-generated tones. Generated files must be reproducible from the
committed generator and record the generator path, stable seed, license, and SHA-256 checksum in
`plugins/session-alarm/assets/sounds/sources.json`.

External bundled sounds require an exact asset page, contributor, license and terms URL,
verification date, SHA-256 checksum, and commercial-use status. Search-result or collection pages
are not acceptable provenance.

Do not submit media copied from search engines, social networks, broadcasts, videos, celebrity
voices, or any source whose commercial-use and application-integration rights are unclear.
External files must not be presented as original Session Alarm creations or redistributed beyond
their license. Generated tones must not be described as real animal recordings. Add localized
catalog metadata and tests with each asset.

## Pull requests

`main` is protected. Changes must arrive through a pull request and pass the required CI check.
