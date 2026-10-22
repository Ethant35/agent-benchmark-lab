# Local acceptance
Author: Ethan

Status: IN PROGRESS. No release accepted yet. GitHub Actions is intentionally omitted and repository Actions permissions are disabled per Ethan. Equivalent acceptance runs locally.

## Environment
macOS arm64, Python 3.13.17, Node 22.13.1, Podman 6.1.4. Dedicated `abl-benchmark` VM: 2 CPUs, 2 GiB RAM, 12 GiB virtual disk. Container image: `docker.io/library/python:3.12-slim`; actual content ID recorded per trial. No OpenRouter credential is present in the process environment.

## Commands and observations
- `uv venv --python python3.13 && uv pip install -e .`: PASS, initial installation.
- `uv lock`: PASS, Python dependency lock generated.
- `cd dashboard && npm install && npm run build`: PASS, TypeScript and Vite production output.
- `.venv/bin/abl validate`: PASS, 12 schemas and all six categories.
- `.venv/bin/python -m compileall -q abl tests`: PASS, syntax only.
- Missing engine initial `abl doctor`: correctly BLOCKED_EXTERNAL, no host fallback.
- First Podman smoke attempt: ERROR/isolation_error from a damaged image layer after VM lifecycle interruption. Cleanup succeeded. Image repull and rerun required; this is not acceptance PASS.

## Required matrix
BL-01–BL-18: PENDING real CLI/container/browser E2E.
BL-19–BL-22: BLOCKED_EXTERNAL, missing authorized OpenRouter credential. **Live model integration unverified.** No mocked responses or fabricated model results used.

Detailed machine-readable evidence will be saved from the public CLI/container harness `tests/e2e.py` and Playwright. Release permitted only once every deterministic gate passes.
