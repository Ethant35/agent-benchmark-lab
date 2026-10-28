# Result clarity and production acceptance
Author: Ethan
Date: 2026-10-27

The v1.2.1 candidate passed local qualification for macOS Apple Silicon, Python 3.12
and rootless Podman. Public release/download qualification is recorded separately in
`evidence/result-clarity/release-provenance.json` after publication. A candidate pass
alone does not prove a published download works.

## Behavior and compatibility

The dashboard and guided CLI distinguish scheduled task completion from retained
attempts. A real interrupted task resumed successfully: one scheduled task passed,
two attempts remained, the attempt pass rate stayed 50%, and legacy CLI exit 1 stayed
unchanged. The interrupted document was unchanged after resume. No historical attempt,
score, deadline or provider cost was rewritten.

Task descriptions and expected artifacts appear only when saved manifest, task version,
corpus hash, task artifact identity and installed tree match. Missing identity produces
an explicit unavailable state. The selected/latest matching run is named; attempt
metrics and terminal spend cover the active filters. An active total is unavailable,
with the terminal known subtotal labelled. Technical details expose allowlisted settings,
fingerprints, trace and measurement sources. The API remains read-only.

## Observed checks

| Gate | Evidence and result |
|---|---|
| Local regression | 91 canonical Python tests pass; duplicate local filenames excluded from the count, preserved on disk |
| Installed CLI | All 12 reference controls pass; failure, timeout, tool recovery, cancellation, isolation, resume, export and aggregate checks pass |
| Complete user journey | Free task, real SIGTERM, successful recovery, returning API, filters, backup/restore, exact exports, database rows and artifact hashes pass |
| Browser | 18 checks pass; real persisted records plus explicit fixtures for large history, errors, unknown costs and configuration differences |
| Accessibility | Axe reports zero violations in checked views; forward/reverse focus through collapsed and expanded details, focus return, 320px reflow and scrollable evidence pass |
| Visual inspection | Desktop summary, result detail and mobile screenshots inspected; outcomes/evidence first, charts and technical fields collapsed initially |
| Upgrade and rollback | Public v1.2.0 free result survives upgrade to v1.2.1; separate v1.2.0 rollback reads restored backup with equal exports, rows and artifacts |
| Uninstall | Removing the package from the separate rollback environment preserves its result database and artifacts |
| Package | 77 runtime files match source and installed wheel; Author Ethan; unrelated duplicate files excluded |
| Historical boundaries | 77 baseline engine/provider/corpus/isolation/recovery/evidence files remain unchanged; earlier live qualification remains scoped to those bytes |
| Dependencies | Frozen development, newly resolved installed-wheel Python dependencies and npm audited: no known vulnerabilities |
| Static review | Nine approved Semgrep rulesets run, 43 indicators reviewed, no confirmed vulnerability; 15 rule errors, no Pro, YAML ruleset unavailable |
| Cleanup | Installed procedure stops its dashboard and closes its port; acceptance leaves no owned containers or volumes |

Evidence is in `evidence/result-clarity/`. Full private state, logs, screenshots and
failed iterations remain in `.abl/production-20261027/`. The first candidate's browser
regression exposed focus moving into hidden disclosure content; the repaired candidate
passed the full procedure. Evidence from the earlier candidate is not substituted for
changed bytes. Static findings include two alerts in the explicit verification helper:
its URL is fixed to loopback and its CLI subprocess uses an argument list without a shell.

No provider calls were made; API cost is $0. Reference controls do not score a model.
The historical DeepSeek full-corpus result and separately versioned integration test
remain separate. No expired or spent paid allowance was renewed. Docker, Windows,
other compatible services, unfamiliar-user studies, new-Mac setup, native assistive
technology certification and runtime/kernel escape immunity are not claimed.

## Reproduce

The explicit local procedure is `.agents/verify-agent-benchmark-lab/SKILL.md`, with
five feature maps and a launcher that reuses the public CLI and browser harnesses.
It is separate from shared skills; no global settings, hooks or picker registration
are needed. Build from clean tracked source plus named new files. Do not package local
duplicate files or private result roots. Use the exact installed wheel for user journeys.
The source distribution includes built dashboard assets for a wheel rebuild without Node.

The independent review covered backend identity, snapshot consistency, costs and legacy
contracts, dashboard navigation/settings and helper packaging/cleanup. The final keyboard
fix was demonstrated by the failing then passing browser regression. No performance
comparison or field-user learning claim is made. Existing project-local source-guided
verification and review procedures were retained; no new upstream plugin was installed.
