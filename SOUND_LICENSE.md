# Sound provenance and license

## Bundled animal sounds

The 40 built-in WAV files are Pixabay sound effects used under the
[Pixabay Content License](https://pixabay.com/service/license-summary/). Pixabay's official
license and FAQ permit commercial and non-commercial use, subject to the prohibited uses in its
[Terms of Service](https://pixabay.com/service/terms/).

The assets are incorporated as functional notification sounds in the Session Alarm application.
They are not offered as a standalone sound-effect library. Do not extract, sell, sublicense, or
redistribute the audio files separately from Session Alarm.

Pixabay does not require attribution, but Session Alarm identifies the provider and retains a
machine-readable provenance manifest at
[`plugins/session-alarm/assets/sounds/sources.json`](plugins/session-alarm/assets/sounds/sources.json).
That manifest records the license verification date, source pages, integration purpose, and a
SHA-256 checksum for every file.

The elephant file was independently matched to
[“Elephant Trumpeting” by DRAGON-STUDIO](https://pixabay.com/sound-effects/nature-elephant-trumpeting-494313/).
Its normalized waveform correlates 0.998711 with an official source download after encoder-delay
alignment.

The original prototype did not retain exact asset-level URLs for the other 39 files. Their
corresponding Pixabay collection pages and hashes are disclosed in the manifest instead. This is
less complete provenance than the project requires for future contributions; no future sound may
be added without its exact asset URL and contributor.

The repository's MIT License applies to the software and documentation, not to the bundled
Pixabay audio. Nothing in this repository transfers ownership of Pixabay content or grants rights
beyond the Pixabay Content License.

## User-imported sounds

The `custom add` command can copy a user's local WAV into their private Session Alarm data
directory. Those files are never uploaded or added to this repository. Their original rights and
license remain unchanged. Users are responsible for importing only audio they created or are
authorized to use.
