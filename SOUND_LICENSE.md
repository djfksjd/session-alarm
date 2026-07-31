# Sound provenance and license

## Bundled real-animal sounds

Session Alarm bundles 12 short recordings of real animals. Every selected recording was marked
[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) on its individual
Freesound page when retrieved. CC0 does not require attribution, but Session Alarm keeps the
contributor, exact sound page, Freesound ID, original filename, retrieval date, source-preview
hash, processing recipe, and committed WAV hash for transparency.

Freesound hosts sounds under multiple licenses; this statement applies only to the 12 individually
verified files listed in
[`sources.json`](plugins/session-alarm/assets/sounds/sources.json). It is not a claim that every
sound on Freesound is public domain or that uploader-provided metadata can never be mistaken.

Original-file downloads on Freesound require an account. The committed derivatives were made from
the public high-quality MP3 preview exposed by each selected sound page, not from a claimed
original download. That source type and its SHA-256 are recorded explicitly in the manifest.

The recordings were trimmed and normalized as short mono 16-bit PCM notification WAVs. They are
integrated as functional application assets and are not presented as a standalone stock-audio
library.

Run the offline fail-closed verifier after any asset change:

```bash
python3 plugins/session-alarm/scripts/verify_builtin_sounds.py
```

The verifier checks the exact catalog and file set, file-level SHA-256 values, source and license
fields, and PCM format without downloading anything.

## User-imported sounds

The `custom add` command can copy a user's local WAV into their private Session Alarm data
directory. Those files are never uploaded or added to this repository. Their original rights and
license remain unchanged. Users are responsible for importing only audio they created or are
authorized to use.
