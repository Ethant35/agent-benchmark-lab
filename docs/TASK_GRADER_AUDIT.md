# Task and grader audit — 2026-10-28
Author: Ethan

Reviewed all twelve task YAML files, fixtures and grader source files before adding
comparisons. This is a source audit. No model was called and no historical score
was changed. The existing reference/unsolved runs establish execution on their
saved bytes; they do not establish complete grader coverage or general model ability.

| Task / version | What the grader checks | Limits or mismatch |
|---|---|---|
| bugfix-interval-merge / 1.0 | Four CLI cases: touching, sorting, empty and negative intervals; compact JSON | Does not call the requested function directly; finite examples permit hardcoding. |
| bugfix-rounding / 1.0 | Five CLI cases, including positive/negative ties, zero and carry | Does not call `format_price` directly; no broad decimal-domain coverage. |
| extraction-contacts / 1.0 | Exact ordered records, lowercase email and original phone strings | Fixed fixture only. Array shape is implied by the starter `contacts.json`, not explicit in the description. |
| extraction-invoices / 1.0 | Exact ordered records, keys and integer cents | Fixed fixture only. Array shape is implied by the starter output. |
| feature-order-filter / 1.1 | Inclusive paid boundary, full records in order, empty pending result | Two CLI cases; no nonempty pending case or general numeric-input coverage. |
| feature-slugify / 1.0 | Four stdin examples: accents, punctuation, numbers, empty slug | Does not call `slugify(text)` directly; Unicode coverage is narrow. |
| multistep-document-index / 1.1 | Three commands, exact records/index, punctuation and SHA-256 over actual output bytes | Float byte counts and document count can compare equal to integers. Fixed two-document fixture. Grader invokes commands itself, so it cannot prove the agent ran them in order. |
| multistep-ledger / 1.1 | Three commands, ordered normalized rows/totals and output digests | Totals enforce integer type; normalized cents and row count do not. Grader execution cannot prove the agent's execution order. |
| navigation-config / 1.1 | Unchanged source digest, exact facts/types and four explanation keywords | Keyword coverage is not semantic accuracy. A contradictory sentence containing those keywords can pass. Equivalent wording outside the regex may fail. |
| navigation-routes / 1.0 | Unchanged source digest, exact routes/order/count and explanation strings | **Unstated constraint:** explanation must contain `/health`, `/items`, GET, POST, DELETE and at least 40 characters. Keyword checks do not prove a correct explanation. |
| refactor-csv-summary / 1.0 | Named functions exist; four CLI inputs match trusted baseline | Does not prove the helpers are used or correct. Parsed JSON equality does not check requested sorted-key serialization. |
| refactor-text-stats / 1.0 | Named functions exist; four CLI inputs match trusted baseline | Does not prove helpers are used or correct. Parsed JSON equality does not check requested sorted-key serialization. |

The reviewed gaps are addressed by the separately versioned [2.0 contracts](GRADER_V2.md).
This audit describes the earlier bytes; its historical findings remain unchanged.

## Interpretation of existing results

The preserved twelve-task DeepSeek run used version 1.0 tasks and package 1.0.1:
8 PASS, 3 FAIL, 1 TIMEOUT. Its order-filter representation and navigation-config
wording failures have confirmed contract ambiguity. The document-index attempt
hit its step limit under an underspecified schema; the relative effects of the
model, limit and contract are unresolved. The ledger timeout establishes a deadline
event, not its root cause. See `CORPUS_QUALIFICATION.md` and the original report in
`evidence/full-deepseek-1017/`. Do not convert these observations into model-error
counts or rescore historical attempts.

Keep verifier rejection, configured limits, provider errors, harness errors and
interruption separate. A verifier rejection alone does not prove model fault.
References and intentional restriction controls are diagnostic evidence, not a
model leaderboard. Historical 30-second tasks and 120-second integration tasks
are different contracts even when their problem text is similar.

## Before any new model collection

Version corrections to the routes explanation contract and strengthen the gaps
above with positive variants and targeted negative controls. Require explicit
output schemas and objective acceptance criteria; avoid lexical proxies for prose
quality. Verify changed graders in isolation against correct and deliberately wrong
implementations. Keep prior task hashes and results intact. This audit does not
change graders or authorize a new corpus score or paid collection.

Pure checker/equality probes confirm the navigation keyword false positive and
numeric-type/JSON-order gaps. See `evidence/matched-20261028/audit-probes.json`.
These checks execute no candidate programs and are not new container qualification.

Matched comparisons require saved manifest/configuration identity, identical task
version and artifact hash, identical fixture/image identity and the same runner
kind. Show configuration differences, every retained attempt count, known versus
missing costs and outcome classes. Unmatched or unverifiable records are excluded
with counts. Small observational samples cannot establish a causal advantage or
rank configurations across the full corpus.
