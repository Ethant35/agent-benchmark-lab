# Interruption and recovery
Author: Ethan

## Sub-features
Signal handling, retained attempts, recovered schedule outcome and exit compatibility.

## How to get to it (user POV)
Interrupt an active Terminal run, then use `abl start --root <directory> --resume <run-id>`.

## Driving it with CLI and Playwright
The helper runs the existing usability journey with `--recovery-mode success`.
It waits for the real container, sends SIGTERM, requires INTERRUPTED and no cleanup
errors, then resumes the same unchanged configuration to PASS. Verify the old attempt
document is unchanged, the schedule reports 1/1 with one recovery, and attempt metrics
remain 1/2. The CLI must still exit 1. Inspect the saved output and API evidence.

## Gotchas
A run marked COMPLETED means scheduling ended. It does not erase failed or interrupted
attempts. No manifest means unknown schedule context. Latest RUNNING, changed identities
and unattempted slots cannot count as passes. Keep unknown costs and known subtotals
distinct. The default timeout recovery control remains available and must not be weakened.
