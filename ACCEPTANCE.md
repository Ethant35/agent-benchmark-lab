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
