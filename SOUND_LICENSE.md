# Sound provenance and license

Session Alarm contains **no sampled, downloaded, scraped, celebrity, broadcast, meme, or
third-party audio**. The 40-sound catalog is generated deterministically from the original DSP
recipes in [`catalog.py`](plugins/session-alarm/session_alarm/catalog.py).

The synthesis engine models pitch contours, harmonic excitation, vocal formants, filtered breath,
amplitude envelopes, tremolo, and simple acoustic echoes at 44.1 kHz. Stock-media files are not
included, transformed, embedded, or required at runtime.

The synthesis code is covered by the repository's MIT License. To the extent that copyright or
related rights may exist in WAV files produced solely by these recipes, the project author
dedicates those generated audio outputs to the public domain under
[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/).

Animal names describe the original sound design's intended character. They do not claim that a
generated effect is a recording of that animal.

Sound contributions must be original recipes. Pull requests containing recordings, extracted
samples, model-generated audio of unclear provenance, or imitations of identifiable copyrighted
clips will not be accepted.
