# Backup and restore
Author: Ethan

## Sub-features
Consistent backup, new restore destination, immutable history and artifact fidelity.

## How to get to it (user POV)
Use `abl backup <destination> --root <results>` and
`abl restore <backup> --root <new-results>` with stopped writers.

## Driving it with CLI
The usability journey backs up the first real reference result, restores to a new
directory and compares JSON exports, every database row in runs/trials/run_manifests,
and SHA256 of all artifact files. Run `tests/test_recovery_privacy.py` for privacy,
invalid-path and corrupt-store behavior. Retain evidence after cleanup.

## Gotchas
Compare logical SQLite rows, not database file bytes after checkpointing. Do not
restore over user data. No schema migration is introduced by the presentation work;
historical export regression tests must still pass. A new release or migration would
need its own installed upgrade/rollback qualification.
