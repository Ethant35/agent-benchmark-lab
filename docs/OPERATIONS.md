# Local operation and recovery
Author: Ethan

## Support boundary

The current qualification target is macOS Apple Silicon, Python 3.12 and a dedicated
rootless Podman VM. Tests used Python 3.12.14 and Podman 6.1.4. Docker and other
OpenAI-compatible endpoints are implemented but not qualified. Windows is unsupported.
Version 1.1.0 passed real streaming/nonstreaming integration on a separately versioned
120-second test contract. Three 30-second benchmark timeouts remain failures. Historical
v1.0.1 live results are separate evidence.

Use a dedicated disposable VM for untrusted code. On macOS, create a Podman machine
only if none exists, start it, then pull `docker.io/library/python:3.12-slim`.
`abl check` reports prerequisite status and safe recovery commands; `abl doctor` retains the legacy JSON diagnostic view.
A missing runtime blocks execution. The image is inspected and pinned for each run.

Source development uses `uv sync --frozen --python 3.12`, `npm ci --prefix dashboard`,
and `npm run build --prefix dashboard`. A release wheel includes the dashboard and
corpus. `uv run abl validate` checks configurations without provider calls. If an
editable development install cannot import `abl.cli`, inspect the environment's `.pth`
file flags. Python skips macOS hidden `.pth` files; this was reproduced in the local
synced workspace. A reinstall may only temporarily clear those flags. Prefer the
release wheel for users, or an unsynced development environment; do not change global
Python or Finder settings as a workaround. This does not affect ordinary wheel imports.

Version 1.2.0 adds `abl start` (one free reference task by default), `abl configure`,
`abl check`, and saved dashboard views. The YAML and JSON-output `abl run` interface
remains available for existing scripts. `abl start --plan` previews configuration
without container setup or provider calls. `--accept-cost AMOUNT` is an explicit
scripted consent option and must equal the configured whole-run USD reserve exactly.
Interactive runs default to declining paid execution. An absent credential is requested
through hidden input after consent and removed from the environment after execution.
No credential value is written to the configuration. See [first use](USABILITY.md).


## Deadlines, costs and interrupted requests

The effective deadline is the smaller of the task and configuration limits. Bundled
tasks allow 30 seconds, including setup, tools and verification. Setting a larger
configuration maximum does not extend the task contract. A slow live model may time
out even if it produces useful output. Do not change an old outcome to PASS afterward.

Set conservative current token prices and request/output-token limits. The local
reserve is an operational estimate, not a hard billing cap. For a hard cap, use a
provider-side capped key. Request intent is persisted before transmission. An interrupted
request leaves unknown total cost, its generation ID when observed, and the known
subtotal from prior responses. Unknown cost stops further spending in that run.
Provider generation/account charges can arrive late. Reconcile those IDs separately;
do not treat an early zero delta as free usage or overwrite original trial measurements.

No request is automatically retried. Resume does not rerun completed slots. New runs
are new spend decisions. Review the original evidence and provider charges first.

## Resume and migration

New runs save an ordered corpus manifest with task versions, file hashes and immutable
image ID. Resume validates its ID before filesystem work and rejects a changed manifest
or configuration. Use the same source/corpus/image to resume. A per-run lock excludes
concurrent resume; shared activity locks exclude backup during execution.

Old result stores remain readable and exportable after the additive schema migration.
Legacy runs without a manifest cannot safely resume in the new version. Preserve them;
use the original installed version and original corpus/image in an isolated environment
if recovery is needed. Never infer the missing manifest from today's files. Upgrading
and exporting a real v1.0.1 record was checked without changing its content.

After a forced process death, inspect only resources labelled `abl.managed=true` and
match the trial ID before cleanup. For current manifested runs, resume reconciles
abandoned containers and incomplete archives. A SIGKILL cannot run cleanup immediately.
Do not remove resources belonging to another run. For legacy RUNNING states, finish
recovery with the original version before using the new offline backup command.

## Backup, restore and rollback

Stop all runs first. Use a new destination outside the source store:

```sh
abl backup ./saved-backup --root .abl/results
abl restore ./saved-backup --root .abl/restored
abl compare --root .abl/restored
abl diagnostics --root .abl/restored
```

Backup uses SQLite's backup API, an exclusive activity lock, database integrity checks,
and SHA-256 hashes for the database and artifacts. It rejects active states, links and
special files. Restore verifies the manifest and only writes a new directory; it never
overwrites an existing store. Partial staging output is removed on ordinary errors.
A killed backup may leave a `.abl-backup-*` staging directory; verify it is inactive
before removing it. Historical `artifact_dir` strings remain original provenance;
the dashboard reads artifacts relative to the selected restored root.

Before upgrade, save a verified backup. To roll back, stop new runs, retain new results,
install the previous wheel in a separate environment, and read a restored copy of the
pre-upgrade backup. Do not downgrade in place over your only copy. No destructive schema
migration is required. Corrupt databases produce an actionable error; preserve the
original bytes and restore a verified backup instead of trying to reinitialize it.

## Privacy and retention

Result roots are owner-only (0700); the database and new traces are owner-only (0600).
Opening a legacy root restricts traversal without rewriting historical evidence. Do
not weaken these permissions or share the root. The loopback dashboard has no remote
authentication and must not be exposed through a proxy or tunnel. Host/Origin checks,
no-store headers and escaped evidence reduce unintended browser access.

Traces, archives and full exports can contain private task/provider content. Provider
credentials are redacted and excluded from containers, but redaction is not a reason
to publish raw evidence. `abl diagnostics` emits operational counts and version only;
it excludes task names, paths, configs and provider bodies. Inspect anything before
sharing it. No analytics, source uploads or remote monitoring are installed.

Retention is local and manual. Keep the database and artifacts together for auditability.
After backup and with writers stopped, move an unwanted whole result root to Trash if
you want recoverability. The application has no automatic purge or secure-erase claim.
Opaque candidate archives are untrusted: never extract them on the host.

## Maintenance

Version 1.2.1 adds a schedule summary without changing attempt-level metrics or saved
records. After interruption and successful recovery, one scheduled task can pass while
the CLI retains its legacy exit code 1 for the interrupted attempt. Use the explicit
schedule counts to assess final task completion; retain the attempt history for reliability
and cost comparisons. Historical task descriptions require a matching manifest, corpus
hash, task version and installed task tree. Missing identity remains unavailable.

To uninstall from the dedicated environment, stop its dashboard and runs, save a backup,
then run `uv pip uninstall --python ~/agent-benchmark-lab/.venv/bin/python agent-benchmark-lab`.
This removes the package; it does not remove separately stored results or the Podman VM.
Keep the environment if you want to reinstall. Retain the database and artifacts together.
Stop the dedicated VM when it has no other work; do not use prune as an uninstall step.

Use frozen dependencies for development; review lockfile changes and run both dependency
audits. Requalify changed execution, provider and storage boundaries before release.
Review a new container image before using it; an image change deliberately blocks resume.
The project's GitHub Actions remain disabled. No global hooks or Codex config changes
are needed. See READINESS.md for current gates and evidence, including partial static
analysis coverage and the separately versioned live integration contract.

To reproduce bounded protocol acceptance after installing a wheel, use
`tests/live_integration_e2e.py --python /path/to/env/bin/python --cli /path/to/env/bin/abl --config-a streaming.json --config-b nonstreaming.json --root .abl/live-integration-new`.
Copy the sanitized configs from evidence/readiness/live-integration/ and supply the
credential only through its named environment variable. The wrapper requires a fresh
root, caps each of three runs to a $0.02 local reserve, and uses a separately versioned
120-second task copy. The bundled 30-second benchmark is never edited. Provider-side
hard limits are still needed for guaranteed monetary caps. This command spends money;
it is not run during installation, ordinary tests or releases.
