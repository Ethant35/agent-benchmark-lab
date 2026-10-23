# First use and returning use
Author: Ethan

This guide is for the supported local setup: macOS Apple Silicon, Python 3.12, and Podman. The released wheel contains the dashboard. A user does not need Git, Node.js, or a frontend build to install it.

## 1. Install and check prerequisites

Follow the wheel installation in [README.md](../README.md#install-the-released-app), then check the Python package and container runtime:

```sh
source ~/agent-benchmark-lab/.venv/bin/activate
abl check
podman machine list
podman info
```

`abl check` reports which prerequisite is unavailable and what to inspect next. If the Podman machine is stopped, start it:

```sh
podman machine start abl-benchmark
podman info
abl check
```

If the required image is missing, use the pull command printed by `abl check` (for the standard image: `podman pull docker.io/library/python:3.12-slim`) and check again. Do not remove Podman data as a troubleshooting step. Do not run task code directly on the host if the container runtime fails. The application refuses that fallback.

## 2. Run the free reference task

Choose an empty directory for results. The guided start runs one deterministic rounding reference task, checks its output with the independent verifier, and stores the run in that directory. It makes no model-provider request and costs $0.

```sh
mkdir -p ~/abl-results
abl start --root ~/abl-results
```

The CLI prints progress while the task runs. At completion, it gives the run ID, the verifier outcome, and the next command to inspect the result. The reference implementation provides a local setup check; its PASS result is not a model score.

Inspect the completed run and its trials with:

```sh
abl runs --root ~/abl-results
abl inspect RUN_ID --root ~/abl-results
```

`RUN_ID` is the identifier printed by `abl start`. These commands read the saved result store and do not start inference.

## 3. Open the dashboard

Use the same result directory to open the local dashboard:

```sh
abl dashboard --root ~/abl-results
```

Open <http://127.0.0.1:8765>. The dashboard reads local records from the directory supplied on the command line. Stop it with Ctrl-C.

The workspace view distinguishes an empty store from a filter with no matches. The first means no run has been recorded in this directory. The second means records exist but the active filters exclude them. Clear filters to return to the full set. Filters and selected result details are restored on a later visit. Use the result detail view to inspect the verifier, trace, run configuration, and per-trial cost provenance; null or unknown values remain visible as unknown.

## 4. Choose and authorize an optional model run

The reference flow never asks for provider credentials. A model run is a separate, optional action. Before starting it, decide which exact provider and model to use, check their current prices, and choose a spending cap. Use your provider's account-level cap for an enforceable billing ceiling; the app's cost estimate depends on configured prices and provider-reported usage.

Enter the provider key through the current shell environment. Keep it out of the YAML and source tree. Create and review a configuration:

```sh
abl configure model.yaml
# If no key is set, interactive abl start asks for hidden input after consent.
```

Confirm the provider, exact model ID, endpoint, input/output price assumptions, request and token limits, and maximum run spend in `model.yaml`. The command does not choose or substitute a model. Then request the model run:

```sh
abl start --config model.yaml --root ~/abl-results
```

Before it makes a provider request, the guided flow shows the selected provider/model and cost preview and asks for explicit consent. Decline or cancel to return without making a request. During the run, progress identifies the active task and tool/request state without printing the credential. Cancellation terminates owned work and marks the run for recovery. If a request outcome or charge is unknown, the app retains the known subtotal, reports the unknown remainder, and blocks paid resume for that run. Provider-side billing reconciliation stays separate from immutable trial records. If the final charge remains unknown, review it and choose a new explicit cap before starting a new run.

To inspect an interrupted run, use `abl inspect RUN_ID --root ~/abl-results`. Resume only with the same root and unchanged task/image manifest:

```sh
abl start --root ~/abl-results --resume RUN_ID
```

Both commands accept the same YAML configuration. The compatibility `abl run` command prints JSON and assumes the script author has already authorized execution; `abl start --config` adds preview and consent. The guided wrapper does not alter the task contract or its deadline. Resuming a paid run can make remaining provider requests, so review the run state and configuration first.

## 5. Return to prior work

Activate the same virtual environment and use the same result directory. The CLI lists prior runs; the dashboard restores its view state and saved filters:

```sh
source ~/agent-benchmark-lab/.venv/bin/activate
abl runs --root ~/abl-results
abl dashboard --root ~/abl-results
```

If there are no rows, confirm that `--root` points to the directory used earlier. If the dashboard reports zero filter matches, clear the filters. A new empty result directory remains separate from existing history.

## 6. Back up, update, and roll back

Back up only when no run is active. The destination must not already exist. Restore checks the backup manifest and writes only to a new destination; it does not merge or overwrite records.

```sh
abl backup ~/abl-results-backup --root ~/abl-results
abl restore ~/abl-results-backup --root ~/abl-results-restored
```

Download the next supported wheel and verify its published SHA-256 checksum before installation. Install it into the existing virtual environment. The additive store migration keeps old records readable; keep the result directory and verified backup separate from package files.

```sh
source ~/agent-benchmark-lab/.venv/bin/activate
uv pip install --upgrade ./agent_benchmark_lab-NEXT_VERSION-py3-none-any.whl
abl check
abl runs --root ~/abl-results
```

If the new app version does not work, install the prior wheel in a separate environment and read a restored copy of the pre-update backup. Do not restore over the existing result directory. Restore the backup to a new path only if recovery from the saved copy is required. Follow the detailed [operations guide](OPERATIONS.md) for store compatibility, rollback, and recovery limits.

## Interpreting evidence scopes

Keep these records separate when reading reports:

- The historical twelve-task model benchmark on the bundled 30-second contracts scored **8 PASS, 3 FAIL, 1 TIMEOUT** and recorded **$0.014957188** in observed key charges. Those outcomes and costs are immutable historical evidence.
- The provider integration check used a separately versioned 120-second task contract to qualify streaming and nonstreaming paths. Its cost was **$0.001403188**. The longer timeout did not change, retry, or rescore the historical benchmark.
- A reference run uses deterministic local actions, makes no provider request, and costs **$0**. It verifies local setup and the reference verifier path; it says nothing about model quality.

See the [original full-run report](../evidence/full-deepseek-1017/REPORT.md), [readiness record](../READINESS.md), and [operations guide](OPERATIONS.md) for exact provenance and cost reconciliation.
