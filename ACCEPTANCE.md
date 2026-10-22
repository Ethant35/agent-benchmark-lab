# Local acceptance: v1.0.0
Author: Ethan

**Deterministic framework acceptance: PASS. Live model integration unverified.** BL-01–18 pass. BL-19–22 are **BLOCKED_EXTERNAL**, because no authorized OpenRouter credential was available. No model responses, provider charges or token measurements were fabricated.

GitHub Actions is intentionally omitted per Ethan. Repository Actions permissions are disabled, and the GitHub API reported zero workflow runs before release. Local checks replace the specification's CI gate.

## Environment and reproducible commands

2026-10-22, macOS arm64. Python 3.13.17 development environment and clean Python 3.12.14 wheel/source installations. Node 22.13.1. Podman 6.1.4 in a dedicated `abl-benchmark` VM (2 CPUs, 2 GiB memory, 12 GiB disk). Container Python 3.12.15; image ID `7efd45553a98be3d940b73600550669831c0be34f30c521159e7030a91fcdee6`. The actual image, task and fixture identifiers are recorded per trial.

```sh
uv sync --frozen
npm ci --prefix dashboard
npm run build --prefix dashboard
podman pull docker.io/library/python:3.12-slim
uv build
uv venv .abl/clean-install
uv pip install --python .abl/clean-install/bin/python dist/agent_benchmark_lab-1.0.0-py3-none-any.whl
.venv/bin/python tests/e2e.py --cli .abl/clean-install/bin/abl --root .abl/release-acceptance
.abl/clean-install/bin/abl dashboard --root .abl/release-acceptance
# Separate terminal:
cd dashboard
npm run test:e2e
```

The CLI/container harness passed using the installed wheel, not imports into application internals. A fresh local Git clone of implementation commit `04e1600` independently passed `uv sync --frozen`, `npm ci`, production dashboard build, `doctor`, `init`, and `validate`. The wheel contains all twelve task definitions and built dashboard assets. Its saved Author metadata and HTML/PNG author fields were verified as Ethan.

## E2E matrix

| Scenario | Result | Evidence |
|---|---|---|
| BL-01 Clean installation | PASS | Fresh clone and clean Python 3.12 wheel install; doctor/init succeed |
| BL-02 Task validation | PASS | Public CLI validates twelve YAML tasks, six categories |
| BL-03 Reference success | PASS | Rounding repair passes real container verifier |
| BL-04 Reference failure | PASS | Original broken rounding fixture rejected; stderr preserved |
| BL-05 Fresh environments | PASS | Three unique trial IDs, containers and artifact directories; same fixture hash |
| BL-06 All categories | PASS | Two task-specific verifier successes per category |
| BL-07 Timeout | PASS | Nonterminating shell stopped; TIMEOUT and cleanup persisted |
| BL-08 Tool failure | PASS | Actual exit 7 recorded in trace and metrics; subsequent repair passes |
| BL-09 Cancellation | PASS | Public cancel command terminates active trial and cleans resources |
| BL-10 Host isolation | PASS | Host-only sentinel unreadable; inherited test secret absent; network denied; inspect confirms limits, unprivileged user and volume-only mounts |
| BL-11 Hidden artifact isolation | PASS | Agent's actual file-read attempt cannot access `/verifier/check.py` |
| BL-12 Resume | PASS | SIGTERM interruption then resume preserves completed IDs; unfinished slot retried in fresh trial |
| BL-13 JSON export | PASS | Reopened JSON equals SQLite documents with required fields |
| BL-14 CSV export | PASS | Row counts, typed values, nested sources and unavailable values match SQLite |
| BL-15 Aggregation | PASS | Independent arithmetic matches all-attempt rates, timing, tools and cost; unknown tokens remain null |
| BL-16 Dashboard | PASS | Actual browser displays persisted API metrics and verifier evidence; downloads work |
| BL-17 Filters | PASS | Task/model/provider/run filtering matches persisted records; cross-run filters exclude other records |
| BL-18 Full suite/report | PASS | Twelve-task suite succeeds from clean state; comparison/report generated |
| BL-19 Live execution | BLOCKED_EXTERNAL | Missing authorized OpenRouter credential |
| BL-20 Live failure attribution | BLOCKED_EXTERNAL | Missing authorized OpenRouter credential |
| BL-21 Two live configurations | BLOCKED_EXTERNAL | Missing authorized OpenRouter credential |
| BL-22 Provider usage accounting | BLOCKED_EXTERNAL | No actual provider responses to audit |

Playwright: **3 passed (2.3s)**. Desktop and mobile screenshots were inspected. The primary acceptance dataset has 28 real reference attempts; an additional genuine missing-credential agent attempt makes 29 records for cross-provider/model filter validation. That attempt has no provider response records and is explicitly BLOCKED_EXTERNAL. It is not a live model benchmark.

A final complete corpus run after adding strict JSON type checks passed **12/12** (`dfb66c480969433183a27e11ca37d3a2`). A separate negative-control suite rejected **all 12 original unsolved fixtures**. Final isolation cleanup found no remaining containers or volumes for acceptance trial IDs.

## Saved evidence

- [Machine-readable scenarios and exact CLI transcripts](evidence/cli-container-acceptance.json)
- [Final complete corpus results](evidence/final-corpus.json)
- [Unsolved-fixture controls](evidence/unsolved-controls.json)
- [SQLite-matched JSON export](evidence/trials.json) and [CSV export](evidence/trials.csv)
- [Comparison](evidence/comparison.json) and [HTML report](evidence/report.html)
- [Desktop screenshot](evidence/dashboard.png) and [mobile screenshot](evidence/dashboard-mobile.png)
- [Live preflight](evidence/live-preflight.json) and [actual credential-blocked trial](evidence/credential-blocked-trial.json)

Original traces and opaque workspace archives remain under the local `.abl/` acceptance roots; release evidence is derived from those actual executions.

## Failures repaired during acceptance

The first VM lifecycle interruption left stale sockets and an incomplete image layer. The runtime was restarted and the image repulled; the framework had correctly refused unsafe host execution. Acceptance also found and repaired an incorrect order-filter reference action, a nested-string slugify verifier error, overstrict navigation explanation matching, an omitted wheel dashboard, a report argument mismatch, and browser port/format assertions. None of those failing attempts were relabeled as passing. Fresh reruns supplied the passing evidence above.

## Live reproduction and limits

`tests/live_e2e.py --config-a model-a.yaml --config-b model-b.yaml --root .abl/live-new --cli .venv/bin/abl` runs the four live gates with two explicitly supplied configurations, one small coding task and at most $0.25 configured reserve per run. The third restrictive run uses zero tool steps. Use a provider-side capped key for a hard billing limit; client reserves are estimates. No automatic live tests or provider spending occur on installation, PRs or releases.

Podman was exercised locally; Docker command compatibility is implemented but not separately runtime-tested here. OpenRouter and generic compatible HTTP/SSE adapters remain unverified against live providers. Nonzero provider spend/cache accounting cannot be empirically validated without those live gates. These limitations qualify this as a credential-free framework release, not a fully validated live-provider benchmark product.

## v1.0.1 bounded-output correction (2026-10-22)

This patch revisits the v1.0.0 acceptance claim. That release passed its recorded scenarios, but those scenarios did not establish correct behavior for hostile output volume. **Upgrade from v1.0.0 for the corrected host collector limits.** Author: Ethan.

### Method and rewritten task

Field: execution-boundary reliability and adversarial acceptance testing. Using the explicitly requested be-ambitious workflow:

1. A specialist would reproduce a boundary failure before changing it, then inspect both failure evidence and cleanup after interruption.
2. The raw inputs were `abl/isolation.py`, `abl/engine.py`, actual pipe bytes, opaque tar files, process/container inventories, trace JSONL, and SQLite trial documents.
3. The methods were public CLI/container adversarial workloads, nonblocking pipe collection with `selectors.DefaultSelector`, independent archive-size/hash observations, process signals, and Playwright against the installed dashboard.
4. External evidence was an observable failure on v1.0.0 followed by enforced byte limits, explicit incomplete/truncated evidence, accurate failed-tool counts, no abandoned trial resources, and passing existing acceptance checks. Live-provider behavior could not be established without credentials.

The executed rewrite was:

```text
Harden Agent Benchmark Lab's existing execution boundary. First reproduce
host-side output and artifact limit defects with real container tasks. Then
enforce the existing limits while bytes are read, including fast exits,
simultaneous stdout/stderr, cancellation, and timeout. Preserve bounded,
explicitly labeled evidence and accurate failure metrics. Remove partial
archives and clean every trial resource.

Use public CLI/container E2E, actual process/file observations, SQLite, and
official Python/Podman documentation. Do not mock AI responses or add features.
Pass the adversarial cases and existing local acceptance before publishing a
patch. Keep live-provider checks BLOCKED_EXTERNAL, GitHub Actions disabled,
a current HANDOFF.md, and the account-usage stop checker active.
```

Primary sources informed the design: Python documents that `communicate()` buffers output in memory and warns against unlimited output ([subprocess](https://docs.python.org/3.12/library/subprocess.html)); Unix pipe readiness is supported by [selectors](https://docs.python.org/3.12/library/selectors.html). Podman documents tar output to stdout with `cp ... -`, including stopped containers ([podman cp](https://docs.podman.io/en/latest/markdown/podman-cp.1.html)). The implementation limits bytes during collection and never extracts the untrusted archive on the host.

### Reproduced defects and corrected outcomes

[Before evidence](evidence/hardening/before.json) records real v1.0.0 runs: two of three fast 2.2 MB stdout trials bypassed the 2 MB limit; simultaneous 2.4 MB output bypassed it; sustained excessive output lost the failed-tool count and result; a 70,003,712-byte archive remained despite the 64,000,000-byte cap. A 400,001-byte output retained 200,000 bytes without labeling truncation.

[After evidence](evidence/hardening/after.json) records **14 passing adversarial cases**. Expected ERROR, TIMEOUT, CANCELLED, and INTERRUPTED trial statuses are successful test outcomes where the workload intentionally violates a boundary.

| Cases | Verified result |
|---|---|
| Explicit truncation; exact 2 MB boundary; normal dual stream | Exact observed byte counts; bounded retained prefixes; completion/truncation flags; normal trials PASS |
| Fast excessive output, three repetitions | Every attempt stops with `output_limit`; one failed tool and bounded evidence persisted |
| Sustained output; simultaneous streams; stderr-only flood | Combined limit enforced through pipe EOF, including buffered bytes after process exit |
| 70 MB artifact | Host writes never exceed 64,000,000 bytes; no completed or partial archive remains; `artifact_limit` persisted |
| Archive timeout and public cancellation | Correct terminal status, partial archive removal, resource cleanup |
| SIGTERM during archive transfer | Interrupted outcome saved, partial removed, resources cleaned |
| SIGKILL then public resume | Resume removes abandoned partial, preserves interrupted history, and completes a fresh PASS trial |

The four archive-interruption cases use a transparent transport wrapper that paces bytes from the real Podman `cp`; all other commands execute the real runtime unchanged. It does not fabricate archive content or provider responses. Tests observe actual files and independently hash completed archives. Sampling file size alone cannot exclude a transient overshoot; the collector's capped writes establish that bound, with observed peaks as a separate check. Byte counts are source bytes; invalid UTF-8 replacement and JSON encoding can expand serialized text. Aborted output counts are lower bounds.

Reproduction commands, using fresh output roots:

```sh
uv sync --frozen
.venv/bin/python tests/resource_e2e.py --root .abl/resource-new --cli .venv/bin/abl
.venv/bin/python tests/e2e.py --root .abl/regression-new --cli .venv/bin/abl
npm run build --prefix dashboard
uv build
# Install the 1.0.1 wheel in a clean environment, then serve the regression root:
.abl/patch-install/bin/abl dashboard --root .abl/hardening-regression-v2
npm run test:e2e --prefix dashboard
```

The adversarial harness uses a disposable source/corpus copy through the public CLI so it can prepend actual hostile commands without modifying the release corpus. The original CLI/container regression passed against source; [regression evidence](evidence/hardening/regression.json) records BL-01–15 and BL-18. A separate clean Python 3.12 wheel install passed doctor, all twelve task schemas, and a real rounding trial (`aabac7b48a1041688d794ef4b1077a36`). [Package evidence](evidence/hardening/package.json) verifies all 72 packaged implementation/task/static files against source, Author `Ethan`, version 1.0.1, and preserved third-party notices. All three Playwright tests passed in 2.0 seconds against the installed-wheel dashboard and 29 persisted records, including the genuine credential-blocked attempt. Desktop and mobile screenshots were visually inspected and saved with Author Ethan in `evidence/hardening/`. This completes BL-16/17 for the patch.

These are host collection limits, not a per-volume disk quota: container workspace storage still consumes VM capacity. Host execution remains forbidden. Podman on macOS was exercised; Docker remains untested at runtime. BL-19–22 remain **BLOCKED_EXTERNAL: live model integration unverified**. The repeated missing-credential attempt made no provider request. No GitHub workflows were added; repository Actions remained disabled with zero workflow runs.
