# Usability and distribution acceptance
Author: Ethan
Date: 2026-10-22

Status: QUALIFIED AND RELEASED as v1.2.0. Public download, fresh installation and free first task verified.

The supported target remains macOS Apple Silicon / Python 3.12 / rootless Podman.
The new flow is additive: `abl start`, `abl configure`, `abl check`, and a read-only
workspace identity/command endpoint. Existing JSON commands, task contracts, provider
adapter, cost ledger and schema remain compatible. No native launcher or notarization.

| Gate | Evidence required | Status |
|---|---|---|
| Free first task | Clean installed wheel: one rounding reference PASS, zero API cost, progress before completion | PASS |
| Consent/config | Explicit model/provider/prices/reserve; reject declined/mismatched consent; hidden process-only key | Local tests pass; no paid requests |
| Container setup | Missing engine/image readable, no automatic install/reset/pull; real supported engine | PASS; real installed and publicly downloaded tasks pass |
| Cancellation/recovery | Real SIGTERM, preserved history, resume, resource cleanup | PASS |
| Returning dashboard | Empty vs no matches, per-workspace saved filters/details, live progress, accessible keyboard/mobile | PASS |
| Distinct evidence | Reference controls, model benchmarks, integration contract/version/config identity | PASS |
| Update/restore | Upgrade v1.1.0 root, exports unchanged, backup/restore and rollback | PASS |
| Release | Audits, full tests, disabled Actions, merged PR #6, publication and public download verified | PASS |

No unfamiliar-user testing, recruitment, telemetry or field-performance claim is made.
This phase does not rerun the model benchmark or amend historical scores/costs.


Observed release results:
- 78 local tests pass. One existing Starlette/httpx deprecation warning remains visible.
- 15 browser checks pass against the installed final wheel. Axe is clear in tested
  main/detail views; screenshots are retained with Author Ethan metadata.
- All 12 reference tasks pass through the legacy installed-wheel JSON CLI. Their
  contracts and costs remain unchanged; source/provider/isolation byte comparisons pass.
- Final installed-wheel journey passes: empty API, free reference, returning results,
  byte-identical backup/restore, actual SIGTERM interruption, resume to expected TIMEOUT,
  and no owned containers/volumes. Source and initial-wheel runs are separately retained.
- Real v1.1.0 record export remains byte-identical after upgrade. A separate v1.1.0
  rollback environment reads its restored pre-update backup with the same export hash.
- Frozen Python, installed-wheel dependency and npm audits found no known vulnerabilities.
  Installed wheel resolved FastAPI0.161.1; frozen development uses0.161.0. Both audited.
- 76 packaged runtime/corpus/static files match source and installed wheel; metadata
  Author Ethan verified. Required third-party notices remain.
- Provider requests in this phase: zero. API cost: $0. Historical provider and full12
  evidence is byte-unchanged; no new model quality or deadline claim is made.

The dashboard is read-only; live execution/consent/cancellation remain in the CLI.
URL filters override saved state. Saved evidence restores on a plain return without
query filters. Native screen-reader/OS zoom and unfamiliar-user studies were not run.
Final browser process on port8772 was stopped after packaged-browser verification.
Source-editable CLI failure was traced to hidden `.pth` files skipped by Python;
prebuilt-wheel execution passes independently. Failed harness assumptions and preliminary
roots were retained under `.abl/`, not recast as product failures or passing evidence.

Release: https://github.com/Ethant35/agent-benchmark-lab/releases/tag/v1.2.0
Immutable tag commit: `9f2078122ec0dea02aac10427e6f9d31659e302a`.
Public wheel and source downloads match the published checksums and locally qualified
assets. The downloaded wheel passed the full journey recorded in downloaded-journey.json.
After publication, an unauthenticated public download installed into a fresh Python 3.12
environment, passed `abl check`, and completed free run `dc981ce952224d7cbedf82f3486ac6c9`.
The release wheel is byte-identical to the final wheel used for all 15 browser checks.

The newly approved Semgrep scan ran all nine selected packs/repositories. It produced
36 indicators: long expressions, intentional container/verifier execution and literal
platform imports. Manual triage found no confirmed vulnerability. This is partial
coverage: 15 third-party rule compile errors, no Pro cross-file analysis, and unavailable
p/yaml. The runner pruned non-rule YAML and one unsupported join rule. Gitignored files
and scan output are excluded. No findings were suppressed. See semgrep.json and
semgrep.sarif in evidence/usability/. Prior scan output was preserved locally.
