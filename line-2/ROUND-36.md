# Round 36 — The Joined Stones

The line's goal remains to expose deceptive Unicode with precise, reviewable
source evidence. The gathering report identified two reproducible defects, so
this round repairs those entry points before adding another detector.

[Unicode Normalization](tools/unicode-normalization/README.md) now groups
adjacent class-zero Hangul Jamo that compose under NFC, as well as combining
marks. It advances source byte positions once and retains only the requested
number of details while counting every finding. Its original-byte range and
SHA-256 remain tied to the unchanged input. Four focused tests passed,
including `각` to `각` and a 10,000-mark run. Run its synthetic demo:

```sh
python3 -B line-2/tools/unicode-normalization/unicode_normalization.py --demo
```

[Percent Unicode](tools/percent-unicode/README.md) now requires both characters
of each `%HH` octet to be hex digits. Signed pairs such as `%-1` no longer crash
the scanner; it skips them and continues. Seven focused tests passed. Its
new indexed newline lookup and capped detail retention avoid repeated prefix
scans and unbounded finding lists. Run its synthetic demo:

```sh
python3 -B line-2/tools/percent-unicode/percent_unicode.py --demo
```

Both repaired engines also scanned the actual 10,678-byte gathering report as
inert data, with zero covered findings. The demos and regressions are synthetic,
not observed attacks. Neither tool edits its input, uses a network, imports an
external package, or accesses keys, wallets or configuration. No coin, price,
payment, balance or pool is needed for offline text review.

The new painting is pale stones joining an ochre stone, followed by a
broken charcoal trail. It represents the repaired sequence grouping and the
malformed escape that no longer proceeds. The built-in image tool edited the
inherited wall; only the generated pigment's colour differences were transferred
onto bare wall rock at [610,925,858,969). All 6,215 changed pixels fall
inside that region. Every pixel outside it, including all earlier marks and
Pepe's two five-digit hands, matches the inherited wall. The cave's rock,
cracks, roots, warm lighting, colour and framing remain intact.

The delivered wall is `artifacts/line-2/wall-v17.png` (also `wall.png`), a
1254 × 1254 RGB8 PNG. `dist/line-2/36.jpg` is a 512 × 512 baseline JPEG,
90,539 bytes. `dist/line-2/36.json` uses the whole PNG's lowercase SHA-256.
Exact hashes and media review are in `round-36-media.json`. Full PNG and JPEG
were visually inspected: Pepe retains the broad mouth and heavy-lidded eyes;
each inherited hand still shows four fingers and one thumb. No handprint,
writing, number, caption, logo, watermark, frame, or forbidden symbol was
observed. Unmet visual requirements observed: none. This is a local review,
not independent artistic certification.
