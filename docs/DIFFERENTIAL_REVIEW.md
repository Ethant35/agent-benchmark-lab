# Lead resolution update
Author: Ethan

The subsequent regression reproduced F-1 on an existing 0755 store. Store now
restricts the root to 0700 on open, preventing traversal to historical evidence
without rewriting it. New trial directories use 0700 and trace creation uses 0600.
`test_legacy_root_becomes_private_without_rewriting_history` passes in the
60-test suite. Run-lock symlink, credential-in-object-key, and known subtotal
regressions also pass. The review snapshot below is retained as historical evidence.

# Differential security and correctness review

Review date: 2026-10-22  
Baseline: `381caf28ec2d73dc6e87d0956ff2afcde986cced` (current `HEAD`; readiness work is uncommitted)  
Scope: dirty production-readiness changes and new runtime module. This report describes the working tree observed at review time, not a committed revision.

## Result

One confirmed medium-severity privacy issue remains in the reviewed snapshot: existing result stores keep permissive directory and artifact modes. A new store test proves privacy only for a newly created root. On this host, the existing regression store is `0755`, its artifact directories are `0755`, and sample `trace.jsonl` and `trial.json` files are `0644`. A second local OS account that can traverse the store can read trial evidence and provider traces.

This does not provide a remote attack path. The dashboard is loopback-only and has trusted-host and foreign-origin checks. The finding requires a separate local account with filesystem access to the result directory. It matters because the code explicitly treats traces, tasks, and provider data as private evidence and hardens newly created database files.

### Finding F-1 — Existing stores retain group/world-readable evidence (P2)

**Evidence:** `abl/store.py:45-52` calls `mkdir(..., mode=0o700)` on the root, but `mkdir` does not change the mode of an already-existing directory. The same code explicitly chmods the database to `0600`, but does not normalize the root or artifact tree. `abl/engine.py:57-58` creates trial/evidence directories without restrictive modes, and `abl/engine.py:66` opens `trace.jsonl` using the process umask. The observed existing root/artifact directories were `0755`; trace and trial files were `0644`. `tests/test_recovery_privacy.py:15-21` checks only a fresh root, so this upgrade case is not covered.

**Preconditions and impact:** A deployment already has a result root created by the earlier version (or another process with a permissive umask), and another local account can traverse that path. That account can read persisted trial JSON and raw trace events, which may contain task content, tool arguments/results, and provider output. No candidate-controlled input is required. This is local cross-account disclosure, not host compromise or network access.

**Remediation:** Normalize existing store and evidence directory permissions on open, with symlink/type checks, and create trace/trial evidence files with owner-only permissions independent of umask. Add a regression test that constructs an old store with permissive root/artifact modes, opens it through the current store/runner path, and verifies the resulting directory and file modes. Avoid chmod-following attacker-controlled symlinks.

## Review coverage and evidence

I compared the baseline-to-working-tree changes, read the full changed provider, store, API, CLI, engine, isolation, and recovery implementations, inspected the added recovery/privacy, provider-boundary, isolation-edge, resume-contract, history/API, and finalization tests, and followed their direct callers. I reviewed the dashboard, corpus-contract, package/config, and handoff changes at diff level. I inspected relevant history and blame for the isolation and artifact-handling paths. The parent is running the project suites separately; I did not execute tests or mutate code as part of this read-only review.

The focused risk review covered provider request/response parsing and redaction, request-pending and partial-cost accounting, resume identity and locking, backup/restore path handling and integrity checks, SQL filtering/pagination, trace reads, loopback API origin/host boundaries, subprocess/container isolation, and evidence privacy. Current tests cover malformed and oversized provider responses, request interruption, symlink evidence reads, backup tampering, lock exclusion, resume compatibility, API pagination, and fresh-store privacy. The permissive legacy-directory case is the confirmed gap above. The `shell` command is intentionally executed inside the disposable container; the host launches the runtime with an argument vector, so candidate shell syntax is not itself evidence of host-shell injection. The API threat boundary is local-user access; no authentication is added because the service is intended for loopback use.

No additional confirmed provider/accounting, recovery, resume, SQL/API, or candidate-to-host isolation vulnerability was established in this bounded pass. This is not a proof of absence. I did not launch containers, contact providers, execute tests, review generated duplicate files (they were preserved separately), or inspect every transitive dependency implementation. The dashboard diff was reviewed for data-flow and interaction changes, but this pass did not perform browser-based accessibility/performance validation.

The reviewed tracked diff passed `git diff --check` against the baseline. Parent-reported fixes to the run-lock symlink/truncation case, credential scrubbing of object keys, and known-spend aggregation were present in the working tree when checked; those observations are treated as fixed, not open findings.

## Changed paths in scope

Tracked: `.gitignore`, `HANDOFF.md`, `abl/api.py`, `abl/cli.py`, `abl/engine.py`, `abl/isolation.py`, `abl/models.py`, `abl/providers.py`, `abl/store.py`, `corpus/feature-order-filter/task.yaml`, `corpus/multistep-document-index/task.yaml`, `corpus/multistep-ledger/reference.json`, `corpus/multistep-ledger/task.yaml`, `corpus/multistep-ledger/verifier/check.py`, `corpus/navigation-config/reference.json`, `corpus/navigation-config/task.yaml`, `corpus/navigation-config/verifier/check.py`, `dashboard/e2e.spec.ts`, `dashboard/package-lock.json`, `dashboard/package.json`, `dashboard/src/main.tsx`, `dashboard/src/style.css`, `pyproject.toml`, `uv.lock`.

New/untracked: `AGENTS.md`, `CONSTRAINTS.md`, `READINESS.md`, `abl/recovery.py`, `corpus/navigation-config/verifier/contract.py`, `docs/CORPUS_QUALIFICATION.md`, `docs/SECURITY_REVIEW.md`, `docs/SKILL_USE.md`, `docs/UI_QUALIFICATION.md`, `evidence/readiness/history-performance-1.json`, `evidence/readiness/history-performance-2.json`, `evidence/readiness/semgrep-initial.json`, `evidence/readiness/semgrep-initial.sarif`, `tests/history_performance.py`, `tests/test_api_history.py`, `tests/test_corpus_contracts.py`, `tests/test_finalization.py`, `tests/test_isolation_edges.py`, `tests/test_provider_boundary.py`, `tests/test_recovery_privacy.py`, `tests/test_resume_contract.py`, and `tests/workspace_e2e.py`. Generated duplicate files preserved under `.abl/preserved-duplicate-files-20261022` were not treated as source changes.

## Snapshot identity

Baseline commit: `381caf28ec2d73dc6e87d0956ff2afcde986cced`.  
Working tree: dirty, no new commit.  
Review-snapshot fingerprint: `64b508a627cdcdcede72fe5342c140ac1fd063bc9ef65dcf3a0502223070b3fa` (SHA-256 of the baseline diff bytes for tracked paths plus working bytes for untracked paths, with path delimiters; 46 paths; this report excluded).  
The files and line references above refer to the snapshot reviewed on 2026-10-22. The root agent may change implementation after this report; rerun the focused permission check and update this report if the finding is fixed.
