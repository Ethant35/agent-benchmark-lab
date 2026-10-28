---
name: verify-agent-benchmark-lab
description: Explicit local verification of Benchmark Lab's installed wheel, guided CLI, read-only dashboard, recovery and retained evidence.
disable-model-invocation: true
---

# Verify Agent Benchmark Lab
Author: Ethan

Invoke by explicitly asking the agent to read this file. This directory is separate
from the shared `.agents/skills` symlink. Picker discovery is not claimed.

## Launch

Use the repository root. Read AGENTS.md, CONSTRAINTS.md and the current HANDOFF.md.
Keep the account usage guard active if required by the current assignment. Stop
owned processes at its threshold; never run the guard while awaiting user input.

The supported target is macOS Apple Silicon, Python 3.12 and Podman. This procedure
uses free reference execution, never a model configuration or provider credential.
Restore locked development dependencies with `uv sync --frozen` and
`npm ci --ignore-scripts --prefix dashboard` if absent. Do not change lockfiles.

Build and install an isolated candidate. Use a new output directory for each run:

```sh
npm run build --prefix dashboard
uv run --frozen python -m pytest -q
.venv/bin/python .agents/verify-agent-benchmark-lab/scripts/build_candidate.py \
  --output .abl/verify-candidate --include abl/presentation.py
uv venv --python 3.12 .abl/verify-candidate/install
uv pip install --python .abl/verify-candidate/install/bin/python .abl/verify-candidate/dist/agent_benchmark_lab-1.2.1-py3-none-any.whl
```

The filename above matches the current package version. If the version changes,
use the exact wheel just built. Record its SHA256 and verify installed Python files,
static assets and corpus bytes against that wheel. Run installed Python with `-I`
to prevent a source checkout from masking package errors. Check `Author: Ethan` in
the saved wheel metadata. Do not replace or upload a published release asset.

The executable build helper copies tracked working files and the built static bundle
to a new staging directory. `--include` names reviewed new source files that are not
tracked yet. It records a source hash manifest. This avoids packaging unrelated local
files, including the existing duplicate files with names ending in ` 2.py`. Leave
those files in place. For test counts, report canonical tests separately from duplicate
files that pytest may also discover. Do not delete either set to change the count.

## Doctor

Run `<candidate-install>/bin/abl check`. It must report a ready runtime and existing
image before reference execution. If the VM is stopped, inspect `podman machine list`
and start only the named existing dedicated VM. Record whether this verification
started it. Missing engine, VM or image is a prerequisite finding. Do not reset data
or silently install global tools. Existing-VM evidence is not new-Mac setup evidence.

The helper starts its own loopback dashboard on an available port and a new private
result directory. It checks `/api/workspace` and the expected saved trial count.
HTTP reachability alone is not readiness. After any failure, inspect the saved logs
and check the affected prerequisite again before retrying in a new evidence directory.

## Drive

Run the executable helper with the repository environment, which supplies PyYAML to
the reused CLI journey. Give an absolute candidate CLI path and a new evidence path:

```sh
.venv/bin/python .agents/verify-agent-benchmark-lab/scripts/verify.py \
  --cli "$PWD/.abl/verify-candidate/install/bin/abl" \
  --evidence "$PWD/.abl/verify-candidate/evidence"
```

The helper reuses `tests/usability_e2e.py --recovery-mode success` and the existing
`dashboard/e2e.spec.ts`. It does not create a parallel test framework. The CLI journey
checks empty state, first free PASS, progress, returning results, filters, backup and
restore, a real SIGTERM, resume to PASS and resource cleanup. It preserves the original
timeout-recovery control through the harness's default `--recovery-mode timeout`.

The candidate API must show one scheduled task passed after recovery and two retained
attempts with a 50% attempt pass rate. The CLI still exits 1 because the interrupted
attempt remains in its historical exit contract. The browser suite drives real saved
rows and downloads. Its explicit fixtures test errors, large histories and unknown
values; do not describe those fixture cases as real provider behavior.

Only the lead drives a running UI. Browser tests are headless. For visual review,
inspect the saved desktop, mobile and detail screenshots. Use accessible labels and
`data-testid` selectors from the existing suite. No dashboard execution or cancel
endpoint is allowed.

## Evidence

The helper writes `verification.json`, doctor/journey/browser logs, recovered API
responses, screenshots, and the isolated state with trace/artifact files. Keep all
failure evidence as well as successful reruns. Do not copy credentials or provider
payloads into committed reports. Retain exact/unknown costs, manifest identities and
all interrupted attempts. Report API charges as $0 only after checking that all real
execution rows used the reference runner with provider `none` and cost zero.

The [feature map](features/README.md) covers five journeys. Before calling the procedure
complete, execute it, inspect its side effects and confirm evidence survives cleanup.
For maintenance, source-check each mapped feature and drive every feature at least
once. Record product defects as defects, not by weakening expected outcomes. Independent
review may use up to two authorized assistants; never infer delegation authorization
from this file or spawn nested agents.

## Cleanup

The helper terminates its exact dashboard PID on success or failure. Child command
timeouts terminate their owned process group. It never deletes evidence. Check owned
container and volume names against the persisted trial environment IDs. Do not kill
processes by name or delete unrelated data. Stop the dedicated VM only if this session
started it and no unrelated workload is using it. Confirm the dashboard port closed
and `verification.json`, logs and screenshots remain. Keep candidate installs and
private state until no longer needed for review; evidence must remain available.

## Limits

No paid calls, speed comparison, unfamiliar-user study, new-Mac certification, release
publication, GitHub Actions, hooks, global settings or skill installation is included.
Legacy task text stays unavailable unless the saved identity can be proved. Run-level
schedule outcomes are distinct from attempt-level benchmark scores and spend.
