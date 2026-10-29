# Version 2.0 task contracts
Author: Ethan
Date: 2026-10-28

All twelve tasks now use version 2.0. These are new contracts and must not be
pooled with 1.0/1.1 scores. Historical trial records, costs and reports are unchanged.
The exact previous canonical corpus is retained in `corpus_history/2026-10-27/`;
earlier versions also remain in Git history and release tags. No new model result
was collected. The original 30-second task deadline is unchanged.

| Gap | Version 2.0 correction |
|---|---|
| Correct CLI with a broken requested function | Call rounding, interval-merge and slugify functions directly as well as their CLIs. Specify return types and import behavior. |
| Narrow programming examples | Add deterministic generated interval/decimal cases, Unicode/empty slug cases, and filter datasets covering fractional/negative limits, nonempty pending matches, extra fields and empty input. |
| Implicit extraction schemas | Explicit single-array, exact-key and type contracts. These tasks extract the supplied document; they do not ask for general extractor software. |
| Keyword prose grading | Navigation explanations are now structured source claims. The grader checks exact symbols/values or paths/methods, types and unchanged source bytes. Contradictory claims fail. No prose length or keyword proxy remains. |
| Numeric type confusion | Recursive type checks reject floats/booleans for integer fields, including nested pipeline cents, byte counts and counts. JSON duplicate keys fail. |
| Grader creating missing work | Pipelines must leave correct artifacts present before verification. The grader checks them first, then tests the implementation on different/empty inputs. It no longer supplies missing original outputs. |
| Unobservable execution history | The task explicitly grades saved artifacts and executable dependencies. It does not claim that output files prove the agent's command chronology. |
| Incomplete pipeline cases | Add reordered accounts/files, negative/exact decimal amounts, UTF-8 byte counts, ASCII punctuation trimming, empty tokens and empty input. Clarify tokenization and types. |
| Refactor helpers only checked by name | Call helpers with varied inputs and verify outputs; profile the CLI to confirm both helpers execute. Require modules to import without CLI side effects. |
| Unchecked sorted serialization | Validate key order recursively in emitted refactor JSON while allowing whitespace differences. |

The independent checker runs as the trusted verifier; all candidate imports,
function calls and CLI executions run as UID/GID 65534 in the isolated verifier
container, with no network or host mounts. Pure host tests load only trusted schema
helpers, never candidate programs. Runtime/provider/isolation adapters are unchanged.

Navigation now measures structured explanation of source facts, not prose quality.
This deliberate contract change is why the version changes. It neither rescales
old attempts nor implies that an old rejected explanation was a model failure.
Likewise, fixed-document extraction is deliberately scoped to the supplied file.

Finite cases cannot prove general correctness or defeat every grader-aware program.
The strengthened suite catches the specific reviewed gaps and targeted controls;
it is not a claim of adversarial robustness or broad task representativeness.
Execution profiling proves helpers are called, not that every possible program
must use their return values correctly in every untested situation.

## Checks

- `uv run --frozen python -m pytest -q` covers current contracts, schema properties,
  historical contract checks, comparison isolation and the existing harness suite.
- `uv run --frozen python tests/grader_v2_e2e.py --root NEW_DIRECTORY` runs correct
  references, unsolved tasks, alternate valid JSON and deliberate mutants in real
  containers. It does not call a provider. The output folder must be fresh.
- Frozen frontend build and browser acceptance continue to use preserved saved
  results plus explicitly labeled UI fixtures.

See `evidence/grader-v2-20261028/` and the latest handoff for final measured counts.
A task version bump is not a new package release; public v1.2.1 assets remain sealed.
