# Agent Benchmark Lab

Agent Benchmark Lab measures whether an AI agent completes small software tasks. Each task runs in a constrained container and is checked by an independent verifier. Results include failures and unknown measurements; the app does not turn missing cost data into zero.

**Supported setup:** macOS on Apple Silicon, Python 3.12, and Podman. Docker and other OpenAI-compatible endpoints are implemented but are not part of the qualified target. Windows is unsupported. Git, Node.js, and a frontend build are not needed for the supported wheel installation.

## Install the released app

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if it is not already available. It creates an isolated Python 3.12 environment and can download Python when needed. The supported wheel route needs no Git, Node.js, or frontend build. Qualification used Python 3.12.14.

Install the current release wheel in a dedicated Python environment. Release files and SHA-256 checksums are published on the [GitHub Releases page](https://github.com/Ethant35/agent-benchmark-lab/releases/latest). The commands below pin the v1.2.0 wheel; check the release page if a later release is available.

```sh
set -e
mkdir -p ~/agent-benchmark-lab
cd ~/agent-benchmark-lab
uv venv --python 3.12 .venv
source .venv/bin/activate
wheel_path=agent_benchmark_lab-1.2.0-py3-none-any.whl
curl -fL -o "$wheel_path" \
  https://github.com/Ethant35/agent-benchmark-lab/releases/download/v1.2.0/agent_benchmark_lab-1.2.0-py3-none-any.whl
curl -fL -o SHA256SUMS.txt \
  https://github.com/Ethant35/agent-benchmark-lab/releases/download/v1.2.0/SHA256SUMS.txt
expected_hash=$(awk '$2 == "agent_benchmark_lab-1.2.0-py3-none-any.whl" { print $1 }' SHA256SUMS.txt)
test -n "$expected_hash"
printf '%s  %s\n' "$expected_hash" "$wheel_path" | shasum -a 256 -c -
uv pip install "./$wheel_path"
abl --help
```

Keep the `.venv` directory for later updates. The wheel includes the dashboard's built files. Do not install from a source checkout unless you intend to work on the project.

## Set up the container runtime

Install [Podman](https://podman.io/docs/installation) for macOS. Podman runs Linux containers inside a small virtual machine. Use the existing `abl-benchmark` machine if you already created it. Use the macOS installer recommended by Podman; the linked instructions also describe existing Homebrew setups. For a new machine, create and start it:

```sh
podman machine init --cpus 2 --memory 2048 --disk-size 12 abl-benchmark
podman machine start abl-benchmark
podman info
```

If `podman machine init` says the machine already exists, inspect and start that machine instead:

```sh
podman machine list
podman machine inspect abl-benchmark
podman machine start abl-benchmark
podman info
```

The app checks the runtime and reports if its task image is missing. Pull it with the command shown by `abl check`, then run the check again. It never runs task code directly on the Mac. If Podman does not respond, run `podman machine list`, `podman machine inspect abl-benchmark`, and `podman info`, when it has no other active work, restart the dedicated machine with `podman machine stop abl-benchmark` followed by `podman machine start abl-benchmark`. Do not run prune or delete commands to troubleshoot; they can remove containers, images, or volumes used by other work.

## Get a first result without model charges

Create a new, empty directory for this app's results. It is separate from the project source and contains its local database, traces, and task artifacts.

```sh
mkdir -p ~/abl-results
abl check
abl start --root ~/abl-results
abl runs --root ~/abl-results
```

The first guided run uses the deterministic reference implementation for the small rounding task. It makes no provider request and costs $0. The CLI shows progress and then reports the verifier result. A passing reference run verifies the local install, container and result store; it does not score a language model.

To revisit the records, start the dashboard against the same result directory:

```sh
abl dashboard --root ~/abl-results
```

Open <http://127.0.0.1:8765>. Stop the dashboard with Ctrl-C. On later visits, use the same `--root` to see prior runs and saved filters. A genuinely empty workspace has no runs. If filters match zero runs, clear or adjust the filters; the page says which state you are viewing.

## Optional model run

Model calls are separate from the free reference run. Choose an exact provider, model ID, endpoint, and current input/output prices. `abl configure` writes an explicit configuration file for review; it does not select or substitute a model for you. Add the provider key to the process environment without putting it in the YAML file or repository. Before consent, inspect the selected model and its price assumptions and set a maximum run spend. The configured price estimate is not a provider-side billing limit. Use a provider key/account limit for a hard external cap.

```sh
read -s "OPENROUTER_API_KEY?OpenRouter API key (hidden): "
export OPENROUTER_API_KEY
abl configure model.yaml
```

Review `model.yaml`, including the exact provider/model, token and request limits, USD-per-million-token prices, and maximum run spend. The guided start displays a cost preview and asks for explicit confirmation before any provider request:

```sh
abl start --config model.yaml --root ~/abl-results
```

Do not commit the key or config file. Unset the key when finished with this terminal session. Unknown final charges stay unknown and block paid resume for that run. Reconcile billing separately; records are immutable. A new run needs a new, explicit spending decision. The CLI does not silently retry paid requests. See [Operations and recovery](docs/OPERATIONS.md) for accounting details and the exact limits.

## Existing JSON and benchmark workflows

The lower-level `abl run --config FILE --root DIR` command remains for advanced scripts and legacy workflows. It accepts an explicit configuration and prints the legacy JSON run/trial records, but does not provide the guided consent flow. Prefer `abl start --config model.yaml` for the reviewed optional model path. Existing benchmark results keep their original task deadlines and outcomes.

The historical full-corpus DeepSeek run recorded 8 PASS, 3 FAIL, and 1 TIMEOUT at an observed key charge of $0.014957188. Separately, the provider integration check used a versioned 120-second task contract and cost $0.001403188. That integration check did not extend or rescore any historical 30-second benchmark task. See the [original benchmark report](evidence/full-deepseek-1017/REPORT.md) and [current readiness record](READINESS.md).

## Updates and recovery

Before an update, make a verified backup into a new destination. Install the next wheel into the same virtual environment; keep the result directory untouched. For rollback, install the prior wheel in a separate environment and open a restored copy of your pre-update backup. Keep the original history intact. Restore a backup only to a new, empty destination; restore refuses to overwrite existing data.

```sh
abl backup ~/abl-results-backup --root ~/abl-results
uv pip install --upgrade ./agent_benchmark_lab-NEW_VERSION-py3-none-any.whl
abl check
abl dashboard --root ~/abl-results
```

For an interrupted run, use the run ID printed by the CLI. Resume with the same result root and unchanged task/image manifest. Completed slots are retained; interrupted slots are recovered before remaining work starts. If uncertain, inspect the run and diagnostics before resuming:

```sh
abl inspect RUN_ID --root ~/abl-results
abl diagnostics --root ~/abl-results
abl start --root ~/abl-results --resume RUN_ID
```

See [USABILITY.md](docs/USABILITY.md) for first-use, returning-use, update, backup, and recovery walkthroughs; [OPERATIONS.md](docs/OPERATIONS.md) for support and rollback; and [SECURITY.md](SECURITY.md) for privacy and isolation.

## Development and acceptance

The source-development path requires Git, Python 3.12, and Node.js 22+ to build the dashboard. It is not needed by wheel users.

```sh
git clone https://github.com/Ethant35/agent-benchmark-lab.git
cd agent-benchmark-lab
uv sync --frozen --python 3.12
npm ci --prefix dashboard
npm run build --prefix dashboard
uv run abl check
```

Container and browser acceptance instructions are in [CONSTRAINTS.md](CONSTRAINTS.md) and `tests/`. Do not treat reference checks as live-provider results. GitHub Actions is disabled. Author: Ethan. MIT license; bundled dependency notices are retained.
