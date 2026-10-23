# ADR 002: Guided execution stays in the local CLI
Author: Ethan
Date: 2026-10-22
Status: Accepted

New users need one short path from an installed wheel to a useful saved result.
The existing CLI already owns credentials, execution, interruption, locking and
spending enforcement. The dashboard is a loopback, read-only view of that store.

Add `abl start` as a human-readable wrapper over the existing runner. Its default is
one free reference task. An explicit model file must identify the provider, model,
price bounds and whole-run reserve. The wrapper shows effective task deadlines and
requires confirmation, or exact `--accept-cost` consent for deliberate automation.
An optional hidden credential is process-local. `abl configure` creates a private,
exclusive new YAML file with no credential value. `abl check` diagnoses prerequisites
without downloading, starting, deleting or resetting anything.

Use an optional metadata-only progress observer in the runner. It does not change
recorded events, cost calculations, task deadlines, resume manifests or legacy JSON
output when absent. Keep the lower-level `abl run` contract for existing scripts.
Do not add browser write routes, credential storage, background daemons or a native
launcher. No notarization is needed for this Python package and local web app.

The additive `GET /api/workspace` returns three strings: `workspace_id` (SHA-256 of
the resolved result root), `start_command` and `dashboard_command` (shell-quoted
commands for that root). Existing loopback Host, Origin and no-store rules apply.
The browser persists only filters, page and a trial ID under that workspace identity.
Explicit query filters win over saved state. Visible tabs poll every three seconds;
hidden tabs and pending filter requests do not poll. Evidence remains on the local server.

Acceptance uses real installed-wheel reference tasks, interruption/recovery,
update/rollback, browser checks, and downloaded-release checks. Controlled UI and
consent fixtures are labelled. No model performance or unfamiliar-user study is inferred.
