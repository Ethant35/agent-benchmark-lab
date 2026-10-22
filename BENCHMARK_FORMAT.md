# Benchmark format v1
Author: Ethan

Each `corpus/<id>/` contains `task.yaml`, original `fixture/`, trusted `verifier/check.py`, and `reference.json`. Only fixture files and the public description reach the agent. Task definitions are trusted operator input, not downloaded executable configuration.

```yaml
schema_version: 1
id: bugfix-rounding
version: '1.0'
category: bug_fix
description: Repair decimal rounding in app.py.
fixture: fixture
setup: []
allowed_tools: [read_file, write_file, shell, finish]
network: none
runtime_seconds: 30
max_tool_steps: 20
token_budget: null
cost_budget_usd: null
verifier: [python, /verifier/check.py]
expected_artifacts: [app.py]
cleanup: always
```

Categories are `bug_fix`, `feature`, `navigation`, `refactor`, `extraction`, `multistep`. Unknown fields, schema versions and unsafe fixture paths are rejected. Version 1 supports only network `none` and cleanup `always`; broad network access is intentionally not implemented. Setup commands are trusted task setup but execute inside the constrained agent container. Runtime covers setup, agent work and verification; cleanup may add a bounded delay.

Reference actions are JSON arrays of `{ "tool": "write_file", "arguments": { "path": "app.py", "content": "..." } }`, `read_file`, `shell` or `finish`. They are infrastructure fixtures, not model completions. File tools require paths under `/workspace`. Shell commands have the container's constrained filesystem view.

Run configuration accepts runner/provider/model identity, endpoint and credential **environment variable name**, capability flags, optional streaming/temperature/reasoning effort, request/output/tool/runtime/token budgets, conservative price bounds, spend limit, repeats, task IDs, runtime and image. `abl init` writes a complete reference configuration. Never write API keys into YAML.

Exports contain every persisted trial field, nested verifier evidence and a measurement-source map. JSON preserves native nulls and types. CSV uses an empty cell for null, JSON for nested objects and booleans, and a leading apostrophe for strings beginning with spreadsheet formula characters. Trial artifact directories contain `trace.jsonl`, opaque `workspace.tar`, `verifier.json` when verification ran, and final `trial.json`. Treat tar contents as untrusted; do not extract them into a sensitive directory.
