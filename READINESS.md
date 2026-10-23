# Local-user readiness audit
Author: Ethan
Updated: 2026-10-22

## v1.2.0 usability candidate

Candidate acceptance is complete: 78 local tests, 15 packaged-dashboard browser checks,
12 installed-wheel reference passes, free-first/interruption/recovery journey,
upgrade/rollback, package byte checks and dependency audits. Publication and downloaded
release verification are pending. See [USABILITY_ACCEPTANCE.md](docs/USABILITY_ACCEPTANCE.md)
and evidence/usability/. No new provider requests or charges; historical records remain
unchanged. The CLI adds optional guidance while the dashboard remains read-only.

## v1.1.0 qualification (preserved)

Status: **QUALIFIED AND RELEASED as v1.1.0 for the documented local target.** Current
local, container, browser, package, upgrade and bounded live integration gates have
evidence. This is not a guarantee that a model completes the 30-second benchmark.
The separate integration fixture permits 120 seconds; its inputs/verifier and all
implementation bytes match the qualified wheel. Historical results remain unchanged.
See CONSTRAINTS.md and evidence/readiness/live-integration/.

| Gate | Current evidence | Status / limit |
|---|---|---|
| Support/security | docs/OPERATIONS.md, SECURITY.md, security/differential reviews and ADR-001 | Local macOS Apple Silicon/Python 3.12/Podman only; Docker unqualified |
| Twelve contracts | Current CLI suite: all 12 references PASS; all 12 unsolved controls FAIL; property/contract tests | PASS; four contracts versioned, old scores not rescored |
| Resource isolation | resource-results.json: 14 expected outcomes; workspace-results.json: 128 MiB / 16,384 inode exhaustion and independent verifier | PASS on Podman; runtime/kernel escape immunity not claimed |
| Provider/cost | Actual streaming PASS, nonstreaming PASS, zero-tool FAIL as expected; all 11 charges and persisted usage reconcile to $0.001403188 | PASS on separately versioned 120-second integration contract; three original 30-second timeouts retained |
| Resume/recovery | ID/path/manifest/lock tests, real kill/resume cases, immutable image, corruption tests | PASS for new manifests; legacy resume refused safely |
| API/reporting | Parameterized pagination, complete denominators, typed envelopes, bounded trace reads and known subtotal tests | PASS; legacy unpaged endpoints retained for compatibility |
| Dashboard | Eight packaged-API browser checks, axe clear, keyboard/mobile/error/empty/loading/URL/filter/evidence tests | PASS within documented automated checks; no field metrics or OS zoom certification |
| Privacy/observability | Owner-only root and DB/traces; safe diagnostics; private retention/export guidance | PASS for local threat boundary; raw exports remain sensitive |
| Dependencies/install | Frozen Python 3.12.14 dev install; pip-audit/npm audit zero; clean wheel trial PASS | PASS for dated snapshots; unconstrained future dependency resolution not qualified |
| Upgrade/backup | Real v1.0.1 trial export unchanged after upgrade and backup/restore; 75 packaged files match source; Author Ethan | PASS; candidate package local only |
| Static/differential | Final Semgrep 31 triaged indicators, reviewed diff, fixed legacy-root privacy defect | Partial scan coverage: 15 third-party rule errors, p/yaml unavailable, Community only |
| Test floor | 61 pytest passes, eight browser passes; floor checker flags manually reviewed | See docs/FLOOR_REVIEW.md; automated checker itself still exits 1 |
| Performance | 10,000-row controlled test: JSON 127.95 MB → 1.26 MB, Python allocation 410.86 MB → 15.91 MB | Synthetic local measurement; median query/encoding 1.047 s → 0.391 s |
| Documentation | Operations, recovery/rollback, support, API, ADR and changelog | Current; see skill ledger for applicable work and limits |
| Shipping | PR #5 merged; v1.1.0 published; downloads match checksums/local bytes; downloaded wheel task PASS | PASS; release-provenance.json records immutable commit and hashes |

## Commands and evidence

`uv run --frozen python -m pytest -q`: 61 passes, one dependency deprecation warning
for Starlette's httpx TestClient path. `npm run build --prefix dashboard`: success.
`ABL_BASE_URL=http://127.0.0.1:8767 npm run test:e2e --prefix dashboard`: eight passes.
Real CLI, negative corpus, resource, workspace, dependency, live cost and package records
are retained under evidence/readiness/. No mock response is labelled a live model result.
The local CLI suite reports live scenarios BLOCKED_EXTERNAL because it does not call a
provider. Separate live integration evidence proves BL-19–22 for the selected OpenRouter
model, with stronger checks requiring both configurations to pass the verifier.

The earlier full twelve-task model run remains 8 PASS / 3 FAIL / 1 TIMEOUT, costing
$0.014957188. Readiness spending is separate and fully reconciled: $0.001900464 for the three
30-second timeout attempts plus $0.001403188 for the final integration suite, totaling
**$0.003303652**. No automatic retries. The final wrapper copies the installed package
and changes only the rounding task's version and deadline to 120 seconds. It verifies
that the original installation is unchanged. Streaming took 27.1 seconds, nonstreaming
40.5 seconds, and the zero-tool control failed in 4.9 seconds. This closes protocol/tool/
usage integration, not a new full-corpus score or a passing 30-second nonstreaming result.
All benchmark contracts, original failures and historical model scores remain intact.

## API contract

`GET /api/trials/page?limit=100&offset=0` accepts run_id, provider, model and task_id
filters and returns `{items,total,limit,offset}`. Limits are 1..200; offset is nonnegative.
Newest records come first; compact rows omit evidence bodies. `/api/overview` uses the
same filters. Summary metrics cover all matching terminal trials; chart_trials contains
at most the newest 2,000, with chart_sampled/chart_total disclosure. Facets span the store.
Legacy trial, summary, detail and export routes remain. Unknown measurements stay null.

Compound reads use one SQLite snapshot. HTTP access is read-only, loopback Host only,
foreign Origin rejected, and no-store/security headers applied. Full trace previews are
bounded to 2 MB total / 1 MB per line and signal truncation; symlinks are rejected. Corpus
manifest hashes separate changed-contract comparison groups from legacy unknown identity.

Release: https://github.com/Ethant35/agent-benchmark-lab/releases/tag/v1.1.0 .
Publication verification is recorded in evidence/readiness/release-provenance.json
after upload; the release tag and uploaded assets are unchanged.
