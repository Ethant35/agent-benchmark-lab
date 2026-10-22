# agent-benchmark-lab
End-to-end benchmarking for AI models and agents

Agent Benchmark Lab measures actual task completion through independent behavioral verifiers, with fresh constrained containers, recorded traces and reproducible exports.

**Live OpenRouter smoke tests passed** on v1.0.1 with `deepseek/deepseek-v4.1-flash-1017`: streaming, nonstreaming, intentional tool-limit failure, and returned usage accounting. This covers one small task, not full-corpus model performance or every provider. The reference suite separately tests the framework. See [ACCEPTANCE.md](ACCEPTANCE.md) for dated evidence. GitHub Actions is intentionally disabled; all acceptance runs locally.

## Install

Requires Python 3.12+, Node 22+ for building the dashboard, and a running Docker or Podman engine. No Claude account is needed.

```sh
git clone https://github.com/Ethant35/agent-benchmark-lab.git
cd agent-benchmark-lab
uv sync --frozen
cd dashboard
npm ci
npm run build
cd ..
# Use docker instead when that is your installed engine.
podman pull docker.io/library/python:3.12-slim
uv run abl doctor
uv run abl init
uv run abl validate
```

On macOS, initialize/start a Podman machine before pulling the image. The CLI refuses execution without a working container engine. No unrestricted host fallback exists. Prebuilt release wheels include the dashboard; source installations must build it before `abl dashboard`.

## Run the entire reference suite

```sh
uv run abl tasks list
uv run abl tasks inspect bugfix-rounding
uv run abl run --root .abl/reference --repeats 3
uv run abl runs --root .abl/reference
uv run abl compare --root .abl/reference
uv run abl report report.html --root .abl/reference
uv run abl export results.json --root .abl/reference
uv run abl export results.csv --format csv --root .abl/reference
uv run abl dashboard --root .abl/reference
# Open http://127.0.0.1:8765
```

The CLI prints run/trial IDs. Inspect with `abl inspect RUN_ID --root PATH`, cancel from another terminal with `abl cancel RUN_ID --root PATH`, and resume an interrupted schedule with `abl run --resume RUN_ID --root PATH`. Completed slots are not repeated. A run returns nonzero if any trial did not pass.

## Compare two live configurations

Set `OPENROUTER_API_KEY` in your shell without saving it in repository files. Use an independently capped provider key for a hard billing limit. Select exact tool-capable model IDs from your authorized account. Start from `examples/openrouter.yaml`, then copy it to two files and set distinct model/settings. Supply conservative current prices in USD per million tokens. The CLI enforces a per-run request-reserve spending check and records actual provider cost when available. It does not silently perform live calls during installation or tests.

```sh
uv run abl validate --config model-a.yaml
uv run abl run --root .abl/comparison --config model-a.yaml
uv run abl run --root .abl/comparison --config model-b.yaml
uv run abl compare --root .abl/comparison
uv run abl dashboard --root .abl/comparison
```

Provider adapters: OpenRouter and explicitly configured OpenAI-compatible Chat Completions endpoints. JSON responses and optional OpenAI-format SSE are supported; endpoint capabilities must be declared. Runners: deterministic reference actions and the bounded provider-neutral tool-calling agent. The adapter never converts prose into invented tool calls. Request errors, missing credentials, unsupported capabilities, step limits, budget limits and verifier failures are distinct outcomes.

## Corpus and evidence

Twelve small stdlib Python tasks cover bug fixing, feature implementation, repository navigation, refactoring, structured extraction and multistep tool use, two each. Files, executable behavior, schema values and source facts are checked. Refactoring compares original and changed behavior. Public verifier source is excluded from running agent environments.

Trial records include configuration/task/image hashes, UTC timestamps, outcome and failure reason, wall/API latency, measured streaming TTFT, token/cache counts, tool failures, retry counts, cost source and verifier output. Unknown provider measurements are null, never invented zeroes. Aggregates include unsuccessful attempts and report coverage. See [METHODOLOGY.md](METHODOLOGY.md), [BENCHMARK_FORMAT.md](BENCHMARK_FORMAT.md), [ARCHITECTURE.md](ARCHITECTURE.md), and [SECURITY.md](SECURITY.md).

## Local E2E acceptance

```sh
uv run python tests/e2e.py --cli .venv/bin/abl --root .abl/acceptance-new
uv run abl dashboard --root .abl/acceptance-new
# In a second terminal:
cd dashboard
npx playwright install chromium
npm run test:e2e
```

These checks invoke real public CLI commands, containerized execution, verifier subprocesses, SQLite and the browser. No unit tests or mocked AI responses substitute for live checks. Live BL-19–22 require credentials and explicit model choices; missing credentials are recorded BLOCKED_EXTERNAL.

Author: Ethan. MIT license; original license retained.
