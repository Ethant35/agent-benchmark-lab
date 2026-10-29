# Qualification constraints
Author: Ethan

These are release gates for the active local-user readiness effort. Historical
v1.0.1 evidence remains valid only for its exact sources and environment.

## Supported target

Single-user local benchmarking on macOS Apple Silicon, Python 3.12 and a dedicated
Podman Linux VM. The dashboard binds to loopback and reads the operator's result
directory. OpenRouter chat completions, tools, streaming and nonstreaming are
central supported paths and require real validation after adapter changes.
Docker and other OpenAI-compatible services remain implemented but unqualified
until exercised on their real runtimes. Windows is unsupported because execution
uses POSIX process groups, selectors and file locks. This scope does not make an
unfinished central feature optional.

## Invariants and commands

| Dimension | Required property | Evidence command or gate |
|---|---|---|
| Correctness | All 12 task contracts are explicit, independently checked and versioned; reference passes and unsolved controls fail | Real container corpus acceptance, `tests/test_corpus_contracts.py` |
| Isolation | Candidate code executes only in an isolated container; no credentials, host workspace mounts or network; CPU, memory, processes, output, artifacts and workspace growth are bounded | `tests/resource_e2e.py` plus workspace quota and descendant cleanup cases |
| Spending | Request and token caps apply before transmission; unknown outcomes block further spending; measured, estimated and missing costs remain distinct | Provider boundary tests and bounded live generation/key reconciliation |
| Recovery | Resume preserves history and rejects changed contracts; interruption cleans owned resources; malformed IDs cannot select paths | Real cancellation/kill/resume tests plus ID and corpus mismatch tests |
| Persistence | New and old result stores open without data loss; connections close; backup and restore preserve records; disk and corruption errors are actionable | Store tests and fresh/upgrade qualification |
| API | Additive interfaces, bounded list pages, complete summary denominators, explicit chart sampling; read-only local access | `uv run --frozen python -m pytest tests/test_api_history.py` |
| UI | Real persisted-data flows, keyboard detail navigation, empty/error/loading states, 320px layout and accessibility checks | `npm run test:e2e --prefix dashboard` against a real API |
| Dependencies | Frozen installs reproduce reviewed dependencies; reachable critical/high findings resolved before release | Frozen Python/npm installs and native audit with recorded triage |
| Privacy | No credentials in saved evidence; diagnostic exports omit task/provider payloads; local retention and deletion are documented | Sanitized evidence inspection and privacy/recovery tests |
| Packaging | Clean wheel install, upgrade data, installed corpus and static bytes match qualified source; release download hashes match | Fresh environment and downloaded-asset comparison |
| Operations | Actions disabled; no workflows, global hooks or user config changes; no usage guard required | Repository permissions check; instruction 2026-10-29 removes both prior usage stops |

Run `uv run --frozen python -m pytest -q` for small/local integration tests and
`npm run build --prefix dashboard` for the UI build. These do not substitute for
container, browser, live-provider or packaged-install gates.

## Floor

- Tests: Do not delete assertions, skip failing cases or weaken verifiers to obtain a pass. Version and document corrections to an invalid task contract.
- Checks: Do not suppress findings or replace a failed external check with an assumed pass.
- Scope: Do not remove central capabilities to claim readiness.
- Evidence: Label controlled fixtures, reference runs, real provider runs and unknown values separately.
- Release: Publish only after every applicable gate in `READINESS.md` has current evidence.

No numerical coverage quota is imposed. Test meaningful boundaries and failure modes.
Exceptions: none approved.
