# Exact quantities before trust

Unit Flint checks calculations with exact rational arithmetic and explicit
physical dimensions. It runs offline with Python 3.10+ and only the standard
library. It neither reads inputs from files nor contacts any service.

From the repository root, check a speed claim:

```sh
python3 -B line-4/tools/unit-flint/unit_flint.py '10 km / 2 h' --expect '5 km/h' --to m/s --json
```

This prints the exact `25/18 m/s`, reports `check.matches: true`, and exits 0.
An unequal claim exits 1; invalid syntax or incompatible units exits 2.
See [the tool README](tools/unit-flint/README.md) for the grammar, limits,
diagnostics, examples and one-command regression suite. The check verifies
the supplied arithmetic, not the truth of a measured input.

Mark 23 adds claim checking while preserving the line's original goal.
[WALL.md](WALL.md) records dimensions, formats and visual review;
[USED.md](USED.md) records the sources used.

Mark 24 adds exact inclusive bounds. Check a supplied transfer-time calculation:

```sh
python3 -B line-4/tools/unit-flint/unit_flint.py '5 MiB / (2 MiB/s)' --at-least '2000 ms' --at-most '3 s' --to s --json
```

This returns `2.5 s`, both bounds pass, and exit 0. The tool checks supplied
arithmetic; the transfer rate is an example input, not a measurement.

Mark 25 adds [Calculation Receipt](tools/calculation-receipt/README.md), a
portable bundle that saves a calculation and recomputes it to check the saved
result. Its demo shows a passing receipt, a faithfully recorded failed bound,
and rejection of an altered result even when its checksum is recalculated:

```sh
python3 -B line-4/tools/calculation-receipt/receipt.py demo
```

Receipts identify exact supplied arithmetic and engine source; they do not
authenticate an author or establish the accuracy of a measurement.

Mark 26 adds [Interval Flint](tools/interval-flint/README.md), which encloses a
formula over user-supplied uncertain quantities using exact endpoints and unit
dimensions. The demo yields the hypothetical transfer-time interval
`[3.6, 5.5] s` and checks it against `[3, 6] s`:

```sh
python3 -B line-4/tools/interval-flint/interval_flint.py demo
```

The result is an enclosure, not a probability statement or a validation of
the supplied measurements. The line goal remains unchanged.

Mark 27 adds [Round Flint](tools/round-flint/README.md), a portable checker
for decimal display claims after exact unit conversion. Choose a rounding
rule and precision, then check a proposed displayed result:

```sh
python3 -B line-4/tools/round-flint/round_flint.py '10 km / 2 h' --to m/s --places 2 --expect 1.39
```

This returns exact `25/18 m/s`, rounded `1.39`, exact rounding error
`1/900 m/s`, and a passing display check. It checks the supplied calculation
and rounding policy; it does not establish measurement accuracy.

Mark 28 adds [Tolerance Flint](tools/tolerance-flint/README.md), an exact
comparison with declared absolute and relative error allowances:

```sh
python3 -B line-4/tools/tolerance-flint/tolerance_flint.py demo
```

The demo checks an inclusive boundary at `6 mm` error and rejects a value
`0.001 mm` beyond it. The allowance is absolute tolerance plus relative tolerance
times the reference magnitude. Tolerances are supplied policy, not inferred
measurement accuracy. The tool works offline using only the standard library.

Mark 29 adds [Worksheet Flint](tools/worksheet-flint/README.md), an ordered
chain of named exact calculations. `$name` references an earlier quantity
without copying rounded display values. Its demo deliberately reports an
exceeded budget with exit 1:

```sh
python3 -B line-4/tools/worksheet-flint/worksheet_flint.py demo
```

The supplied example computes 62.5 seconds for a transfer and 64 seconds with
overhead; the 60-second limit fails. The full worksheet is checked before any
output, with explicit dimensions, direct dependencies and per-step checks.

Mark 30 adds [Worksheet Receipt](tools/worksheet-receipt/README.md), which keeps
an entire exact worksheet and recomputes its intermediate quantities, dimensions,
dependencies and claims later. A verified receipt can still contain a failed
claim; its exit status preserves that distinction. Try:

```sh
python3 -B line-4/tools/worksheet-receipt/worksheet_receipt.py demo
```

The offline demo replays passing and failed budgets and rejects a rehashed
altered intermediate. Receipts establish consistency, not input truth or authorship.

Mark 31 adds [Subdivision Flint](tools/subdivision-flint/README.md). It covers
one uncertain input with exact subintervals and combines their output bounds,
reducing dependency overestimation without sampling or discarding domains:

```sh
python3 -B line-4/tools/subdivision-flint/subdivision_flint.py demo
```

The demo tightens `[0, 100]` to `[0, 37.5] m²`, proving containment in a supplied
`[0, 38] m²` limit. It remains a conservative enclosure, not exact optimization.

Mark 33 adds [Table Flint](tools/table-flint/README.md), which checks sums and
means from a CSV of measured quantities with compatible units and optional
weights. It compares exact claims and binds the raw CSV bytes by SHA-256:

```sh
python3 -B line-4/tools/table-flint/table_flint.py demo
```

The synthetic demo checks `1500 m` total, `750 m` ordinary mean and `2500/3 m`
weighted mean. It checks the supplied data, not the measurements' truth.

Mark 34 adds [Temperature Flint](tools/temperature-flint/README.md), which
checks exact temperature conversions while distinguishing readings (points)
from temperature changes (deltas). Its offline demo converts 32 degF to 0 degC,
checks equivalent mixed-scale readings and shifts 20 degC by an 18 degF change
to obtain 30 degC:

```sh
python3 -B line-4/tools/temperature-flint/temperature_flint.py demo
```

All three claims pass. Exact conversion does not establish sensor accuracy.
