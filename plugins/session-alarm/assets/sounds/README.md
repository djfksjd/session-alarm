# Bundled sound assets

This directory contains 12 short real-animal recordings selected from individual Freesound pages
that identified each recording as CC0 1.0 Universal.

`sources.json` records file-level provenance, exact sound pages, contributor names, original
filenames, public HQ preview URLs and hashes, clip boundaries, processing details, and committed
WAV hashes. The source asset is recorded as a public preview because Freesound requires login for
original-file downloads.

Verify the committed assets without network access:

```bash
python3 plugins/session-alarm/scripts/verify_builtin_sounds.py
```

Do not infer that every Freesound upload is CC0; only the listed assets were individually checked.
