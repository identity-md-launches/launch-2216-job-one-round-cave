# Temperature Flint

Check temperature conversions, differences and shifts with exact rational
arithmetic. Python 3.10+ standard library only; copy this folder to use it
offline. Temperature readings are **points**, while temperature changes are
**deltas**. Offsets apply only to points: 32 degF is 0 degC, but a change of
32 degF is a change of 160/9 kelvin.

One command from the repository root shows it working:

```sh
python3 -B line-4/tools/temperature-flint/temperature_flint.py demo
```

Observed locally: all three exact claims passed, exit 0. The demo converts
32 degF to 0 degC, subtracts equivalent readings (68 degF minus 20 degC)
to get a zero-kelvin change, and shifts 20 degC by an 18 degF change to
get 30 degC. These are supplied examples, not measured temperatures.

For your own calculation, pass one JSON object on stdin:

```sh
printf '%s\n' '{"operation":"shift","point":{"value":"20","unit":"degC"},"delta":{"value":"18","unit":"degF"},"to":"degC","expect":{"value":"30","unit":"degC"}}' | python3 -B line-4/tools/temperature-flint/temperature_flint.py run
```

Every request requires `operation` and `to`. Exactly these operation-specific
fields are accepted:

- `convert`: `kind` (`point` or `delta`) and `input`.
- `difference`: `end` and `start`, both points; result is end minus start, a delta.
- `shift`: `point` and `delta`; result is a point.

Every quantity has exactly `value` (a decimal/scientific string) and `unit`
(`K`, `degC`, `degF`, case sensitive). Optional `expect` uses the result's kind
and may use any supported unit. Results include exact `value`, `base_value`
in kelvin, explicit temperature dimension and point/delta kind. Fractions in
outputs use `numerator/denominator`; inputs require decimal strings. Output
fractions must be converted to exact decimal inputs only when terminating;
this tool has no receipt/replay format. `K` means a kelvin point or a kelvin
change according to the explicit kind; do not discard that kind downstream.

Exit 0: valid operation and supplied equality passes, or no equality supplied.
Exit 1: valid operation but equality fails. Exit 2: invalid request, with no
partial stdout and a diagnostic on stderr. Unknown/duplicate keys, unsupported
units, nonstring quantities, nonfinite constants and below-zero-kelvin points
(including shifted results and expected points) are rejected. Negative deltas
are valid. Point addition, point multiplication and arbitrary formulas are
intentionally absent; adding two readings is not a temperature shift.

Exact definitions: K has scale 1, offset 0; degC has scale 1, offset 273.15 K;
degF has scale 5/9, offset 45967/180 K. A point maps to `value * scale + offset`;
a delta maps to `value * scale`. These conventional affine conversions do not
calibrate sensors or establish physical measurement accuracy. Below absolute
zero is outside this tool's thermodynamic model. No uncertainty, significant
figures, rounding, compound temperature units or currency conversion is inferred.
It complements Unit Flint; it does not modify or extend that tool's grammar.

Limits: 8192 stdin bytes, four JSON nesting levels, 80 characters per decimal,
exponents -200 through 200, 2048-bit parsed rational components. There are at
most three quantity parses and a fixed number of rational operations per request;
no expression evaluation, imports of other tools or external dependencies.
The tool reads stdin only and writes stdout/stderr. It never reads environment,
configuration or user files, uses a network, accesses wallets or sends anything.
No price, payment or coin is needed.

Run the regression suite:

```sh
python3 -B -m unittest discover -s line-4/tools/temperature-flint -v
```

Nine tests passed locally: fixed points, point/delta distinctions, mixed-scale
differences, shifts, equality failures, absolute-zero boundaries, strict input
validation, resource limits, no mutation and actual CLI exit/stream checks.
400 seeded independent rational oracle cases check Celsius point conversion
and Fahrenheit changes. Local results are not independent certification.
