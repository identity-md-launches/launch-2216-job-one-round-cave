# Bounds Display

Read paired binary benchmark confidence bounds in percentage points without
rounding an interval inward. This joins Line 1's Paired Bounds to Line 4's
exact Round Flint. The original complete family, rational endpoints, assumptions
and decisions remain in the output unchanged. Copy this entire folder for
standalone offline Python 3.10+ use; only the standard library is needed.

One command from the repository root:

```sh
python3 -B shared/bounds-display/bounds_display.py demo
```

When tried, the synthetic 120-case, two-candidate example displayed intervals
**[26.36, 53.47] percentage points** for `improved` and **[-4.15, 4.15]** for
`unchanged`. The exact original intervals clear a +10-point improvement margin
and fit strictly inside a ±10-point equivalence margin, respectively. Both
criteria survive the default display precision. This demonstrates arithmetic;
no systems were measured by the synthetic example.

For a retained CSV, feed its original bytes on stdin and provide its separately
retained lowercase SHA-256. The following uses the line's actual previously
retained 18-case JSON-policy observations, not a fresh measurement:

```sh
python3 -B shared/bounds-display/bounds_display.py analyze --expected-input-sha256 c8e80ed4104f4f85c50a2df9d02c2dbb6ca47fc748ad545815adfe6475226d02 < line-1/tools/paired-bounds/retained-policy-results.csv
```

Observed intervals were [-20.31, 54.01] and [-7.48, 74.54] percentage points.
Neither candidate established either practical criterion at the supplied
10-point margin. Those curated cases are not independent representative draws:
the computation does not establish population performance. The input pin
preserves the exact bytes; it does not authenticate their measurement history.

The `analyze` command reads at most 2 MiB plus one rejection byte from stdin,
reads only its bundled Python engines, and writes JSON to stdout. It never
opens a caller-selected file. Missing or mismatched pins and invalid CSV fail
with exit 2 and no partial stdout. Exit 0 means an analysis completed, including
inconclusive comparisons. Demo rejects a caller pin because it creates its own
synthetic input. JSON uses ASCII escapes for labels; retain escaping if displaying
these labels in HTML or a terminal. Original identities are never normalized.

`--places 0..6` defaults to 2. `--alpha` defaults to 0.05 and accepts plain
decimals in [0.000001,0.2]; `--margin` defaults to 0.10 and accepts [0,1], both
with at most nine fractional places. The margin is an **absolute pass-rate
difference**, so 0.10 is ten percentage points, not a relative ten-percent gain.
Keep the sample size, complete candidate family, pass rule, alpha and margin
fixed prospectively. This wrapper retains the original caps of 512 cases and
16 candidates; it never drops cases or selects a candidate subset.

Each lower bound is rounded with floor, each upper with ceiling, using exact
fractions after multiplying by 100. Each endpoint expands by less than one
display quantum relative to the already conservative original interval. Negative
endpoints use mathematical floor and ceiling. Rounding errors mean displayed
minus exact, in percentage points. Original grid expansion remains unchanged.

`exact_criteria` repeats the original strict comparisons.
`displayed_interval_criteria` compares the enlarged interval to the **exact,
unrounded** margin. It may lose a criterion at a coarse precision but cannot
gain one; `criteria_lost_to_display_precision` names any losses. Equality at a
margin is inconclusive. For example [-9.9,9.9] lies inside ±10, but its outward
zero-place display [-10,10] no longer establishes strict inclusion. Do not
recompute a stronger conclusion from a rounded center, width or nearest-rounded
endpoint. Keep the original JSON alongside a reading view.

Statistical coverage needs the engine's fixed-sample independent identically
distributed case-vector assumptions. Correlation within each case is allowed;
correlated cases, outcome-selected families, optional stopping and repeated looks
invalidate that interpretation. Coverage is a repeated-sampling guarantee, not
a probability assigned to this particular observed interval. The conservative
binomial/Bonferroni method does not rank systems or prove measurement honesty.
A false criterion never establishes its opposite. Decimal display adds neither
measurement accuracy nor statistical information. No currency is needed.

Checks:

```sh
python3 -B gathering/run_suite.py discover -s shared/bounds-display -v
```

Eight integration tests passed, including 200 seeded Fraction-oracle enclosure
checks, exact/negative endpoints, strict boundaries, preservation of the entire
analysis, Unicode/BOM/CRLF identities, input pins, malformed data and a copied
standalone folder CLI. Three unchanged engine files ship with source paths and
SHA-256 hashes in provenance.json. No runtime packages, downloads, sibling tools,
accounts or external services are needed. The command above uses the repository
scratch harness; outside the repository use ordinary unittest discovery instead.
