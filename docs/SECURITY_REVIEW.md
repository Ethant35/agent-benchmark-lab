# Readiness security review
Author: Ethan

Status: bounded local review complete. Initial findings below are retained for provenance;
the final and release updates give their current dispositions and coverage limits.

## Boundaries and assets

The operator controls local configs, corpus, installed runtime and result directory.
Provider responses and candidate code are untrusted. Browser requests can come from
an unrelated website. Protect API credentials, host files, paid-request accounting,
independent verifier inputs, and recoverable result evidence.

Candidate code runs as UID 65534 with no network, no host workspace mounts, a read-only
root filesystem, dropped capabilities and per-container resource limits. The private
verifier can change UID for its child but does not share its input volume with the
agent. Neither model text nor a successful tool call establishes task success.

New workspace tmpfs is limited to 128 MiB and 16,384 inodes. A separate sleep-only
container keeps it mounted through agent stop, artifact capture and verification.
It uses container UID 0 for volume initialization, with all capabilities dropped,
no network and no candidate commands. This is not host root or a privileged container.
Rootless Podman mounts tmpfs with ownership outside the container mapping, so the
volume is created with mode 0777; trusted setup changes only extracted child modes.
The volume belongs to one trial and is removed during cleanup.

Failure to initialize the bounded volume fails the trial. There is no unbounded
disk fallback. Docker support for this path still needs real qualification.

## Initial Semgrep scan

The user approved the exact local run-all plan. Five workflow steps:
1. Detected Python/TypeScript/React/FastAPI and Community engine; Pro unavailable.
2. Selected six registry packs and three third-party repositories.
3. Received explicit approval in this chat on 2026-10-22.
4. Ran the installed `run-scans.sh` with metrics off, two scan processes, no upload,
   login, autofix or Actions. Nine process exits succeeded; none skipped/failed.
5. Merged SARIF, preserved full raw outputs and approved plan locally, copied initial
   evidence into `evidence/readiness`, and deleted only the cloned rules directory.

**Coverage is partial despite zero failed scan processes.** Raw records report
partial TSX parsing around a spaced self-closing JSX tag. The JSX was normalized;
a later scan must confirm parser coverage. Elttam also has twelve rule parse errors;
Apiiro has three. The full error records and repository revisions are retained in
`evidence/readiness/semgrep-initial.json`. `p/yaml` returned 404 during planning and
was not included in the approved plan. Community mode cannot prove cross-file data flow.
No oversized targets or covered-nothing scans were reported. The runner's
`partial:false` flag reflects exit handling and does not erase errors in raw JSON.

Thirty merged findings: twenty-four long-line readability indicators and six dynamic
execution indicators. The six execution sites are the engine's isolated tool wrapper,
the container `exec` path, and three independent verifier subprocess calls. Those
are intended execution boundaries, not evidence of malicious code. They remain
subject to actual isolation/UID/cleanup tests. Long lines warrant a readability
review; no suppression or ignore rule was added to hide these findings.

This initial scan precedes later provider and isolation changes. It is not proof
that the final source has been scanned. A final approved-plan rerun and differential
review remain release gates.

## Verified failure tests so far

- Real SQLite/API tests reject foreign Origin and unsafe page bounds, use parameterized
  filter values, omit evidence payloads from list pages, and close DB connections.
- Loopback HTTP fault injection rejects oversized JSON/SSE, incomplete SSE, malformed
  usage counts and non-finite prices. It preserves generation identity before timeout
  and records preflight refusals as zero requests, not unknown billed requests.
- Intent is saved before transmission. In-flight records carry unknown cost and their
  known prior subtotal. They are not silently retried or treated as zero-cost outcomes.
- A controlled disk-full event reproduction fails on baseline `381caf2` and passes
  after moving cleanup before artifact-event persistence. This control-flow test does
  not substitute for real storage/interrupt recovery qualification.

Still open: safe run IDs, immutable resume manifests, corruption/backup handling,
private result permissions, bounded trace reads, safe diagnostic export, final
dependency audit, full adversarial resource regression and current live-provider tests.

## Final local review update — 2026-10-22

This update supersedes the initial open-item list above. Source at the final scan includes
resume-ID/manifests, private legacy roots, recovery commands, typed API responses, provider
bounds/accounting and the evidence-specific UI retry. The final approved-plan run used
`static_analysis_semgrep_3`, Community engine, metrics off and the same six packs/three
repositories. Seven scans exited 0. Elttam and Apiiro exited 2 with partial outputs:
twelve and three rule parse errors respectively. The wrapper and merge completed; that
does not convert those partial scans into full coverage. No TSX target parse errors remain.
`p/yaml` was unavailable and excluded as disclosed. No Pro/cross-file analysis was available.

The merged 31 findings comprise 25 generic long-line indicators and six intentional
execution sites: engine tool wrapping (two), isolated runtime exec (one), and three
behavioral verifier subprocess calls. These are retained, not suppressed. Each runs
through the documented candidate/verifier boundary; real positive/negative isolation
and fourteen hostile-resource cases passed. Long expressions are a readability debt,
not an established injection exploit. A later refactor must retain tests and evidence.
No new confirmed high/critical security defect was found in this bounded review.
Full locations, raw errors and ruleset revisions remain in semgrep-final.json/SARIF.
Temporary rule clones were removed after merge; raw reports remain local.

The differential review found permissive legacy roots. A regression reproduced it,
then root restriction to 0700 passed without changing historical evidence. Safe run IDs,
no-follow locks, immutable corpus/image resume, corruption errors, checksum backup/restore,
trace limits, diagnostic allowlists and descendant cleanup have focused tests. The final
local suite has 61 passes. Both dependency audits reported zero vulnerabilities for their
resolved snapshots. See package-results.json for real fresh-install/upgrade/restore proof.

Live calls returned real tool data but three attempts reached the 30-second task deadline.
All eleven generation records reconcile to $0.001900464; no further paid attempts were
made. This is accounting/timeout evidence, not a passing normal live workflow. At that snapshot, streaming/nonstreaming success qualification remained open.
The release update below records its later resolution.

## Release qualification update

The final scan reran the same approved plan as static_analysis_semgrep_4 after adding
the integration harness. It has the same 31 findings and 15 rule errors; all raw outputs
and partial-coverage flags are retained. Application bytes did not change after the
reviewed wheel. The new harness changes only a copied task version/deadline and validates
that source code, prompt, fixture and verifier remain unchanged. Both actual live modes
passed, and a zero-tool run failed as expected. All eleven generation charges matched
response usage and account delta: $0.001403188. Earlier timeout charges remain separate.
This resolves the live integration blocker within the declared local support scope.
