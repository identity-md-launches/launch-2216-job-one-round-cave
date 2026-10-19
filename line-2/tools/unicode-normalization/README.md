# Unicode Normalization

Expose Unicode text whose canonical or compatibility-normalized form differs
from the original, with exact UTF-8 byte evidence. This helps a worker review
identifiers that can look stable in one representation but change under a
normalizing system. Python 3.10+ and the standard library are sufficient; the
tool has no network, dependency, environment, sibling-import, or file-writing
behavior.

Run this one command from the repository root:

```sh
python3 -B line-2/tools/unicode-normalization/unicode_normalization.py --demo
```

The demo reports three synthetic normalization findings: a full-width ASCII
letter, a Kelvin sign, and a circled digit. The demo is labeled synthetic,
not an observed attack. Round 36 fixed missed NFC composition between adjacent
Hangul Jamo. The scanner now groups adjacent combining marks and Hangul Jamo,
and advances byte positions in one pass; a 10,000-mark run completes without
the previous repeated-suffix scan. For a real, explicitly selected workspace file:

```sh
python3 -B line-2/tools/unicode-normalization/unicode_normalization.py --file path/to/text.txt
```

Each finding gives the original escaped text, NFC and NFKC forms, scalar names,
the original UTF-8 byte range, and a SHA-256 of that exact source span. Counts
cover the complete input even when `--max-details` limits retained evidence.
Normalization is not inherently malicious, so findings require human review;
the tool does not render text or claim that two fonts will look alike. Inputs
must be strict UTF-8 regular files inside the current workspace and at most
2 MiB. It emits escaped ASCII JSON and never rewrites the selected file.

Observed locally: the demo completed with three findings; four focused tests
passed, including `각` → `각`, exact original-byte evidence, capped counts,
and a long combining run. The tool reports the active Python runtime's Unicode
database version. This is local sequence review, not a whole-label collision
test or a rendered-font comparison.
