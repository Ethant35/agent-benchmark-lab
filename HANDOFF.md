# Agent Benchmark Lab handoff
Author: Ethan

Repository: https://github.com/Ethant35/agent-benchmark-lab
Local path: /Users/ethantarnarider/Documents/ChatGPT/Open source/agent-benchmark-lab
Branch: codex/build-agent-benchmark-lab
PR: https://github.com/Ethant35/agent-benchmark-lab/pull/1

## Goal state
ACTIVE: deterministic acceptance is complete. Last remaining gates are publishing the accepted code (merge, tag v1.0.0, GitHub release), verifying the remote release, and stopping local services. No live provider validation is claimed. Credential-free framework release is permitted by the specification.

## Completed and verified
Python Typer/Pydantic CLI, provider-neutral runner, constrained container lifecycle, OpenRouter/compatible adapter, SQLite reports/exports, React/TypeScript dashboard, twelve independent tasks across six categories, documentation, and real E2E harnesses.

BL-01–18 PASS. Installed-wheel CLI/container run passed all sixteen non-browser deterministic scenarios. Playwright passed 3/3 browser tests. Fresh clone install with frozen Python/npm locks passed. Final corpus passed 12/12 after strict type checks. Original unsolved fixtures were rejected 12/12. All benchmark containers and volumes were cleaned after trials. Details and exact transcripts: ACCEPTANCE.md and evidence/.

BL-19–22 BLOCKED_EXTERNAL: no authorized OpenRouter credential. Live model integration unverified. Actual missing-credential trial persisted as BLOCKED_EXTERNAL; zero provider requests. Docker compatibility is implemented but only Podman was exercised.

## Environment / processes
Podman 6.1.4 installed. Dedicated machine `abl-benchmark`: 2 CPUs, 2 GiB RAM, 12 GiB virtual disk. Python base image content ID 7efd45553a98be3d940b73600550669831c0be34f30c521159e7030a91fcdee6. Do not delete unrelated containers or machines.

At this milestone, VM is held by exec session 72486; final dashboard server runs in exec session 26362 on port 8765 against `.abl/release-acceptance`. Stop both after release verification. All Luna child workers finished and were interrupted. The supported account usage checker runs every 45 seconds in persistent functions cell 8; stop it after work stops. Latest delivered usage was 16% used; no exhaustion observed. Stop at 100% used and never buy credits or switch accounts to continue.

## GitHub safeguards
Exact origin verified. Repository Actions permissions are disabled; API reports zero workflow runs. No workflows added. Recheck permissions before every push/merge/tag/release. No ~/.codex/config.toml changes. Parent repository and other project checkouts untouched.

## Evidence / precise recovery
Canonical local roots: `.abl/release-acceptance` (29 records including one blocked credential probe), `.abl/final-corpus` (12 PASS), `.abl/unsolved-suite` (12 expected FAIL). Clean Python 3.12 wheel environment `.abl/clean-install`; fresh source clone `.abl/clean-source`. Opaque workspace archives and traces are retained under each root's artifacts/.

```sh
cd '/Users/ethantarnarider/Documents/ChatGPT/Open source/agent-benchmark-lab'
git status
gh api repos/Ethant35/agent-benchmark-lab/actions/permissions
gh pr view 1
cat ACCEPTANCE.md
# If publication has not yet happened, finish the accepted PR and release; do not rerun live tests without credentials.
gh release view v1.0.0 --repo Ethant35/agent-benchmark-lab
# To use the local application later:
podman machine start abl-benchmark
uv run abl dashboard --root .abl/release-acceptance
```
