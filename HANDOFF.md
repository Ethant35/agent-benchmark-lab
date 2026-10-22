# Agent Benchmark Lab handoff
Author: Ethan

Repository: https://github.com/Ethant35/agent-benchmark-lab
Local path: /Users/ethantarnarider/Documents/ChatGPT/Open source/agent-benchmark-lab
Branch: codex/build-agent-benchmark-lab
Goal: ACTIVE. Build, verify locally, and release only after required gates pass.

## Current state
- Exact origin verified. Original MIT license and README retained.
- GitHub Actions repository permissions changed from enabled to disabled and verified before pushes. No workflows will be added.
- Startup usage: 1% used in weekly window. Stop at 100% used; do not purchase credits or switch providers to continue development.
- Python 3.13 and Node 22 available. Installing Podman because no Docker/Podman was found.
- No OPENROUTER_API_KEY in process environment. BL-19–22 BLOCKED_EXTERNAL pending authorized credentials.
- No acceptance scenarios passed yet; no release published.

## Architecture decision
Python Typer/Pydantic CLI, SQLite trial documents, isolated Podman/Docker containers, independent verifier container, built-in tool-calling runner and deterministic reference actions. FastAPI serves persisted data and a React/TypeScript dashboard. Fresh volume per trial; no host workspace bind mounts in agent containers. Hidden verifiers run only after stopping agent containers. All task code executes in containers. Local E2E only.

## Next work
Implement package and bounded task/dashboard assistants, run BL-01–18 and available live tests. Record commands/evidence in ACCEPTANCE.md. Commit, push, attach PR, merge/tag/release only after acceptance.

## Processes / recovery
Homebrew Podman installation may be running. No benchmark or agent containers yet.
Resume with `cd '/Users/ethantarnarider/Documents/ChatGPT/Open source/agent-benchmark-lab'`, `git status`, `cat HANDOFF.md`, `podman info`, and account usage check. Do not change ~/.codex/config.toml or parent repository.

## Implementation milestone (2026-10-22 12:01 Pacific)
- Python package, all CLI commands, SQLite metrics, isolated runner, provider adapter and React dashboard implemented as first draft.
- 12 tasks validate through public CLI. Two bounded Luna workers authored corpus/dashboard; parent reviewing and integrating; no additional agents.
- Podman 6.1.4 installed; `abl-benchmark` VM running with 2 CPU, 2 GiB RAM, 12 GiB virtual disk. Python 3.12-slim image pulled (image ID 7efd45553a98be3d940b73600550669831c0be34f30c521159e7030a91fcdee6).
- `abl validate`: PASS (12 tasks, six categories). Python compileall: PASS. Dashboard production build: PASS. These do not establish full acceptance yet.
- Real CLI/container smoke test started; tests/e2e.py is the reproducible BL-01–18 harness (browser portion separate).
- Active usage checker in persistent functions tool cell checks supported account tool every 45 seconds. Last delivered result 5% used. This checker is session-scoped, not a durable automation. It must be stopped when work stops.
- Live integration unverified, BL-19–22 BLOCKED_EXTERNAL; no credential found or provider calls made.
- Next commands: `.venv/bin/abl run --root .abl/smoke --task bugfix-rounding`, then `.venv/bin/python tests/e2e.py --cli .venv/bin/abl --root .abl/acceptance`. Inspect failures before release. GitHub Actions remains disabled.

## Acceptance progress
- Initial implementation committed as 8ac4efc and pushed. Draft PR https://github.com/Ethant35/agent-benchmark-lab/pull/1 is attached.
- BL-01–05 passed in `.abl/acceptance-v1`. Full suite exposed a reference action bug in feature-order-filter (it rewrote orders.json instead of implementing filter_orders.py); parent fixed it. Full suite rerun required.
- Browser first run found default port mismatch, then a percentage display assertion mismatch; both repaired. Final browser pass still pending.
- Clean wheel installed into `.abl/clean-install` using Python 3.12.14. Corpus installed correctly; static dashboard was omitted by build ignore rules. Build artifacts inclusion fixed; clean wheel recheck pending.
- Podman VM now held by long-running exec session 72486 after removing stale project-owned sockets and repulling the damaged image. No host fallback was used.
- Dashboard server PID 23074, exec session 14542, port 8765, root `.abl/acceptance-v1`. Stop it before final cleanup.
- Supported usage checker remains active, latest delivered usage 10% used.

## Release-candidate verification
- First full reference run found three corpus defects (order-filter action, slugify verifier nested command escaping, navigation explanation matching). All repaired; the subsequent 12-task suite passed in `.abl/acceptance-final`.
- That run passed BL-01–15, then found a CLI report positional-argument mismatch before BL-18. Fixed the public signature to match documented commands.
- Final source now records interrupted tool calls as failures, preserves unknown usage for incomplete provider requests, and counts actual verifier success even if a tool/request budget terminates the loop.
- A rebuilt wheel is being installed into clean Python 3.12 environment. Final acceptance is running from that installed wheel with root `.abl/release-acceptance`.
- Browser E2E passed 2/2 on prior real persisted data. Final browser checks must run against release acceptance data, after switching the local server root.
- No release created or main merge yet. Usage checker still running and no exhaustion observed.
