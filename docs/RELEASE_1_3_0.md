# Release 1.3.0 acceptance
Author: Ethan
Frozen: 2026-10-29, before candidate qualification.

## Contract and gates

Supported target: a local macOS Apple Silicon developer with Python3.12 and an
existing rootless Podman VM/image. No paid calls. No Actions. Tests run in background.

1. Build wheel and source archive from tracked merged runtime plus release metadata;
   install outside the checkout. CLI and dashboard work with PYTHONPATH/PYTHONHOME
   unset. Confirm imports come from that environment, not source.
2. Reuse grader-v2 calibration only after all task/reference/verifier bytes match its
   recorded hashes. Retain prior122 Python/22 browser checks for unchanged behavior.
   Keep harness correctness, grader correctness and comparison validity distinct.
3. One free installed journey: empty workspace, reference execution/progress, evidence,
   interruption/resume retaining all attempts, compatible matched comparison/export,
   backup/restore after recovery, and reopen the complete history.
4. Check incompatible comparisons and unknown costs with the existing boundary tests.
   Test the installed dark/light comparison UI and the real comparison download.
5. Confirm wheel/source/installed runtime and static bytes agree, archive rebuild
   agrees, metadata author is Ethan, dependencies match the qualified lock or receive
   a fresh audit, and no historical data or task versions changed.
6. Merge accepted release sources, publish checksum-protected assets, download them
   without credentials, install in another fresh external environment, and verify
   public CLI/dashboard/history and packaged task identities without source paths.
7. Save release/evidence/cleanup handoff and stop. No new study or model ranking.

Independent usability with an unfamiliar developer: pending; no such developer is
available in this session. Earlier Terra review is not a substitute for that study.
The release may pass technical acceptance with this limitation explicitly retained.
Docker, Windows, fresh-Mac setup and new live-provider qualification are not claimed.
Unchanged provider/isolation checks are reused; no adapter changes or paid retesting.

## Evidence

Candidate and public-install results will be recorded in evidence/release-1.3.0/.
Prior evidence: evidence/grader-v2-20261028/, evidence/terra-fixes-20261029/,
and evidence/readiness/. Frozen gates above are not relaxed to obtain a pass.

## Candidate outcome

Technical gates1–5 pass. The wheel imports from isolated site-packages without
PYTHONPATH; all122 tests pass with freshly resolved and audited dependencies. The
free installed journey passes. Full backup restores all3 attempts and manifests;
the reopened dashboard serves task context, traces, recovery counts and comparison
JSON. Both comparison timing cases pass: an early unverified attempt remains in
history but is excluded from matched statistics; a recorded image permits matching.
The test driver now asserts these distinct cases instead of assuming startup timing.
No product/grader/provider behavior was changed for release, aside from version metadata.
Source archive rebuild matches every wheel entry. Public verification follows publication.

## Public release and completion

v1.3.0 is published at https://github.com/Ethant35/agent-benchmark-lab/releases/tag/v1.3.0
from merge fcaf3322289de6512c13ba0ae173481c6117f805 (PR10). Unauthenticated
wheel/source/checksum downloads match the accepted assets. A second fresh install
in ~/Applications/AgentBenchmarkLab/1.3.0 imports only its installed package and
uses the same audited runtime dependencies. Its CLI, reopened restored history,
comparison/evidence/download and task identities pass without source paths. All
restored task contexts and traces still work after candidate/source/backup removal.

Technical gates1–7 are complete. Screenshots, checksums, dependency versions and
cleanup evidence are in evidence/release-1.3.0/. No provider charges. Unfamiliar-
developer usability remains pending. No model-quality or causal-ranking claim is made.
