# Agent Benchmark Lab handoff
Author: Ethan

## Completed release
Goal: COMPLETE for the explicitly permitted credential-free v1.0.0 framework release.
Repository: https://github.com/Ethant35/agent-benchmark-lab
Release: https://github.com/Ethant35/agent-benchmark-lab/releases/tag/v1.0.0
Release commit: 3a66b183aba2cf55fe7f747a69b490c59aee74b0
Merged PR: https://github.com/Ethant35/agent-benchmark-lab/pull/1
Local path: /Users/ethantarnarider/Documents/ChatGPT/Open source/agent-benchmark-lab
Current branch: main. A documentation-only handoff commit follows the immutable release commit; the v1.0.0 tag is unchanged.

## Verified result
BL-01–18 PASS. Real installed-wheel CLI/container acceptance, fresh clone installation, three Playwright browser tests, final twelve-task corpus (12/12 PASS), twelve unsolved-fixture controls (12/12 correctly FAIL), persisted exports, denominator checks, timeout/cancellation/resume and isolation checks passed. ACCEPTANCE.md and evidence/ contain exact commands, outcomes and source records.

The wheel, source distribution and SHA256SUMS.txt are published. Downloaded release assets match both the published checksums and local build bytes. Wheel code/task bytes match verified sources. Author metadata is Ethan; bundled dependency copyright/license notices are preserved.

BL-19–22 remain BLOCKED_EXTERNAL: no authorized OpenRouter credential was available. **Live model integration unverified.** No provider requests or fake provider responses were used. OpenRouter/compatible adapters are implemented, but live tool/streaming/usage behavior and nonzero provider-cost accounting await those real tests. Docker compatibility is implemented; local execution used Podman only.

## Isolation and cleanup
Podman 6.1.4 is installed. Dedicated `abl-benchmark` VM: 2 CPUs, 2 GiB RAM, 12 GiB virtual disk. VM and dashboard server are stopped; port 8765 is clear. All benchmark containers and volumes were removed, all Luna workers were interrupted on completion, and the VM holding process was terminated. Source, fixtures, SQLite results, opaque archives and traces are retained.

The supported account usage checker ran every 45 seconds during work without occupying a Luna slot. Last observed usage before final cleanup: 20% used (80% remaining). No exhaustion occurred. This was a session-scoped tool task, not a durable scheduled automation; it is closed at chat completion. Future work must start its own checker and stop at 100% used, without buying credits or switching accounts.

GitHub Actions remains disabled at repository level; zero workflow runs were verified after publishing. No workflows or ~/.codex/config.toml edits were made. Parent repository and other project checkouts were not modified.

## Exact next-session commands

```sh
cd '/Users/ethantarnarider/Documents/ChatGPT/Open source/agent-benchmark-lab'
git status
gh release view v1.0.0 --repo Ethant35/agent-benchmark-lab
podman machine start abl-benchmark
uv sync --frozen
npm ci --prefix dashboard
npm run build --prefix dashboard
uv run abl doctor
uv run abl dashboard --root .abl/release-acceptance
# Open http://127.0.0.1:8765
```

Acceptance roots: `.abl/release-acceptance` (29 records, including one real credential-blocked probe), `.abl/final-corpus` (12 PASS), `.abl/unsolved-suite` (12 expected FAIL). Clean Python 3.12 wheel environment: `.abl/clean-install`; fresh source clone: `.abl/clean-source`. Release files: dist/; re-downloaded verification copies: `.abl/download-verification`.

For live validation, obtain an authorized OpenRouter key, two exact tool-capable model configurations and a provider-side capped budget. Use examples/openrouter.yaml and tests/live_e2e.py. Do not relabel the existing BLOCKED_EXTERNAL scenarios or present reference outcomes as model scores. No additional implementation is required to finish the credential-free release.
