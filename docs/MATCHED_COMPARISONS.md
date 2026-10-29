# Matched comparisons from saved results
Author: Ethan
Date: 2026-10-28

The dashboard's **Matched comparisons** control compares two configurations on
identical saved task contracts. Current run/provider/model/task filters apply.
Select configurations A and B, inspect changed settings, then open an attempt
for its verifier evidence. Export comparison JSON to retain the same calculation.
The existing configuration table remains an unmatched summary, not a ranking.

## Matching and accounting

`GET /api/comparison?left=<configuration SHA256>&right=<configuration SHA256>`
reads compact trial fields, configurations and manifests in one SQLite snapshot.
It checks each saved configuration hash, corpus manifest hash, task slot, task
version, task artifact and image against that manifest. A match requires the
same task/version/artifact, fixture hash, image and runner kind. Different task
selections can still share an equivalent task. References cannot match agents;
versioned integration tasks cannot match the original benchmark contract.

All retained terminal attempts contribute, including retries and interruptions.
Attempt pass rates do not replace the existing scheduled/recovered outcome view.
Each side shows outcome classes, cost sources, total known costs, missing totals,
median duration and attempt links. Configured limits and harness/provider errors
stay separate from verifier rejections. None of these labels alone establishes
model fault. A live run is marked active; terminal-attempt costs are not a final
run total. Unknown-cost attempts retain their known subtotal without double-counting.
Cost differences are omitted when totals or matching cost-source coverage are missing.

The API reports exclusions for nonterminal attempts, unverifiable identity and
no equivalent task. It computes each matched group's totals over all retained
attempts. At most 200 task groups and 100 evidence links per side/group are shown,
with explicit limits; filters allow narrower inspection. Existing exports and
aggregate percentages are unchanged. Endpoint/key-environment differences have
withheld values. Harness version, provider routing and time of day are not matching
keys: the stored identity format does not prove these are constant. Results are
observational, not randomized causal estimates or independent paired trials.

## Observed integration comparison

Source: the existing October 22 DeepSeek V4.1 Flash 1017 integration records,
`evidence/readiness/live-integration/`. No new provider requests or charges.
Both arms used `bugfix-rounding`, version `1.0-integration-120s`, the same saved
task/fixture/image hashes and the same configuration except streaming. The
original integration manifest records the package copy used for these runs.

| Configuration | Attempts | Passes | Wall time | Actual provider cost |
|---|---:|---:|---:|---:|
| Streaming | 1 | 1 (100%) | 27.097883 s | $0.000651070 |
| Nonstreaming | 1 | 1 (100%) | 40.464801 s | $0.000678698 |
| Intentional zero-tool streaming control | 1 | 0 (0%) | 4.896488 s | $0.000073420 |

Nonstreaming minus streaming: 0 percentage points, +13.366918 seconds and
+$0.000027628. Combined cost for those two attempts: $0.001329768. The diagnostic
zero-tool control had `max_tool_steps=0` and `max_requests=1` rather than the
ordinary null/default tool limit and eight requests. Its configured-limit failure
is expected evidence about the restriction, not evidence of a broken harness or
a model ranking. All three charges total the previously reconciled $0.001403188.
The streaming attempt appears in both pair reports; do not add the reports' totals.

There is one observation per setting on one task. These values cannot establish
reliability, uncertainty intervals, a causal speed/cost benefit or a full-corpus
ranking. Earlier 30-second timeouts remain separate. The historical twelve-task
run remains 8 PASS / 3 FAIL / 1 TIMEOUT, with original costs and contract issues.
See [task and grader audit](TASK_GRADER_AUDIT.md) before interpreting those failures.

Reports:

- [Streaming versus nonstreaming](../evidence/matched-20261028/streaming-vs-nonstreaming.json)
- [Streaming versus zero-tool control](../evidence/matched-20261028/streaming-vs-zero-tool-control.json)

Each report contains the task/image identity, configuration differences, attempt
IDs, verifier exit codes, outcome classes, costs, input snapshot hash and exclusions.
The original record payloads and historical reports are not rewritten.

## Reproduction without model calls

From the repository, open an existing database read-only:

```sh
uv run --frozen python -m scripts.compare_saved \
  --database .abl/readiness-live-protocol/integration/results/results.sqlite3 \
  --left d2d2fda10b892f5e8c7862b5ef5aa73ac932e07d5e24b18bcd2ad9e6b3433dc8 \
  --right f346c32db5df4c242b63a0513670e3059416d691e1a7d8b37eac349cd0542241 \
  --output /tmp/streaming-comparison.json
```

The database above is private local evidence, not part of the public source tree.
The committed reports are available without that database. The helper does not
launch a benchmark, execute candidate code or access a provider. For browser
acceptance, use a disposable copy containing the saved integration records and
the earlier free/recovery records. Synthetic boundary cases in tests are labeled
fixtures and never presented as model measurements.
