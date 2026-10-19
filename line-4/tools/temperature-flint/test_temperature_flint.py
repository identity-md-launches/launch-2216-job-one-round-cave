import json
from fractions import Fraction
from pathlib import Path
import random
import subprocess
import sys
import unittest
import temperature_flint as t


def q(value, unit):
    return {'value': str(value), 'unit': unit}


def convert(value, unit, target, kind='point'):
    return {'operation': 'convert', 'kind': kind, 'input': q(value, unit), 'to': target}


class TemperatureTests(unittest.TestCase):
    def test_fixed_points(self):
        for value, unit, target, expected in [('32', 'degF', 'degC', '0'),
                ('212', 'degF', 'degC', '100'), ('-40', 'degC', 'degF', '-40'),
                ('0', 'K', 'degC', '-5463/20'), ('-459.67', 'degF', 'K', '0')]:
            self.assertEqual(t.calculate(convert(value, unit, target))['value'], expected)

    def test_delta_offsets_never_applied(self):
        self.assertEqual(t.calculate(convert(18, 'degF', 'degC', 'delta'))['value'], '10')
        self.assertEqual(t.calculate(convert(-18, 'degF', 'K', 'delta'))['value'], '-10')
        self.assertEqual(t.calculate(convert(0, 'degC', 'K', 'delta'))['value'], '0')

    def test_difference_and_shift(self):
        r = {'operation': 'difference', 'start': q(20, 'degC'), 'end': q(68, 'degF'), 'to': 'K'}
        self.assertEqual(t.calculate(r)['value'], '0')
        r['end'] = q(14, 'degF')
        self.assertEqual(t.calculate(r)['value'], '-30')
        r = {'operation': 'shift', 'point': q(20, 'degC'), 'delta': q(18, 'degF'), 'to': 'degC'}
        self.assertEqual(t.calculate(r)['value'], '30')

    def test_seeded_independent_oracle(self):
        rng = random.Random(737)
        for _ in range(400):
            c = rng.randint(-273, 10000)
            # Independent schoolbook Celsius/Fahrenheit relation.
            f = Fraction(9, 5) * c + 32
            self.assertEqual(Fraction(t.calculate(convert(c, 'degC', 'degF'))['value']), f)
            d = rng.randint(-10000, 10000)
            self.assertEqual(Fraction(t.calculate(convert(d, 'degF', 'K', 'delta'))['value']), Fraction(5*d, 9))

    def test_claims(self):
        r = convert(32, 'degF', 'K')
        r['expect'] = q('273.15', 'K')
        self.assertTrue(t.calculate(r)['passes'])
        r['expect'] = q(0, 'K')
        self.assertFalse(t.calculate(r)['passes'])
        self.assertEqual(t.calculate(r)['check']['difference_base_value'], '5463/20')

    def test_absolute_zero(self):
        for unit, value in [('K', '-0.0001'), ('degC', '-273.15001'), ('degF', '-459.67001')]:
            with self.assertRaises(ValueError):
                t.calculate(convert(value, unit, 'K'))
        with self.assertRaises(ValueError):
            t.calculate({'operation': 'shift', 'point': q(0, 'K'), 'delta': q(-1, 'K'), 'to': 'K'})

    def test_schema_and_limits(self):
        bad = [None, [], {}, {'operation': []}]
        for field, value in [('kind', 'absolute'), ('to', []), ('input', {'value': True, 'unit': 'K'}),
                ('input', q('NaN', 'K')), ('input', q('1/3', 'K')),
                ('input', q('1e201', 'K')), ('input', q('1e-201', 'K')),
                ('input', q('1' * 81, 'K')), ('input', q('1', 'C')),
                ('extra', 1), ('expect', {'value': 1, 'unit': 'K'})]:
            r = convert(0, 'K', 'K'); r[field] = value; bad.append(r)
        for r in bad:
            with self.assertRaises(ValueError, msg=repr(r)):
                t.calculate(r)
        for raw in [b'{"x":1,"x":2}', b'{"x":NaN}', b'[' * 1000, b' ' * 8193, b'\xff']:
            with self.assertRaises(ValueError):
                t.load(raw)

    def test_no_mutation(self):
        r = convert('1e2', 'degC', 'degF')
        before = json.dumps(r)
        t.calculate(r)
        self.assertEqual(json.dumps(r), before)

    def test_cli(self):
        script = str(Path(__file__).with_name('temperature_flint.py'))
        for request, status in [(convert(32, 'degF', 'degC'), 0),
                (dict(convert(32, 'degF', 'degC'), expect=q(1, 'degC')), 1),
                (convert(-1, 'K', 'K'), 2)]:
            p = subprocess.run([sys.executable, '-B', script, 'run'], input=json.dumps(request),
                               text=True, capture_output=True)
            self.assertEqual(p.returncode, status, p.stderr)
            if status == 2:
                self.assertEqual(p.stdout, '')
                self.assertIn('zero kelvin', p.stderr)
            else:
                self.assertEqual(json.loads(p.stdout)['passes'], status == 0)
        p = subprocess.run([sys.executable, '-B', script, 'demo'], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(len(json.loads(p.stdout)['examples']), 3)


if __name__ == '__main__':
    unittest.main()
