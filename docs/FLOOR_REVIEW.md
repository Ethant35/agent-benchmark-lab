# Test-floor review
Author: Ethan
Date: 2026-10-22
Baseline: 381caf28ec2d73dc6e87d0956ff2afcde986cced

The installed constraint skill's reference floor-guard ran against the working diff.
It returned exit 1 with eleven flags. This is not reported as a clean automated pass.
The full flags are retained in evidence/readiness/floor-guard.txt.

Two `test-made-easier` flags refer to CSS `.skip-link` and `.skip-link:focus`. They
implement keyboard skip navigation, which the browser test exercises. They are not
skipped tests. No skip/only directive was introduced.

Nine `assertion-removed` flags are textual replacements in dashboard/e2e.spec.ts:
row counts now assert the first page's exact expected size rather than requiring every
stored record in the DOM. Filter assertions query the corresponding filtered compact
page and require the exact visible count. API tests independently check parameterized
filter correctness and complete totals. The first-detail assertion now uses the first
record in the same paginated order as the UI, instead of the legacy unpaged order.

The original tested behaviors remain: persisted metrics, run/provider/model filtering,
actual evidence, downloads, mobile overflow, and passing-record presence. New checks
require page-two navigation and reload for a controlled 250-row store, URL restoration,
complete summary versus sampled chart labels, a bounded 2,000-cell matrix, focus loops,
no axe violations, known-cost subtotals and evidence-specific retry. Eight browser tests
pass against the packaged API; controlled response fixtures are explicitly labelled.

Manual disposition: these flags describe interface-aware replacement assertions and
a CSS name collision, not a lowered floor. No test failure was skipped and no task
verifier was relaxed solely to obtain PASS. Four corpus contract corrections have
versioned reasoning and unchanged historical outcomes in CORPUS_QUALIFICATION.md.
No guard suppression or exception rule was installed. The separate live-provider gate subsequently passed as described below.

The final live integration wrapper is additive: default live_e2e.py retains the bundled
30-second behavior and its prior failures. The separate wrapper uses a new task version
with a 120-second latency allowance, leaves all inputs/prompt/verifier bytes unchanged,
and checks original-package hashes afterward. It tests provider/tool/usage integration,
not the deadline-bound benchmark score. Normal nonstreaming success is now explicitly
asserted too, along with artifacts, TTFT mode, no pending request and clean cleanup.
The old harness only asserted identity/comparison fields for that second configuration.
No existing assertion was removed. Final integration PASS does not relabel any timeout.
