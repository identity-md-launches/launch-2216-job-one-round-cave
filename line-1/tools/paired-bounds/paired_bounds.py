#!/usr/bin/env python3
"""Conservative simultaneous paired-binary effect bounds, with exact arithmetic."""
import argparse
import csv
import hashlib
import io
import json
import re
import unicodedata
from fractions import Fraction
from pathlib import Path

MAX_BYTES = 2 * 1024 * 1024
MAX_CASES = 512
MAX_CANDIDATES = 16
BITS = 32
GRID = 1 << BITS


class InputError(ValueError):
    """Input does not fit the retained protocol."""


def decimal(value, name, low, high):
    if not isinstance(value, str) or not re.fullmatch(r'(?:0|1)(?:\.[0-9]{1,9})?', value):
        raise InputError(f'{name}: use a plain decimal with at most nine fractional places')
    result = Fraction(value)
    if not low <= result <= high:
        raise InputError(f'{name}: must be in [{low}, {high}]')
    return result


def label(value):
    return (1 <= len(value) <= 200 and value == value.strip()
            and all(not unicodedata.category(c).startswith('C') for c in value))


def parse_csv(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
        raise InputError('CSV must be bytes, at most 2 MiB')
    try:
        reader = csv.reader(io.StringIO(raw.decode('utf-8-sig'), newline=''), strict=True)
        header = next(reader, [])
        if (not 3 <= len(header) <= MAX_CANDIDATES + 2
                or header[:2] != ['case', 'baseline'] or len(set(header)) != len(header)
                or not all(label(x) for x in header)):
            raise InputError('header: case,baseline followed by 1–16 unique valid candidate names')
        cases, rows = set(), []
        for row in reader:
            if len(row) != len(header) or not label(row[0]):
                raise InputError(f'CSV line {reader.line_num}: invalid case or field count')
            if row[0] in cases or any(x not in ('0', '1') for x in row[1:]):
                raise InputError(f'CSV line {reader.line_num}: duplicate case or nonbinary outcome')
            cases.add(row[0])
            rows.append(tuple(map(int, row[1:])))
            if len(rows) > MAX_CASES:
                raise InputError(f'at most {MAX_CASES} complete cases are supported')
        if not rows:
            raise InputError('at least one complete case is required')
        return header[2:], rows
    except (UnicodeError, csv.Error) as exc:
        raise InputError('invalid UTF-8 or CSV') from exc


def load(name):
    root = Path.cwd().resolve()
    path = Path(name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise InputError('input must be a regular file resolving inside the current workspace')
    with path.open('rb') as stream:
        return stream.read(MAX_BYTES + 1)


def cdf_numerator(n, k, a, b):
    """Integer numerator of P[Bin(n,a/b)<=k], common denominator b**n."""
    if k < 0:
        return 0
    if k >= n:
        return b ** n
    if a == 0:
        return b ** n
    if a == b:
        return 0
    term = (b - a) ** n
    total = term
    for j in range(k):
        # The complete numerator is divisible by the complete denominator.
        term = term * (n - j) * a // ((j + 1) * (b - a))
        total += term
    return total


def lower_bound(n, successes, tail):
    """Outward grid bracket for the Clopper–Pearson lower endpoint."""
    if successes == 0:
        return Fraction(0)
    lo, hi = 0, GRID
    denominator = GRID ** n
    while hi - lo > 1:
        middle = (lo + hi) // 2
        # P_p[X>=successes] = P_{1-p}[X<=n-successes], increasing in p.
        upper_tail = cdf_numerator(n, n - successes, GRID - middle, GRID)
        if upper_tail * tail.denominator <= denominator * tail.numerator:
            lo = middle
        else:
            hi = middle
    return Fraction(lo, GRID)


def binomial_bounds(n, successes, tail):
    if (type(n) is not int or type(successes) is not int
            or not 1 <= n <= MAX_CASES or not 0 <= successes <= n
            or not isinstance(tail, Fraction) or not 0 < tail < Fraction(1, 2)):
        raise InputError('invalid binomial bound arguments')
    return lower_bound(n, successes, tail), 1 - lower_bound(n, n - successes, tail)


def fraction(value):
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator)}


def analyze(raw, alpha=Fraction(1, 20), margin=Fraction(1, 10)):
    if (not isinstance(alpha, Fraction) or not Fraction(1, 1000000) <= alpha <= Fraction(1, 5)
            or not isinstance(margin, Fraction) or not 0 <= margin <= 1):
        raise InputError('invalid alpha or margin')
    names, rows = parse_csv(raw)
    n, m = len(rows), len(names)
    tail = alpha / (4 * m)
    candidates, cache = [], {}
    for index, name in enumerate(names, 1):
        wins = sum(row[0] == 0 and row[index] == 1 for row in rows)
        losses = sum(row[0] == 1 and row[index] == 0 for row in rows)
        for count in (wins, losses):
            if count not in cache:
                cache[count] = binomial_bounds(n, count, tail)
        wl, wu = cache[wins]
        ll, lu = cache[losses]
        low, high = wl - lu, wu - ll
        candidates.append({
            'name': name, 'candidate_only_pass': wins, 'baseline_only_pass': losses,
            'observed_difference': fraction(Fraction(wins - losses, n)),
            'win_probability_bounds': [fraction(wl), fraction(wu)],
            'loss_probability_bounds': [fraction(ll), fraction(lu)],
            'candidate_minus_baseline_bounds': [fraction(low), fraction(high)],
            'candidate_exceeds_positive_margin': low > margin,
            'baseline_exceeds_positive_margin': high < -margin,
            'entire_interval_strictly_inside_equivalence_margin': low > -margin and high < margin,
        })
    return {
        'schema_version': 1, 'input_sha256': hashlib.sha256(raw).hexdigest(),
        'paired_cases': n, 'candidate_count': m, 'familywise_alpha': fraction(alpha),
        'simultaneous_coverage_at_least': fraction(1 - alpha), 'practical_margin': fraction(margin),
        'method': 'Clopper–Pearson binomial win/loss bounds; Bonferroni over all 4m tails; subtract bounds',
        'one_sided_tail_budget': fraction(tail), 'outward_grid_bits': BITS,
        'candidates': candidates,
        'assumptions': [
            'Independent identically distributed case vectors from the target population; dependence within a row is allowed.',
            'One fixed final sample size; complete prespecified candidate family, pass rule, alpha and practical margin.',
            'Each row evaluates the same case once under baseline and every candidate; no selected or omitted outcomes.',
            'Correlated cases, repeated looks, optional stopping and selected families invalidate the stated coverage.',
            'Coverage is a repeated-sampling guarantee under these assumptions, not a posterior probability.',
            'Conservative intervals may be wide; an inconclusive interval is not evidence of equivalence.',
            'Pins prove byte identity, not honest measurement, prospective choice or representative sampling.',
        ],
    }


def demo_csv():
    lines = ['case,baseline,improved,unchanged']
    for i in range(120):
        baseline = int(i < 40)
        improved = int(i < 90)
        lines.append(f'synthetic-{i + 1:03},{baseline},{improved},{baseline}')
    return ('\n'.join(lines) + '\n').encode()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--demo', action='store_true')
    source.add_argument('--input')
    parser.add_argument('--expected-input-sha256')
    parser.add_argument('--alpha', default='0.05')
    parser.add_argument('--margin', default='0.1', help='absolute pass-rate difference, not percent')
    args = parser.parse_args(argv)
    try:
        alpha = decimal(args.alpha, 'alpha', Fraction(1, 1000000), Fraction(1, 5))
        margin = decimal(args.margin, 'margin', Fraction(0), Fraction(1))
        if args.demo:
            if args.expected_input_sha256 is not None:
                raise InputError('the demo does not accept an input pin')
            raw = demo_csv()
        else:
            pin = args.expected_input_sha256
            if not pin or not re.fullmatch('[0-9a-f]{64}', pin):
                raise InputError('a retained lowercase 64-hex --expected-input-sha256 is required')
            raw = load(args.input)
            if hashlib.sha256(raw).hexdigest() != pin:
                raise InputError('input SHA-256 mismatch')
        result = analyze(raw, alpha, margin)
        result['data_kind'] = 'synthetic_demonstration' if args.demo else 'user_supplied_benchmark'
    except (InputError, OSError, ValueError) as exc:
        parser.exit(2, f'error: {exc}\n')
    print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
