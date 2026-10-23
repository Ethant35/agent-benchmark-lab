# Invoked skill evidence
Author: Ethan
Updated: 2026-10-22

Sources are project-local `../.agents/skills/<name>/SKILL.md`. Installation alone is
not execution. Local qualification is complete; this ledger does not claim every optional technique
from each skill or untested platforms. No hooks or Actions were enabled.

| Skill | Applied work and retained evidence | Limit / disposition |
|---|---|---|
| source-driven-development | SQLite connection lifetime/JSON, FastAPI boundaries, OpenRouter usage/reasoning docs; changes checked against actual runtime | Provider metadata and actual requests outrank examples |
| constraint-driven-development | CONSTRAINTS, AGENTS, executable floor checker and manual review | Twelve textual flags retained; see FLOOR_REVIEW; separate integration contract documented |
| documentation-and-adrs | READINESS, OPERATIONS, migration/rollback instructions, ADR-001 and changelog | Current release documentation |
| test-driven-development | API, resume, provider, legacy permissions, cleanup and evidence retry reproduced before fixes | 61 local and eight browser tests; not substitutes for external gates |
| property-based-testing | Hypothesis corpus generation and invariants | Corpus worker's evidence in CORPUS_QUALIFICATION |
| systematic-debugging | Stored failures, RED regressions, real timeout/cleanup probes, failed editable import | Import repaired by reinstall; original environment cause unknown |
| variant-analysis | Twelve-task review for schema/order/wording problems; four contracts versioned | Old results immutable; no model rescoring |
| api-and-interface-design | Additive paginated/overview interfaces, typed response envelopes, explicit sampling/null costs | Legacy unpaged exports/routes retained |
| security-and-hardening | Threat boundaries, no-follow files/locks, private stores, real resource limits, native dependency audits | Local single-user support; runtime/kernel escape immunity not claimed |
| sharp-edges | Unsafe IDs, unknown spend, task/config deadline, comparison identity and legacy resume | Refused unsafe cases and documented remaining deadline behavior |
| differential-review | Bounded read-only changed-path and call-chain review | Found legacy-root privacy issue; reproduced and fixed; retained snapshot |
| find-bugs | Provider/recovery/isolation/accounting source review and targeted regressions | No exhaustive/transitive dependency proof |
| semgrep | Approved local run-all Community workflow, six packs/three repos, merged/triaged evidence | Final 31 findings; fifteen rule errors and p/yaml unavailable; no Pro |
| harness-writing | Inspected native harness workflow; repository has no owned C/C++/Rust parser target | No native fuzz harness fabricated; Python HTTP fault/property controls used separately |
| performance-optimization | 10,000-row baseline/after measurement; compact SQL projection; one-pass capped UI matrix | Synthetic local evidence, not field profiling |
| observability-and-instrumentation | Correlated trace IDs, partial-cost fields, payload-free diagnostic counts | Local only, no hosted analytics or secrets in diagnostic export |
| deprecation-and-migration | Additive schema/routes; legacy record preservation; real wheel upgrade and backup/restore | Legacy manifestless resume deliberately refused; rollback documented |
| impeccable | Context/Operate/craft references, manual responsive/focus review and detector | Detector returned no findings; no claim of external panel/field review |
| baseline-ui | Existing stack retained, native controls/dialog, bounded layouts and clear states | Eight real/controlled browser cases |
| fixing-accessibility | Skip navigation, focus wrapping/return, scroll regions, contrast, axe | Axe clear in tested views; actual OS zoom/screen-reader certification not claimed |
| web-design-guidelines | Current Vercel primary guidelines, URL state, empty/error/loading/mobile review | Recorded in UI_QUALIFICATION |
| vercel-react-best-practices | Parallel independent requests, guarded versioned localStorage flag | Next.js/server-only rules not applicable |
| vercel-composition-patterns | Assessed current component/prop structure | No speculative compound-component refactor justified |
| code-simplification | Reviewed changed boundaries; retained focused fixes and one-pass aggregation | Long expressions remain readability debt; no broad cleanup solely for scan count |
| shipping-and-launch | Prelaunch gates, clean package/upgrade, rollback and local diagnostics | Local release gates satisfied; no cloud/canary deployment claim |
| verification-before-completion | Actual exits/outcomes checked and failures retained | Published assets downloaded, hashes matched and downloaded wheel task passed |

Primary references consulted in this work:
- https://docs.python.org/3.12/library/sqlite3.html
- https://www.sqlite.org/json1.html
- https://fastapi.tiangolo.com/tutorial/query-params-str-validations/
- https://openrouter.ai/docs/guides/features/tool-calling
- https://openrouter.ai/docs/guides/best-practices/reasoning-tokens

Initial contract tests used Python 3.13. Qualification uses frozen Python 3.12.14.
The local wheel and fresh upgrade environments also used Python 3.12.14. Each evidence
record names the kind of test; reference outcomes and controlled fixtures are not model scores.


## v1.2.0 usability and distribution phase

The seven explicitly requested workflows were loaded from their installed project-local
SKILL.md files. No new skill was installed and no hooks or global settings changed.

| Workflow | Application in this phase |
|---|---|
| shipping-and-launch | Wheel-first route, dependency audits, real first-use/return/update/recovery/rollback and downloaded-asset gate; no hosted rollout or field telemetry |
| api-and-interface-design | Additive CLI commands and read-only typed workspace identity/commands; existing run/config/schema/provider contract preserved; consent and unknown outcomes explicit |
| impeccable | Existing Operate surface refined; context/onboard/craft references, rendered mobile review and detector; no redesign or unfamiliar-user study |
| baseline-ui | Concise optional quick start, clear empty/loading/error/recovery states, no new animation/decorative hero |
| fixing-accessibility | Native controls, keyboard focus/return and axe checks, mobile reflow; OS assistive-tech certification not claimed |
| systematic-debugging | Reproduced hidden .pth imports, source harness assumptions, dashboard returning-state timing and label defects before targeted repairs |
| verification-before-completion | Fresh command results, package/source byte checks, real containers and browser checks gate release |
| test-driven-development (debugging support) | New guided consent/config/negative-control/terminal-control tests observed RED then GREEN; no fake response labelled live |

The old editable-import diagnosis above is historical. Current verbose Python import
output proves macOS hidden file flags cause `.pth` files to be skipped in this synced
workspace. Release-wheel imports and actual task execution passed independently.
The detailed current phase matrix is USABILITY_ACCEPTANCE.md.
