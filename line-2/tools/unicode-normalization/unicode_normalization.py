#!/usr/bin/env python3
"""Report Unicode sequences whose compatibility or canonical form changes."""
import argparse
import hashlib
import json
import pathlib
import sys
import unicodedata

MAX_BYTES = 2 * 1024 * 1024
MAX_DETAILS = 1000
DEMO = "owner=Ａdmin\nlabel=Kelvin\ncount=①"


def _joins(previous, current):
    """Keep scalars together when normalization may cross their boundary."""
    left = unicodedata.normalize("NFKD", previous)[-1]
    right = unicodedata.normalize("NFKD", current)[0]
    if unicodedata.combining(right):
        return True
    # Hangul L+V and LV+T composition uses class-zero Jamo. NFKD also
    # exposes compatibility Jamo and precomposed LV syllables here.
    return (0x1100 <= ord(left) <= 0x1112 and 0x1161 <= ord(right) <= 0x1175) or (
        0x1161 <= ord(left) <= 0x1175 and 0x11A8 <= ord(right) <= 0x11C2
    )


def escaped(text):
    return text.encode("unicode_escape").decode("ascii")


def scalar(c):
    return {"codepoint": f"U+{ord(c):04X}",
            "name": unicodedata.name(c, "UNNAMED"),
            "category": unicodedata.category(c)}


def review(data, max_details=100):
    if not isinstance(data, bytes) or len(data) > MAX_BYTES:
        raise ValueError("input must be UTF-8 bytes of at most 2 MiB")
    if not isinstance(max_details, int) or not 0 <= max_details <= MAX_DETAILS:
        raise ValueError("max_details must be an integer from 0 to 1000")
    text = data.decode("utf-8", "strict")
    findings = []
    finding_count = 0
    index = 0
    byte_position = 0
    while index < len(text):
        end = index + 1
        while end < len(text) and _joins(text[end - 1], text[end]):
            end += 1
        original = text[index:end]
        nfc = unicodedata.normalize("NFC", original)
        nfkc = unicodedata.normalize("NFKC", original)
        original_bytes = original.encode("utf-8")
        after = byte_position + len(original_bytes)
        if nfc != original or nfkc != original:
            finding_count += 1
            if len(findings) < max_details:
                findings.append({
                    "character_index": index,
                    "source_byte_range": [byte_position, after],
                    "source_span_sha256": hashlib.sha256(original_bytes).hexdigest(),
                    "original": escaped(original),
                    "nfc": escaped(nfc),
                    "nfkc": escaped(nfkc),
                    "original_scalars": [scalar(c) for c in original],
                    "nfc_changed": nfc != original,
                    "nfkc_changed": nfkc != original,
                })
        byte_position = after
        index = end
    return {
        "schema_version": 1,
        "tool": "unicode-normalization/2",
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "source_bytes": len(data),
        "unicode_version": unicodedata.unidata_version,
        "analysis_complete": True,
        "finding_count": finding_count,
        "detail_cap": max_details,
        "retained_details": len(findings),
        "omitted_details": finding_count - len(findings),
        "details": findings,
        "coverage": "UTF-8 text sequences whose NFC or NFKC form differs from the original.",
        "limitations": [
            "Normalization differences can be intentional and are not proof of deception.",
            "This is lexical review; it does not render text or compare fonts.",
            "Adjacent combining marks and Hangul Jamo are grouped; this is not a whole-label collision test.",
            "Source ranges are zero-based UTF-8 byte offsets and output is escaped ASCII JSON.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--demo", action="store_true")
    group.add_argument("--file")
    parser.add_argument("--max-details", type=int, default=100)
    args = parser.parse_args()
    try:
        if args.demo:
            data = DEMO.encode("utf-8")
            source_kind = "synthetic-demo"
        else:
            path = pathlib.Path(args.file)
            root = pathlib.Path.cwd().resolve()
            resolved = path.resolve()
            if not resolved.is_relative_to(root) or not resolved.is_file():
                raise ValueError("file must be a regular file inside the current workspace")
            data = resolved.read_bytes()
            source_kind = "selected-workspace-file"
        report = review(data, args.max_details)
        report["source_kind"] = source_kind
        print(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2))
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
