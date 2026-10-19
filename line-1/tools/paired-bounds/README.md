# Paired Bounds

Report simultaneous confidence bounds for **candidate minus baseline pass rate**
on complete paired binary benchmarks. A worker can ask whether the evidence
clears a prespecified useful improvement, or is precise enough to fit within a
prespecified equivalence margin. This complements the line's significance tests:
non-rejection alone does not answer either question. Existing tools are unchanged.

Python 3.10+, standard library only. Copy this entire folder for standalone,
offline use. From the repository root, one command demonstrates it:

```sh
python3 -B line-1/tools/paired-bounds/paired_bounds.py --demo
```

When tried, the explicitly **synthetic** 120-case, two-candidate demo gave:

| Candidate | Observed difference | Simultaneous interval, approximately | Planned 0.10 margin |
| --- | ---: | --- | --- |
| improved | 0.416667 | [0.263698, 0.534653] | lower bound exceeds +0.10 |
| unchanged | 0 | [-0.0414113, 0.0414113] | entire interval inside (-0.10, +0.10) |

These are pass-rate differences: 0.10 means ten percentage points. The familywise
coverage is at least 95% **under the stated sampling assumptions**. Approximate
decimals in this README are for reading; the JSON retains exact rational bounds
and every decision uses those fractions. `example-result.json` is actual demo
output. No systems were measured by the synthetic demonstration.

## Use your own benchmark

Use UTF-8 CSV, with optional BOM, quoted fields and CRLF:

```csv
case,baseline,model-a,model-b
request-a,0,1,0
request-b,1,1,1
request-c,1,0,1
```

Every row must contain the same case's literal `0`/`1` outcomes for baseline and
**every** planned candidate. Labels are preserved, not normalized. Case IDs must
be unique; labels have 1–200 characters, no edge whitespace or Unicode categories
starting with C. Blank rows, missing values, extra fields, duplicate/reserved
header names and malformed CSV are errors. Limits: 1–512 cases, 1–16 candidates,
2 MiB per input. No partial-family or dropped-case fallback exists.

Retain the raw input SHA-256 independently at handoff. Replace these uppercase
tokens together with your actual file and retained digest:

```sh
python3 -B line-1/tools/paired-bounds/paired_bounds.py --input RESULTS.csv --expected-input-sha256 RETAINED_SHA256 --alpha 0.05 --margin 0.10
```

Alpha is a plain decimal from 0.000001 through 0.2; margin is from 0 through 1.
Both allow up to nine fractional places. Choose both before seeing outcomes.
The file must resolve to a regular file inside the current working directory;
symlinks escaping it are refused. Raw bytes, including BOM and line endings,
enter the digest. The runtime only reads that file and writes JSON to stdout;
it does not change inputs or read environment variables. Exit 0 means complete
analysis, including inconclusive results; exit 2 means invalid input or pins,
with no partial stdout. Preserve JSON escaping when displaying labels in HTML.

`candidate_exceeds_positive_margin` requires the lower bound to be strictly
greater than +margin. `baseline_exceeds_positive_margin` requires the upper
bound strictly below -margin. Equivalence requires the entire interval strictly
inside (-margin,+margin). All comparisons are conservative sufficient criteria,
not a ranking, recommendation or separate p-value. Equality does not pass these
strict criteria; margin zero cannot establish equivalence. A false field means
that criterion was not established, not that its opposite was established.

## Exact calculation

For one candidate count `w` candidate-only passes and `l` baseline-only passes
among all `n` cases. Let their population probabilities be `q_w` and `q_l`.
The paired pass-rate difference is `q_w - q_l`. Each count marginally has a
Binomial(n,q) distribution under independent identically distributed case vectors.
The two counts need not be independent; neither do candidates within a row.

For `m` candidates allocate `t = alpha/(4m)` to each of the two tails of each
of the two binomial proportions per candidate. Compute conservative
Clopper–Pearson endpoints by inversion. For nonzero observed count k, its lower
endpoint solves `P_p[Bin(n,p) >= k] = t`; the upper is one minus the lower
endpoint for n-k. Counts zero/n retain their exact endpoint zero/one.

Bisection on the 2^-32 grid uses **integer binomial probabilities**, comparing
integer numerators against the exact rational t. Each lower endpoint rounds
outward down, and each upper endpoint rounds outward up. No floats, beta
approximation, bootstrap, normal approximation or random simulation is used.
Subtract `[L_w-U_l, U_w-L_l]`. By the union bound all reported intervals jointly
cover their true effects with probability at least 1-alpha. Dependence across
candidates is allowed. The method is conservative; it does not exploit the full
multinomial constraint to shorten intervals, and its bounds need not agree with
McNemar/Holm rejection decisions, which use a different procedure.

Each binomial endpoint is expanded by less than or equal to 2^-32 relative to
the ideal endpoint; a difference endpoint expands by at most twice that.
Binomial tail terms use a common integer denominator and exact divisible
recurrences. Repeated count endpoints are cached within a report. Work is
bounded by 512 cases, 16 candidates and 32 bisection steps per endpoint.

## Assumptions and limits

Fix the final sample size, case sampling, pass rule, full candidate family,
alpha and practical margin prospectively. Cases must be independent draws from
the same target distribution. Multiple seeds/tasks for one user or document may
violate that assumption. The cluster tools offer a different protocol; merely
renaming correlated cases does not make these bounds valid. Curated fixed
examples do not supply population sampling by themselves. These bounds do not
support repeated looks, adaptive stopping or outcome-selected families.

Coverage is a repeated-sampling guarantee, not a 95% probability assigned to
this observed interval. A digest cannot prove honest outcomes, preregistration
time, measurement quality or representative sampling. Binary pass rate does
not address latency, costs or severity. A practical threshold is supplied by the
worker; the tool cannot decide what matters operationally. Wide intervals are
inconclusive, not equivalent. There is no currency, price, payment, balance,
pool, chain, network, key, wallet, signing, sending, posting or deployment need.

## Retained measured workload

`retained-policy-results.csv` copies the exact 18-case observations previously
retained by Cluster Stability from the line's actual local JSON-policy workload.
This step **did not reexecute or certify** the measurements. The groups are
curated examples, not a random population sample: the coverage interpretation
must not be applied to them. They exercise the tool on existing real-workload
bytes, as an arithmetic demonstration. `retained-policy-bounds.json` contains
the analysis plus explicit provenance and this limitation.

```sh
python3 -B line-1/tools/paired-bounds/paired_bounds.py --input line-1/tools/paired-bounds/retained-policy-results.csv --expected-input-sha256 c8e80ed4104f4f85c50a2df9d02c2dbb6ca47fc748ad545815adfe6475226d02 --margin 0.10
```

When tried, the constants guard's interval was approximately [-0.2031,0.5401]
and the unique/finite guard's [-0.0748,0.7453]. Neither cleared a +0.10 margin
or fit wholly inside ±0.10. These calculations do not establish population
performance of either policy.

## Checks

```sh
python3 -B -m unittest discover -s line-1/tools/paired-bounds -v
```

Eleven tests passed locally. Independent Fraction/binomial formulas check tail
numerators and outward brackets. Exhaustive small binomial and three-category
multinomial probabilities check coverage at specified rational models. Further
checks cover baseline swap symmetry, alpha/family monotonicity, the demo,
Unicode/BOM/CRLF, malformed CSV, caps/types, maximum precision, independent pins,
symlink escapes, input immutability and a copied-folder offline CLI. These tests
exercise stated behavior; they are not independent statistical certification.
All runtime source is new and standalone; no predecessor engine is needed.
