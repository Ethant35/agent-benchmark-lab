# Corpus qualification

Author: Ethan  
Qualified: 2026-10-22

This is the preserved October 22 qualification of versions 1.0/1.1.
For the current 2.0 contracts, see [GRADER_V2.md](GRADER_V2.md).

## Scope and evidence

The corpus contains twelve deterministic reference tasks. Their verifiers define
observable acceptance outcomes; task descriptions tell the model what outcomes
to produce. A passing implementation must meet the verifier and the prompt must
state every representation or wording constraint that the verifier enforces.

The most recent provider evidence is the one-attempt-per-task DeepSeek V4.1
Flash 1017 run in [`evidence/full-deepseek-1017/REPORT.md`](../evidence/full-deepseek-1017/REPORT.md)
and its raw records. That run used corpus task version 1.0, package 1.0.1,
streaming, and a 30-second effective deadline. It is a historical result; this
qualification does not rewrite or relabel its 8 PASS, 3 FAIL, and 1 TIMEOUT.
No provider was called for this contract repair, and the changed task versions
have not been scored.

## Findings and changes

The live order-filter trace contained one valid JSON object per matching line.
The verifier called `json.loads` once on the entire output and expected a JSON
array. The task said “compact JSON” without selecting one of those valid JSON
representations. Version 1.1 now requires one array, including an empty array
when there are no matches.

The document-index task asked for names, byte counts, an index, and hashes but
left the intermediate JSON structures partly implicit. The verifier required
`file`/`bytes` records and `sha256`/`document_count` keys. Version 1.1 specifies
the exact record fields, types, tokenization, order, digest inputs, and manifest
shape.

The configuration-navigation verifier required the literal substring
`caching` and at least 40 characters although the prompt only asked for a
brief explanation. The live answer was rejected on that lexical check despite
having correct extracted fields. Version 1.1 describes the required topics and
accepts common forms of “cache” while still checking that the explanation
covers port, retry, cache, and formats. Its pure checker is tested with
generated synonymous wording and with each required topic removed.

Variant review found a related order-contract problem in the multistep ledger.
Its verifier compared object member order in `totals.json`, but JSON objects are
unordered by [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259.html#section-4).
Version 1.1 uses an array of `{account, total_cents}` records so first-seen
order is part of the data model. It also specifies all intermediate and
manifest schemas. The historical ledger attempt timed out during provider
response six at the 30-second deadline; that trace does not establish a model
or prompt cause. The task contract is now clearer, but its reference/unsolved-control
qualification has now passed through actual containers.

The other eight tasks were reviewed against their verifiers. Their outputs,
fields, ordering, and behaviors are sufficiently described for their current
verifier contracts. No further mismatches were confirmed. This is a bounded
manual contract review, not evidence that the task set is broadly representative
or that its answer quality has external validity.

## Versioned contracts

These tasks have new contracts and must be scored as new task versions:

| Task | Historical version | Current version | Contract change |
|---|---:|---:|---|
| `feature-order-filter` | 1.0 | 1.1 | Specify one JSON array |
| `multistep-document-index` | 1.0 | 1.1 | Specify intermediate and manifest schemas |
| `multistep-ledger` | 1.0 | 1.1 | Specify schemas and represent ordered totals as an array |
| `navigation-config` | 1.0 | 1.1 | Accept equivalent cache terminology; remove unstated length floor |

Existing stored trials and reports remain version 1.0 evidence. Do not compare
the new scores as if the contracts were unchanged. Re-run only with explicit
authorization and a bounded spend allowance; no such run was part of this
repair.

## Verification

Local contract suite:

```sh
.venv/bin/pytest tests/test_corpus_contracts.py -q
```

The tests parse the task YAML, check that affected prompts include the required
contract details, apply Hypothesis-generated explanation variants to the pure
navigation contract checker, reject explanations missing any required topic,
and confirm that the historical full-run evidence remains version 1.0 / package
1.0.1. They do not execute candidate code on the host or call a provider.

The benchmark verifier itself is packaged into the isolated container. All twelve current reference tasks passed and all twelve unsolved controls failed through
actual containers. See evidence/readiness/cli-acceptance.json and corpus-negative.json.
This establishes verifier execution for the new contracts, not new model scores.

## Skill use

| Skill | Application | Output and verification |
|---|---|---|
| `source-driven-development` | Read repository stack (`requires-python >=3.12`, PyYAML 6 range), Python JSON documentation, and RFC 8259 §§4 and 5. | The prompts choose explicit JSON structures; the ledger uses an array because JSON objects are unordered. Sources: [Python `json`](https://docs.python.org/3.13/library/json.html), [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259.html). |
| `constraint-driven-development` | Converted each confirmed verifier expectation into a prompt contract and local regression assertion. | Focused suite checks task versions and required schemas; no acceptance threshold was relaxed. |
| `systematic-debugging` | Read saved provider error traces and verifier stderr before making changes. | Reproduced the order JSON parse mismatch and navigation lexical rejection from preserved artifacts; distinguished ledger's deadline event from a verifier issue. |
| `variant-analysis` | Compared every task description to the verifier; traced the ordering issue across order-filter and ledger. | Found JSON object's unordered semantics in the ledger verifier and changed the output representation. Review covered all 12 tasks. |
| `test-driven-development` | Added tests first and ran the focused suite before updating contracts. | RED: 5 failing tests exposed old task versions and missing pure checker. GREEN: `.venv/bin/pytest tests/test_corpus_contracts.py -q` returned `7 passed`. |
| `property-based-testing` | Used Hypothesis to vary equivalent cache wording, separators, and missing required topics. | Deterministic bounded strategies test acceptance of paraphrases and rejection when any concept is omitted. |

Hypothesis 6.170.6 and pytest 9.1.1 (with pluggy 1.7.0) were installed in the
local `.venv` for these checks; the parent production-readiness lead is
recording the exact development dependency versions. They are not runtime
dependencies.
