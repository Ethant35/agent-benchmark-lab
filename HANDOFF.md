# Agent Benchmark Lab handoff
Author: Ethan

## Latest: authorized live smoke validation complete
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
