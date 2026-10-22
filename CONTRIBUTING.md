# Contributing
Author: Ethan

Use Python 3.12+, Node 22+, and Docker or Podman. Install with `uv sync --frozen`; build the UI with `cd dashboard && npm ci && npm run build`. All validation is local. Do not add or enable GitHub Actions for this repository.

Add task fixtures independently from their reference solution. Verifiers must inspect observable results and reject the starting fixture for missing repairs/features. Refactors must preserve baseline behavior and require the requested structure. Run candidate code in unprivileged verifier subprocesses; never import it into the trusted root verifier. Keep source paths and explicit explanations in navigation answers.

Run `abl validate`, `python tests/e2e.py --cli .venv/bin/abl --root .abl/review`, then serve that database with `abl dashboard --root .abl/review` and execute `npm run test:e2e` from dashboard. Use a fresh root for each acceptance run. All tests use real CLI, containers, verifier processes, persisted SQLite data and browser requests. Do not add mocked provider responses or unit tests as substitutes for acceptance. Live checks require explicit credential setup, selected models and a small spending cap.

Include task versions, commands and exact evidence in a PR. Keep unknown measurements null, respect runner/provider/model separation, and include failed attempts in comparisons. Use focused commits and never force-push shared history.
