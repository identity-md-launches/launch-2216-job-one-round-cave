#!/usr/bin/env python3
"""Read-only reproductions of repaired and still-open upstream boundary cases."""
import importlib.util
import json
from pathlib import Path
import unicodedata

ROOT = Path(__file__).resolve().parent.parent


def load(name, source):
    spec = importlib.util.spec_from_file_location(name, ROOT/source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    norm = load('edge_norm', 'line-2/tools/unicode-normalization/unicode_normalization.py')
    percent = load('edge_percent', 'line-2/tools/percent-unicode/percent_unicode.py')
    lens = load('edge_lens', 'line-3/tools/uncertainty-lens/uncertainty_lens.py')
    normalization = []
    for name, text in [('Hangul Jamo', '\u1100\u1161'),
                       ('Bengali vowel signs', '\u09c7\u09be'),
                       ('Tamil vowel signs', '\u0bc6\u0bbe')]:
        report = norm.review(text.encode())
        whole = unicodedata.normalize('NFC', text)
        normalization.append({'case': name,
            'input_escaped': text.encode('unicode_escape').decode(),
            'whole_string_nfc_escaped': whole.encode('unicode_escape').decode(),
            'whole_string_changes': whole != text,
            'finding_count': report['finding_count'],
            'missed_change': whole != text and report['finding_count'] == 0})
    try:
        percent_result = percent.scan(b'%-1 %+1 %D1%96')
        percent_check = {'malformed_escapes_rejected_without_crash': True,
                         'valid_following_scalar_retained': percent_result['findings'] == 1,
                         'details': percent_result['details']}
    except ValueError as exc:
        percent_check = {'malformed_escapes_rejected_without_crash': False, 'exception': str(exc)}
    lens_cases = []
    cases = [('NaN endpoint', [{'id':'a','start':float('nan'),'end':1},{'id':'b','start':2,'end':3}]),
             ('boolean endpoints', [{'id':'a','start':False,'end':True}]),
             ('duplicate IDs', [{'id':'same','start':0,'end':1},{'id':'same','start':2,'end':3}])]
    for name, events in cases:
        try:
            result = lens.analyze(events)
            lens_cases.append({'case': name, 'accepted': True, 'observed': result})
        except ValueError as exc:
            lens_cases.append({'case': name, 'accepted': False, 'diagnostic': str(exc)})
    result = {'normalization': normalization, 'percent_parser': percent_check,
              'uncertainty_lens': lens_cases,
              'line_files_changed': False,
              'limits': 'Constructed probes of current source, not observed attacks or real incident evidence; script reports gaps rather than treating acceptance as correctness.'}
    print(json.dumps(result, ensure_ascii=True, allow_nan=False, indent=2))


if __name__ == '__main__':
    main()
