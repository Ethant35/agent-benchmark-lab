# Agent Benchmark Lab handoff
Author: Ethan

## Current qualification checkpoint — 2026-10-22, 22:36 PDT
Author: Ethan

Candidate 1.1.0 remains **unreleased and incomplete**. No readiness commit, PR, push,
tag or release was made. Branch codex/production-readiness; baseline 381caf28ec2d73dc6e87d0956ff2afcde986cced.
This is a saved checkpoint, not a new user-requested pause or a claim of completion.
The goal tool previously remained paused because its API cannot resume it; resumed
work followed Ethan's direct instruction. Do not create a replacement goal to hide this.

Completed local qualification: 61 pytest passes, eight browser passes on a fresh wheel,
zero axe violations in tested views, fourteen real resource cases, 128 MiB/16,384-inode
workspace control, all twelve references PASS and all twelve unsolved controls FAIL.
Fresh wheel task PASS. Real v1.0.1 upgrade plus backup/restore preserved export content.
Seventy-five runtime/corpus/static files match final wheel, tested install and sources;
Author Ethan verified. Both dependency audits found zero vulnerabilities. Actions
rechecked disabled with zero runs; no global config/hook changes. Final source manifest,
package evidence and exact limitations are under evidence/readiness/ and READINESS.md.

Final approved Semgrep plan ran as static_analysis_semgrep_3: seven scans exit 0,
Elttam and Apiiro exit 2 with partial results (12 and 3 rule errors). No TSX target
parse errors. Thirty-one findings (25 long-line indicators, six intentional execution
sites) retained and triaged; p/yaml unavailable, Community only. No claim of complete
coverage. Rule clones removed; raw local reports retained. Floor checker still exits 1:
two CSS skip-link false positives and nine replaced pagination assertions manually
reviewed in docs/FLOOR_REVIEW.md; no suppression, skipped test or guard override.

Live gate OPEN: three real readiness attempts timed out at the unchanged 30-second
task limit. Low/none reasoning and request caps are recorded in .abl/readiness-live,
.abl/readiness-live-none and .abl/readiness-live-capped-2. The first capped attempt
(.abl/readiness-live-capped) made zero requests after an editable CLI import failure;
forced local package reinstall restored imports, original cause unknown. The harness
stopped on its first assertion, so current nonstreaming normal success is not verified.
Do not label the old v1.0.1 smoke run as qualification of new provider code.

All eleven readiness generation charges later reconciled exactly with two matching
key readings: **$0.001900464**, zero unattributed difference, no missing generations.
Evidence: evidence/readiness/live-reconciliation.json. Original interrupted trial costs
remain null, preserving observed records. No more inference retries were made. Key used
only through hidden input/process memory; no matching credential in candidate files.
Original full12 remains 8 PASS/3 FAIL/1 TIMEOUT, observed charge $0.014957188; earlier
smoke $0.003375022 stays separate. No full12 rerun or retrospective rescoring.

Remaining: choose a bounded live integration design that addresses observed latency
without weakening or relabelling benchmark contracts, complete actual streaming and
nonstreaming success/restriction checks, then final review/commit/package/publication
and downloaded-asset verification only after every gate closes. No automatic paid
retry loop. Current local docs include operations, migration/rollback, ADR, skill ledger,
security/floor/UI reviews and unreleased changelog. Long expressions remain readability
debt, not hidden scanner suppressions. OS zoom/field telemetry/Docker remain unqualified.

Shutdown: all owned containers/volumes were empty before stopping abl-benchmark VM.
Own dashboard PIDs 91235 and 87514, holding sleeps 61169 and 63740 were terminated.
No provider process or worker remains. The 45-second usage checker is closed at end of
this checkpoint; final direct reading 35% used / 65% remaining. On any continuation,
start a fresh checker and stop at >=90% used / <=10% remaining in any applicable window.
Never buy credits/reset/switch accounts automatically. Preserve the numbered copies
under .abl/preserved-duplicate-files-20261022 and all historical evidence.

## Resumed — 2026-10-22
Author: Ethan

Ethan explicitly revoked the pause through the coordinating chat. Initial account
reading: 5% used, 95% remaining. Session checker cell 10 checks every 45 seconds (cell 2 was replaced to emit readings).
New mandatory stop: any applicable window at **90% used / 10% remaining**.
The goal record still reports paused; its API cannot resume status. Work is resumed
under the explicit instruction, without creating a replacement goal.

Preserved 81 extra untracked numbered copies under
`.abl/preserved-duplicate-files-20261022/` with SHA256 inventory. These files were
not in the saved pause inventory; including fixture copies would change candidate
inputs. No copy was deleted or used to overwrite canonical edits.

Active work: resume-ID and immutable-manifest repair from nine confirmed failing
tests. One bounded Luna UI worker owns dashboard source/tests and UI qualification.
No provider calls. Prior pause details below remain the baseline, not a new stop.

### Resume progress snapshot

- 55 local tests pass after resume manifest, ID validation, private DB/root,
  bounded safe trace reads, additive comparison grouping, backup/restore with
  integrity manifests and activity locks, and payload-free diagnostics.
- New files: abl/recovery.py, tests/test_isolation_edges.py,
  tests/test_recovery_privacy.py. CLI adds backup/restore/diagnostics.
- UI worker completed build plus six browser checks and stopped server8766.
  Same worker now performs bounded read-only differential review.
- Podman first startup died after command exit; next had gvproxy readiness error.
  Frozen editable reinstall repaired missing CLI import. Debug startup succeeded
  with holding session89410; redundant holding sleep61169/session15792 remains.
  No global Podman configuration/rootful/helper changes.
- Resource roots3 setup failed;4 passed ten cases then reproduced Darwin zombie
  killpg EPERM masking timeout. Two diagnostic retries retained in root4.
  Fix confirms no live group member before treating EPERM as completed cleanup.
  Current resource suite root5/session7163; CLI acceptance root1/session95839;
  all12 negative controls/session79203. Own these only during shutdown.
- No readiness provider spending yet. Live adapter check, final scan/audit,
  package/upgrade/release, review repairs and final documentation remain open.

## PAUSED at Ethan's explicit instruction — 2026-10-22
Author: Ethan

This section supersedes all older active-work instructions below. **Do not resume
without a new instruction from Ethan.** The stop instruction arrived from the
coordinating chat and explicitly permitted only safe shutdown and this handoff.
The goal tool actually returned `status: paused`; it was not marked complete.

### Objective and checkout

Full objective: Qualify Agent Benchmark Lab for real local users through the
explicitly invoked project-local skills: define support/security scope and
executable readiness criteria; fix verified correctness, isolation, recovery,
cost/accounting, UI/onboarding and maintenance defects; validate fresh/upgrade/
package and live supported paths within existing spending limits; retain skill-use/
readiness evidence, HANDOFF, disabled Actions, and account-usage stop monitoring.
Release only after qualification.

Local path: `/Users/ethantarnarider/Documents/ChatGPT/Open source/agent-benchmark-lab`
Branch: `codex/production-readiness`
HEAD: `381caf28ec2d73dc6e87d0956ff2afcde986cced`
No readiness commit, push, PR, merge, tag or release was made. All work is local and
unfinished. Historical v1.0.1 and full-provider benchmark evidence is preserved.

### Completed changes, with limits

- Added `CONSTRAINTS.md`, `READINESS.md`, root `AGENTS.md`, skill-use/security/UI
  evidence docs. The matrix still has open gates; some rows predate the final work
  in this handoff. This section is authoritative for the pause state.
- Four corpus contracts updated to v1.1: order-filter, document-index, ledger,
  navigation-config. Ledger ordered totals now use an array. Navigation wording
  accepts equivalent cache terms. Historical v1.0 outcomes were not rescored.
- Added compact `/api/trials/page` and `/api/overview`, preserving legacy endpoints.
  SQL filters are parameterized; overview summary covers all matching terminal
  trials; chart data explicitly samples at 2,000. Added measurement coverage and
  actual/estimated cost counts. DB context scopes now commit/rollback and close.
  Added local-origin/no-store/security response handling.
- Dashboard now uses paginated data, native detail dialog with explicit keyboard
  wrapping and return focus, replayable local onboarding, improved contrast and
  scroll-region access. Failed detail fetch no longer pretends compact data is full
  evidence. Final small JSX spacing normalization is not in the last built static
  bundle. More UI state, readability and performance work remains.
- Provider uses bounded raw HTTP reads (8,000,000 bytes total, 1,000,000 bytes per
  SSE line/event), identity encoding, multiline SSE and completion-marker checks,
  stricter usage/tool structure validation and finite config prices. Generation
  IDs are saved from headers/events before completion. Request intent is recorded
  only after reserve preflight; pending costs remain unknown and prior subtotal is
  retained. A refusal before transmission stays zero cost. No current live-provider
  verification has been run after these changes.
- Workspace volume is tmpfs, 128 MiB / 16,384 inodes, with a sleep-only keeper to
  retain data through stop/snapshot/verification. Rootless tmpfs required mode 0777
  at mount and chmod only of extracted children. Keeper is container UID 0 with
  all caps dropped and no candidate commands. No unbounded storage fallback.
  Cleanup precedes artifact-event persistence; cleanup attempts each owned resource.
- Locked pytest 9.1.1 and Hypothesis 6.170.6 in Python dev dependencies. Dashboard
  dependencies pinned to installed lock versions and axe-core Playwright added.
  Fresh frozen Python 3.12.14 environment: `.abl/readiness-env`.

### Last actual verification and known failures

- Last entire pytest run: **33 passed**, Python 3.12.14, before the later finalization
  test and resume-contract tests were added. Do not describe current whole suite as
  green. One Starlette warning says its httpx TestClient integration is deprecated;
  production HTTPX remains 0.28.1. Warning was not suppressed.
- Finalization fault injection: baseline `381caf2` **fails** because artifact-event
  persistence prevents cleanup; current implementation **passes 1 test**. This is
  control-flow evidence, not a full storage failure acceptance suite.
- **Current `tests/test_resume_contract.py`: 9 FAIL** by design of the next RED step.
  No repair was started before stop. `corpus_manifest`, `image_identity`, and
  `Store.manifest` do not exist. `run_suite` still permits malformed resume IDs to
  reach filesystem path construction and has no immutable corpus/image manifest.
  Empty resume string starts a fresh run. The controlled test uses runtime `unused`,
  so it did not execute candidate code. One reproduction opened `/tmp/absolute.lock`;
  future tests should use a unique absolute path inside their temporary root.
- Last dashboard build and full Playwright suite: **4 passed (4.9 seconds)**.
  Three tests read actual historical SQLite results through the real API. The
  fourth uses a clearly controlled 250-row API fixture. Axe main/dialog, exports,
  filters, evidence, all tab stops, both wraps, Escape, trigger focus, onboarding
  persistence and 320px/390px behavior passed. Screenshots retained at
  `dashboard/test-results/dashboard.png` and `dashboard-mobile.png`; mobile inspected.
  Source spacing changed afterward only to repair Semgrep TSX parsing, not rebuilt.
- Controlled 10,000-row history comparison: baseline median 1.047s / 410,863,740
  peak Python bytes / 127,952,195 response bytes; revised 0.391s / 15,910,897 /
  1,256,915. Both keep all summary denominators. Evidence in
  `evidence/readiness/history-performance-{1,2}.json`; first attempt retained too.
- Real workspace RED: `.abl/workspace-before/result.json` reports shared capacity
  12,279,853,056 bytes and no ENOSPC. Two subsequent probes failed setup permissions
  and are preserved (`.abl/workspace-after`, `...-after-2`). Final probe
  `.abl/workspace-after-3/result.json`: **PASS**, exact 134,217,728 bytes, 16,384
  inodes, ENOSPC on excess write, valid independent verifier, bounded artifact,
  empty cleanup errors. It is a rounding-task probe, not all corpus acceptance.
- Resource regression `.abl/readiness-resources` failed initial tmpfs permissions.
  Fixed version `.abl/readiness-resources-2` was **interrupted by this stop request**,
  not completed. Eight cases finished with expected outcomes: explicit truncation,
  three fast-output attempts, sustained output, dual streams, oversized artifact,
  stderr limit. Those records have empty cleanup errors. Do not claim 14/14 or
  current cancellation/SIGKILL/resume coverage. Remaining cases did not complete.
- Approved Semgrep run-all scan executed nine scans and merged 30 findings. No
  process failed/skipped; however raw records show partial TSX parsing plus rule
  parse errors (12 Elttam, 3 Apiiro), so coverage is partial. 24 long-line warnings
  and 6 intended dynamic execution boundaries need final triage/review. No secret
  findings. `p/yaml` was unavailable (404) and excluded from the approved plan.
  Initial scan predates provider/isolation changes; final scan remains undone.
  Raw plan/scans: `static_analysis_semgrep_1/`; copied initial SARIF/JSON under
  `evidence/readiness/`. Cloned rules alone were removed after merge; repo SHAs saved.
- Actions was checked disabled during this readiness session. No workflows/global
  config/hooks were changed. No provider/API inference spending occurred in readiness.
  Prior full run actual key delta remains $0.014957188; prior smoke $0.003375022.

### Remaining gates and blockers

The pause is user-directed, not an external technical blocker. Semgrep approval was
received and used; do not keep listing approval as pending. Pro and p/yaml availability
are scan coverage limitations. No additional skill was installed in this session.

Complete the nine RED resume tests and immutable run/corpus/image compatibility;
qualify legacy read/upgrade/recovery paths; enforce safe IDs before filesystem use;
finish backup/restore, corruption/disk failure handling, private permissions, bounded
trace reads and privacy-safe diagnostic export. Review finite usage/cost edge cases,
request outcome accounting, unknown-cost reconciliation and corpus comparison groups.
Finish resource regression (including descendants, inode pressure, cancellation,
SIGTERM, SIGKILL/resume) and all 12 current corpus positive/negative controls. Finish
UI empty/error/loading/zoom/deep-link/readability and large matrix checks. Run current
bounded real OpenRouter stream/nonstream/tool/usage tests within prior spending scope
and reconcile actual charges. Complete all applicable invoked skills, final static/
differential review and audits, fresh wheel install, upgrade and packaged-byte checks,
then publish only after every gate passes. No new release is qualified now.

The 26 invoked skills and actual/pending applications are in `docs/SKILL_USE.md`.
Correct that table from evidence: harness-writing was inspected and has no owned
C/C++/Rust entry point here; web-design and React rule review now occurred; Semgrep
approval/run occurred; other pending workflows remain pending. Do not convert an
installed skill or a worker's claim into completed qualification.

### Shutdown state (verified)

All four children (`corpus`, `dashboard`, `corpus_readiness`, `dashboard_readiness`)
were already terminal and were explicitly interrupted again. No active child remains.
Stopped test parent PID 11641 (session 39816, exit 143) and signalled its exact CLI
child PID 13779. Parent was briefly stopped first to prevent another test from starting.
Dashboard PID 19017/session 15965 shut down (exit 143); port 8765 had no listener.
No project provider, scan, build or test process remains. Scanner session 69635 had
already finished before stop. Other short sessions had completed.

After CLI exit, container and volume inventories were verified **empty**. Cleanup
was restricted to names derived from this test run's persisted trial IDs. Dedicated
Podman VM `abl-benchmark` was stopped and machine inventory reports Running=false.
Holding sleep PID 96124/session 81334 terminated (exit 143). No unrelated process
or other chat's resources were targeted.

Usage checker functions cell 175 was terminated after safe shutdown; last reading
was **71% used** at 20:43:41 UTC. It is session-local and no longer runs. Goal tool
returned **paused** at 20:43:48 UTC, tokensUsed 579201, no token budget. Do not
create a replacement goal or restart monitoring/work until Ethan resumes.

### Exact resume steps — only after a new instruction from Ethan

1. Read this section, `CONSTRAINTS.md`, `READINESS.md`, and inspect the dirty diff.
   Start a fresh supported-tool usage checker at the instructed cadence and stop
   at account exhaustion; do not use paid credits/reset/account switching implicitly.
2. Use this checkout and branch. Preserve all existing edits and historical evidence.
   Fresh/frozen environment command:
   `UV_PROJECT_ENVIRONMENT=.abl/readiness-env uv sync --frozen --python 3.12`
3. Inspect and repair `tests/test_resume_contract.py` against real requirements;
   run `.abl/readiness-env/bin/python -m pytest tests/test_resume_contract.py -q`.
   Full small/local suite: `.abl/readiness-env/bin/python -m pytest -q`.
4. Start the existing dedicated VM only when container work resumes:
   `podman machine start abl-benchmark`. Confirm the image is present with
   `.abl/readiness-env/bin/abl doctor`. Do not install helpers or change rootful/global
   settings just because the runtime startup prints optional suggestions.
5. Resource regression uses a NEW root, preserving interrupted evidence:
   `.abl/readiness-env/bin/python tests/resource_e2e.py --root .abl/readiness-resources-3 --cli .abl/readiness-env/bin/abl`
   Run current all-corpus positive/negative acceptance afterward; do not reuse old
   successful v1.0.1 claims to qualify revised contracts.
6. `npm run build --prefix dashboard`; start
   `.abl/readiness-env/bin/abl dashboard --root .abl/hardening-regression-v2`, then
   `npm run test:e2e --prefix dashboard`. This historical root is UI fixture evidence;
   use fresh data for new engine qualification. Stop the server when done.
7. Complete open gates above. Reuse the approved Semgrep rulesets and installed
   `../.agents/skills/semgrep/scripts/run-scans.sh`; keep metrics off and inspect raw
   error arrays as well as exit codes. Preserve initial scan evidence before rerunning.
8. Only after current gates pass: final diff/security/skill audit, package/upgrade/
   download checks, then release if still authorized. Recheck Actions disabled.

### Exact dirty files at pause

Tracked modifications (plus this HANDOFF update):
```text
.gitignore
abl/api.py
abl/engine.py
abl/isolation.py
abl/models.py
abl/providers.py
abl/store.py
corpus/feature-order-filter/task.yaml
corpus/multistep-document-index/task.yaml
corpus/multistep-ledger/task.yaml
corpus/multistep-ledger/verifier/check.py
corpus/navigation-config/task.yaml
corpus/navigation-config/verifier/check.py
dashboard/e2e.spec.ts
dashboard/package-lock.json
dashboard/package.json
dashboard/src/main.tsx
dashboard/src/style.css
pyproject.toml
uv.lock
HANDOFF.md
```
Untracked files retained:
```text
AGENTS.md
CONSTRAINTS.md
READINESS.md
corpus/navigation-config/verifier/contract.py
docs/CORPUS_QUALIFICATION.md
docs/SECURITY_REVIEW.md
docs/SKILL_USE.md
docs/UI_QUALIFICATION.md
evidence/readiness/history-performance-1.json
evidence/readiness/history-performance-2.json
evidence/readiness/semgrep-initial.json
evidence/readiness/semgrep-initial.sarif
tests/history_performance.py
tests/test_api_history.py
tests/test_corpus_contracts.py
tests/test_finalization.py
tests/test_provider_boundary.py
tests/test_resume_contract.py
tests/workspace_e2e.py
```
Ignored local environments, raw stores, scan output, generated static bundle and
browser screenshots are also retained. No unfinished work was cleaned away.

## Latest: full live corpus run complete
Evidence merged in PR #4: https://github.com/Ethant35/agent-benchmark-lab/pull/4 . Usage checker closed at 43% used (57% remaining). In-memory credential binding cleared; VM and holding process stopped. Working branch main.
2026-10-22: Full twelve-task run requested by Ethan, installed v1.0.1 and exact DeepSeek V4.1 Flash 1017 alias. Raw outcomes: 8 PASS, 3 FAIL, 1 TIMEOUT. One provider-executed attempt per task; four initial zero-request budget blocks were preserved and those untouched tasks executed once separately after charge inspection. Actual key-usage increase $0.014957188; 64 completed response/generation records reconcile to $0.014526328, with $0.000430860 additional key charge consistent with the interrupted request but not individually attributable. Same-key concurrent use would affect this delta. Prior smoke-test costs excluded.
Evidence and failure analysis: evidence/full-deepseek-1017/REPORT.md. Raw data: .abl/full-deepseek-1017. Effective task deadline is 30 seconds despite a 120-second config maximum. The score is qualified by underspecified output schemas and one strict-keyword false negative. No repairs/retries were performed. All resources cleaned and VM stopped. No workers or GitHub Actions. Earlier active-run and smoke-only notes below are historical.

## Latest: authorized live smoke validation complete
Evidence merged in PR #3: https://github.com/Ethant35/agent-benchmark-lab/pull/3 . Usage checker closed after final reading of 39% used (61% remaining). The in-memory credential binding was cleared. No live test process remains.
2026-10-22: Installed v1.0.1 passed BL-19–22 using the user-selected deepseek/deepseek-v4.1-flash-1017 alias on OpenRouter. Streaming and nonstreaming normal trials PASS; intentional zero-tool trial FAIL/step_limit as expected. All twelve response charges reconcile with generation metadata and key-usage delta: $0.003375022 total. Evidence: evidence/live-deepseek-1017/. Raw local root: .abl/live-deepseek-1017. No implementation change or extra inference retries. This is one task and one model, not full-corpus performance or all-provider validation.
Credential retained only in the session's process memory/environment, absent from saved evidence; no key/account settings changed. VM stopped after containers/volumes were verified empty. No workers or GitHub Actions. Historical release and blocked records below remain for provenance; their missing-credential statements no longer describe the tested OpenRouter paths. Current README and ACCEPTANCE describe the bounded live result.

## Current result: v1.0.1 published and verified
The bounded be-ambitious follow-up is complete. Release: https://github.com/Ethant35/agent-benchmark-lab/releases/tag/v1.0.1 ; merged PR: https://github.com/Ethant35/agent-benchmark-lab/pull/2 ; immutable release commit: 1f8753cdadec9054a741620443a1748f74e9faa4. Current branch: main. This documentation-only handoff follows the release commit.

Real v1.0.0 output-limit and archive-limit defects were reproduced, then fixed. Fourteen adversarial cases PASS; BL-01–18 regression PASS; three browser tests PASS. Clean wheel installation completes a real container trial. All 72 packaged implementation/task/static files match the checked sources. Published assets were downloaded and match both local bytes and published SHA-256 checksums. Author fields are Ethan; required dependency notices remain. The v1.0.0 release notes now carry a correction and upgrade link. See ACCEPTANCE.md and evidence/hardening/.

BL-19–22 remain BLOCKED_EXTERNAL. Live model integration is unverified, no provider responses were fabricated, and the current limits do not impose a container-volume disk quota. No workers were spawned for this follow-up; the earlier completed children are interrupted.

Cleanup verified: no trial containers or volumes remained before shutdown; Podman VM abl-benchmark is stopped; dashboard PID 61991 and holding sleep PID 50492 are terminated; port 8765 has no listener. Actions remains disabled and workflow-run count is zero. No config.toml edits. Usage checker ran every 45 seconds and is closed; final direct supported-tool observation was 34% used (66% remaining). A new work session must start its own checker and stop at 100%.

Retained local roots: .abl/resource-before, .abl/resource-final, .abl/hardening-regression-v2, .abl/patch-install, .abl/patch-smoke, .abl/patch-download. Release assets remain in dist/. To inspect results, start the existing VM only if new execution is needed, and serve `.abl/patch-install/bin/abl dashboard --root .abl/hardening-regression-v2`. Do not relabel reference outcomes as model scores or live-provider gates as passing.

## Historical v1.0.0 handoff and follow-up milestones
The sections below are historical; the current state above supersedes their pending actions.

## Completed release
Goal: COMPLETE for the explicitly permitted credential-free v1.0.0 framework release.
Repository: https://github.com/Ethant35/agent-benchmark-lab
Release: https://github.com/Ethant35/agent-benchmark-lab/releases/tag/v1.0.0
Release commit: 3a66b183aba2cf55fe7f747a69b490c59aee74b0
Merged PR: https://github.com/Ethant35/agent-benchmark-lab/pull/1
Local path: /Users/ethantarnarider/Documents/ChatGPT/Open source/agent-benchmark-lab
Current branch: main. A documentation-only handoff commit follows the immutable release commit; the v1.0.0 tag is unchanged.

## Verified result
BL-01–18 PASS. Real installed-wheel CLI/container acceptance, fresh clone installation, three Playwright browser tests, final twelve-task corpus (12/12 PASS), twelve unsolved-fixture controls (12/12 correctly FAIL), persisted exports, denominator checks, timeout/cancellation/resume and isolation checks passed. ACCEPTANCE.md and evidence/ contain exact commands, outcomes and source records.

The wheel, source distribution and SHA256SUMS.txt are published. Downloaded release assets match both the published checksums and local build bytes. Wheel code/task bytes match verified sources. Author metadata is Ethan; bundled dependency copyright/license notices are preserved.

BL-19–22 remain BLOCKED_EXTERNAL: no authorized OpenRouter credential was available. **Live model integration unverified.** No provider requests or fake provider responses were used. OpenRouter/compatible adapters are implemented, but live tool/streaming/usage behavior and nonzero provider-cost accounting await those real tests. Docker compatibility is implemented; local execution used Podman only.

## Isolation and cleanup
Podman 6.1.4 is installed. Dedicated `abl-benchmark` VM: 2 CPUs, 2 GiB RAM, 12 GiB virtual disk. VM and dashboard server are stopped; port 8765 is clear. All benchmark containers and volumes were removed, all Luna workers were interrupted on completion, and the VM holding process was terminated. Source, fixtures, SQLite results, opaque archives and traces are retained.

The supported account usage checker ran every 45 seconds during work without occupying a Luna slot. Last observed usage before final cleanup: 20% used (80% remaining). No exhaustion occurred. This was a session-scoped tool task, not a durable scheduled automation; it is closed at chat completion. Future work must start its own checker and stop at 100% used, without buying credits or switching accounts.

GitHub Actions remains disabled at repository level; zero workflow runs were verified after publishing. No workflows or ~/.codex/config.toml edits were made. Parent repository and other project checkouts were not modified.

## Exact next-session commands

```sh
cd '/Users/ethantarnarider/Documents/ChatGPT/Open source/agent-benchmark-lab'
git status
gh release view v1.0.0 --repo Ethant35/agent-benchmark-lab
podman machine start abl-benchmark
uv sync --frozen
npm ci --prefix dashboard
npm run build --prefix dashboard
uv run abl doctor
uv run abl dashboard --root .abl/release-acceptance
# Open http://127.0.0.1:8765
```

Acceptance roots: `.abl/release-acceptance` (29 records, including one real credential-blocked probe), `.abl/final-corpus` (12 PASS), `.abl/unsolved-suite` (12 expected FAIL). Clean Python 3.12 wheel environment: `.abl/clean-install`; fresh source clone: `.abl/clean-source`. Release files: dist/; re-downloaded verification copies: `.abl/download-verification`.

For live validation, obtain an authorized OpenRouter key, two exact tool-capable model configurations and a provider-side capped budget. Use examples/openrouter.yaml and tests/live_e2e.py. Do not relabel the existing BLOCKED_EXTERNAL scenarios or present reference outcomes as model scores. No additional implementation is required to finish the credential-free release.

## Active bounded follow-up: output/artifact isolation (2026-10-22)
Goal ACTIVE under be-ambitious: reproduce and repair host collector limits with real adversarial container E2E, then rerun local acceptance and publish a patch only if gates pass. The previous DONE result does not establish hostile-output correctness.
Branch: codex/bounded-output-evidence. Primary engineer owns code and tests; no workers active. Supported usage checker runs every 45 seconds in functions cell 68. Startup usage 23%, latest 24% used. Stop all project work at 100% used.
Code inspection: snapshot writes full tar before enforcing 64,000,000-byte cap; command checks 2,000,000-byte cap only while subprocess still runs and silently retains only 200,000 bytes per stream. Existing acceptance has no oversized-output cases. These are hypotheses pending real reproduction, not yet runtime-proven.
Next: start existing Podman VM, create disposable source-copy test corpus through public CLI, collect before/after evidence, fix bounded pipes and terminal metrics. No live credentials available; BL-19–22 remain BLOCKED_EXTERNAL. GitHub Actions verified disabled before work.

## Follow-up reproduction and repair milestone
Real v1.0.0 container runs confirmed: 2/3 fast 2.2 MB outputs bypassed the cap; dual-stream 2.4 MB output bypassed it; sustained output failed with zero failed-tool count and no tool result; 70,003,712-byte archive remained despite 64 MB limit. Raw compact evidence: `.abl/resource-before/results.json`, copied to `evidence/hardening/before.json`.
Primary implementation now drains nonblocking stdout/stderr pipes through EOF with bounded retained prefixes, aborts at cap+1 observed byte, limits archive writes before publishing, records failure categories/byte provenance, and removes partial files. Initial eight-case after-run passed. Comprehensive real E2E running at `.abl/resource-comprehensive`; includes a paced real Podman tar stream for cancellation/timeout/SIGTERM/SIGKILL-resume checks. No mocked model responses. VM held by session 33743. Current usage checker cell 68 remains active; latest 27% used. No new release yet.

## Follow-up gates
Fourteen real adversarial cases now PASS in `.abl/resource-final/results.json` (saved as evidence/hardening/after.json). Fast exits, both streams, stderr-only, exact-limit, explicit truncation, oversized artifacts, normal output, archive timeout/cancel/SIGTERM, and SIGKILL-resume are verified. Partial archives are removed and completed archive hashes independently checked; all trial resources cleaned.
Existing BL-01–18 regression is running at `.abl/hardening-regression-v2`. UI now labels truncated/incomplete verifier evidence without adding controls. Version prepared as 1.0.1, not published. Direct implementation retained by lead; no workers spawned. Next: finish regression and browser checks, package clean install, PR/merge/tag/release with Actions disabled, verify downloads, then stop VM/checker and save final handoff.

## Patch acceptance complete; release pending
BL-01–18 regression PASS, including three browser tests (2.0 seconds) against the clean installed-wheel dashboard. All 14 adversarial cases PASS. Clean wheel 1.0.1 passed doctor, validate and actual rounding trial aabac7b48a1041688d794ef4b1077a36. The repeated agent preflight is BLOCKED_EXTERNAL without provider requests. Package equality verified for 72 implementation/task/static files, Author Ethan and preserved third-party notices. Acceptance method, primary sources, limits and raw compact evidence are saved under ACCEPTANCE.md and evidence/hardening/. Actions disabled; zero runs. Next: commit/PR/merge/tag/release and downloaded asset verification, then stop VM/dashboard/checker.

## Authorized live-provider validation active (2026-10-22)
Ethan supplied an OpenRouter credential and requested economical testing with DeepSeek V4.1 Flash 1017. Exact model ID verified from the live model catalog: deepseek/deepseek-v4.1-flash-1017. Three trials use streaming/nonstreaming and an intentional zero-tool restriction; $0.05 local reserve per trial, $0.15 total across the initial suite. Conservative prices cover listed endpoints: $0.30/M input, $1.20/M output. Key stays in process memory/environment, outside configs and repository files. Existing key cap was inspected, not changed.
Installed v1.0.1 wheel is under test. Configs and raw results: .abl/live-deepseek-1017. No workers or GitHub Actions. Account checker is functions cell 114 every 45 seconds; stop at 100%. Podman VM started with holding session 28050. Next: inspect real responses and verifier outcomes, reconcile usage/cost, save sanitized evidence, stop runtime and checker.

## Full live corpus run active (2026-10-22)
Ethan explicitly authorized all twelve tasks with the same key and DeepSeek V4.1 Flash 1017, keeping spend low. Installed v1.0.1, one trial per task, streaming/low reasoning, 8 requests/task, 2,048 output tokens/request, 16 tool steps/task, 120 seconds/task. The $0.20 local reserve applies across the whole run, not independently to twelve tasks. Conservative prices rechecked: $0.30/M input and $1.20/M output. No automatic inference retries planned. Root: .abl/full-deepseek-1017. Key only in process memory/environment. Usage checker functions cell 134 runs every 45 seconds; VM holding session 83203. Next: wait for all outcomes, reconcile every generation charge and actual key-usage delta, save evidence, and shut down runtime/checker. No workers or Actions.
