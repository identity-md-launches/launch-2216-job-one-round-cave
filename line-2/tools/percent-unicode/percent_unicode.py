#!/usr/bin/env python3
"""Find UTF-8 Unicode characters represented by literal %HH byte escapes."""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import sys
import unicodedata
from pathlib import Path


DEMO = b"URL: https://example.invalid/%6Fwner/%D1%96tem?q=%E2%80%AE"


def _octet_run(data: bytes, start: int) -> tuple[bytes, list[int], int]:
    decoded = bytearray()
    positions: list[int] = []
    pos = start
    while pos + 2 < len(data) and data[pos] == 0x25:
        pair = data[pos + 1:pos + 3]
        # int(b"-1", 16) accepts a sign. %HH admits only two hex digits.
        if any(c not in b"0123456789abcdefABCDEF" for c in pair):
            break
        value = int(pair, 16)
        decoded.append(value)
        positions.append(pos)
        pos += 3
    return bytes(decoded), positions, pos


def scan(data: bytes, max_findings: int = 100) -> dict:
    """Report valid percent-encoded non-ASCII UTF-8 scalars in original bytes."""
    findings = []
    total = 0
    newline_offsets = [pos for pos, byte in enumerate(data) if byte == 0x0A]
    i = 0
    while i < len(data):
        if data[i] != 0x25 or i + 2 >= len(data):
            i += 1
            continue
        octets, positions, end = _octet_run(data, i)
        if not octets:
            i += 1
            continue
        j = 0
        while j < len(octets):
            first = octets[j]
            width = 2 if 0xC2 <= first <= 0xDF else 3 if 0xE0 <= first <= 0xEF else 4 if 0xF0 <= first <= 0xF4 else 1
            if width == 1 or j + width > len(octets):
                j += 1
                continue
            try:
                char = octets[j:j + width].decode("utf-8", "strict")
            except UnicodeDecodeError:
                j += 1
                continue
            if len(char) == 1 and ord(char) > 0x7F:
                lo, hi = positions[j], positions[j + width - 1] + 3
                total += 1
                if len(findings) < max_findings:
                    cp = ord(char)
                    line = bisect.bisect_left(newline_offsets, lo)
                    previous_newline = newline_offsets[line - 1] if line else -1
                    findings.append({
                        "codepoint": f"U+{cp:04X}",
                        "name": unicodedata.name(char, "UNNAMED"),
                        "category": unicodedata.category(char),
                        "decoded": f"\\u{{{cp:X}}}",
                        "source_byte_range": [lo, hi],
                        "source_line": line + 1,
                        "source_byte_column": lo - previous_newline,
                        "source_escape": data[lo:hi].decode("ascii"),
                    })
            j += width
        i = max(end, i + 1)
    return {
        "schema_version": 1,
        "tool": "percent-unicode/2",
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "source_bytes": len(data),
        "unicode_version": unicodedata.unidata_version,
        "analysis_complete": True,
        "findings": total,
        "retained_details": len(findings),
        "omitted_details": total - len(findings),
        "details": findings,
        "coverage": "Valid UTF-8 non-ASCII scalar values formed by consecutive literal %HH octets.",
        "limitations": [
            "Review candidates only; percent escapes can be legitimate.",
            "Does not parse URLs, decode JSON or language escapes, or inspect other encodings.",
            "A UTF-8 scalar split by literal text or malformed escapes is not reported.",
            "An empty result does not establish that the source is safe.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--demo", action="store_true", help="scan the clearly synthetic built-in example")
    source.add_argument("--file", type=Path, help="read one explicitly selected workspace file as inert bytes")
    parser.add_argument("--max-findings", type=int, default=100)
    args = parser.parse_args(argv)
    if args.max_findings < 0 or args.max_findings > 10000:
        parser.error("--max-findings must be between 0 and 10000")
    try:
        if args.demo:
            data = DEMO
        else:
            root = Path.cwd().resolve()
            selected = args.file.resolve(strict=True)
            if not selected.is_relative_to(root):
                parser.error("--file must resolve inside the current workspace")
            data = selected.read_bytes()
    except OSError as exc:
        print(f"percent-unicode: cannot read selected file: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(scan(data, args.max_findings), ensure_ascii=True, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
