#!/usr/bin/env python3
"""Exact temperature points and changes; stdin/stdout only, standard library."""
from fractions import Fraction
import argparse
import json
import re
import sys

# kelvin = displayed point * scale + offset; changes have no offset.
SCALES = {'K': (Fraction(1), Fraction(0)),
          'degC': (Fraction(1), Fraction(27315, 100)),
          'degF': (Fraction(5, 9), Fraction(45967, 180))}
NUMBER = re.compile(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?')


def number(text):
    if not isinstance(text, str) or len(text) > 80 or not NUMBER.fullmatch(text):
        raise ValueError('value must be a decimal string of at most 80 characters')
    exponent = re.split('[eE]', text)
    if len(exponent) == 2 and abs(int(exponent[1])) > 200:
        raise ValueError('decimal exponent exceeds -200..200')
    value = Fraction(text)
    if max(value.numerator.bit_length(), value.denominator.bit_length()) > 2048:
        raise ValueError('value exceeds 2048-bit budget')
    return value


def quantity(obj, kind):
    if not isinstance(obj, dict) or set(obj) != {'value', 'unit'}:
        raise ValueError('quantity requires exactly value and unit')
    unit = obj['unit']
    if not isinstance(unit, str) or unit not in SCALES:
        raise ValueError('unit must be K, degC or degF')
    scale, offset = SCALES[unit]
    value = number(obj['value']) * scale + (offset if kind == 'point' else 0)
    if kind == 'point' and value < 0:
        raise ValueError('absolute temperature is below zero kelvin')
    return value


def exact(value):
    return str(value.numerator) if value.denominator == 1 else str(value)


def calculate(request):
    if not isinstance(request, dict):
        raise ValueError('request must be an object')
    op = request.get('operation')
    fields = {'convert': {'kind', 'input'}, 'difference': {'end', 'start'},
              'shift': {'point', 'delta'}}
    if not isinstance(op, str) or op not in fields:
        raise ValueError('operation must be convert, difference or shift')
    required = {'operation', 'to'} | fields[op]
    if set(request) not in (required, required | {'expect'}):
        raise ValueError('missing or unknown request fields')
    target = request['to']
    if not isinstance(target, str) or target not in SCALES:
        raise ValueError('to must be K, degC or degF')
    if op == 'convert':
        kind = request['kind']
        if kind not in ('point', 'delta'):
            raise ValueError('kind must be point or delta')
        result = quantity(request['input'], kind)
    elif op == 'difference':
        kind = 'delta'
        result = quantity(request['end'], 'point') - quantity(request['start'], 'point')
    else:
        kind = 'point'
        result = quantity(request['point'], 'point') + quantity(request['delta'], 'delta')
        if result < 0:
            raise ValueError('shift produces a point below zero kelvin')
    scale, offset = SCALES[target]
    shown = (result - (offset if kind == 'point' else 0)) / scale
    output = {'schema': 'temperature-flint/1', 'operation': op, 'kind': kind,
              'dimension': 'temperature', 'value': exact(shown), 'unit': target,
              'base_value': exact(result), 'base_unit': 'K', 'passes': True}
    if 'expect' in request:
        expected = quantity(request['expect'], kind)
        output['check'] = {'expected_base_value': exact(expected),
                           'difference_base_value': exact(result - expected),
                           'matches': result == expected}
        output['passes'] = result == expected
    return output


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError('nonfinite JSON constant')


def load(raw):
    if len(raw) > 8192:
        raise ValueError('request exceeds 8192 bytes')
    # Shallow grammar; bound nesting before the JSON decoder touches it.
    depth = 0
    quoted = escaped = False
    for char in raw.decode('utf-8'):
        if quoted:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in '[{':
            depth += 1
            if depth > 4:
                raise ValueError('JSON nesting exceeds four levels')
        elif char in ']}':
            depth -= 1
    return json.loads(raw, object_pairs_hook=no_duplicates, parse_constant=reject_constant)


def demo():
    requests = [
        {'operation': 'convert', 'kind': 'point', 'input': {'value': '32', 'unit': 'degF'},
         'to': 'degC', 'expect': {'value': '0', 'unit': 'degC'}},
        {'operation': 'difference', 'start': {'value': '20', 'unit': 'degC'},
         'end': {'value': '68', 'unit': 'degF'}, 'to': 'K',
         'expect': {'value': '0', 'unit': 'K'}},
        {'operation': 'shift', 'point': {'value': '20', 'unit': 'degC'},
         'delta': {'value': '18', 'unit': 'degF'}, 'to': 'degC',
         'expect': {'value': '30', 'unit': 'degC'}}]
    return {'examples': [calculate(r) for r in requests]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['run', 'demo'])
    args = parser.parse_args(argv)
    try:
        output = demo() if args.command == 'demo' else calculate(load(sys.stdin.buffer.read(8193)))
    except (ValueError, TypeError, UnicodeError, OverflowError) as exc:
        print('temperature-flint: ' + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(output, sort_keys=True))
    return 0 if output.get('passes', True) else 1


if __name__ == '__main__':
    raise SystemExit(main())
