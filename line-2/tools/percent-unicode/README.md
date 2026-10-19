# Percent Unicode

Find valid UTF-8 Unicode characters concealed as consecutive `%HH` byte
escapes in a selected text file. Each result identifies the exact original
escape bytes, code point, Unicode name, line and byte column. This can expose
lookalike or directional characters embedded in URL paths and copied text
before a worker trusts or publishes them. It is a triage aid: percent escapes
are often legitimate, and the scanner does not parse URLs or decode other
escape syntaxes.

Python 3.9+ and the standard library only. The input is read as inert bytes;
the tool does not execute or rewrite it and does not access the network.

From the repository root, one command runs a clearly synthetic example:

```sh
python3 -B line-2/tools/percent-unicode/percent_unicode.py --demo
```

It reports two encoded Unicode scalars (Cyrillic small i and a
right-to-left override) with their exact `%HH` source ranges and exits 0. The
adjacent `%6F` escape decodes to ASCII and is not a Unicode finding.
This demonstrates detection behavior; it is not an observed attack.

Round 36 fixed a malformed-escape crash: signed pairs such as `%-1` and `%+1`
are now rejected as non-hex and scanning resumes at later escapes. Seven
focused tests passed, including this case and capped complete counts. Finding
line and byte-column lookup now uses indexed newline positions, so many
findings do not repeatedly rescan the whole preceding input.

Review one explicitly selected, non-sensitive workspace file with
`python3 -B line-2/tools/percent-unicode/percent_unicode.py --file path/to/file`.
Output is ASCII JSON. The report includes the complete finding count, detail
cap, SHA-256 of the input bytes, and limits of the analysis.
