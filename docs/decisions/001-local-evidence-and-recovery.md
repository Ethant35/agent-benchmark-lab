# ADR-001: Preserve bounded local evidence and immutable run identity
Author: Ethan
Date: 2026-10-22
Status: Accepted.

## Context

Long histories made the dashboard load all evidence bodies. Legacy resumes trusted
mutable task/image names. Interrupted requests could lose generation identity and
make known partial charges look like complete cost. Unbounded workspace growth and
permissive old root permissions weakened the intended local isolation boundary.

## Decision

Keep SQLite and the read-only loopback API. Add compact paginated rows, complete filtered
summaries and an explicitly sampled 2,000-record chart view. Preserve the legacy routes.
Use typed response envelopes and parameterized filters. Include the corpus manifest
hash in comparison groups so changed contracts and unknown legacy identities stay separate.

Pin the inspected image and persist ordered task manifests. Refuse unsafe IDs and changed
or missing manifests. Use additive tables, shared run/exclusive backup locks, private
roots and a verified offline backup into a new destination. Keep historical trial JSON
unchanged. Record intent and observed generation identity before completing a request;
show known subtotal while final cost is unknown. Do not retry uncertain paid work.

Use a 128 MiB / 16,384-inode tmpfs workspace kept alive by a dedicated sleep-only
container, plus bounded host output/archive collectors. Fail if this boundary cannot
be created. Verify independent task outcomes and clean only owned resources.

## Alternatives and tradeoffs

A hosted database/authentication service would expand the single-user local scope.
Loading full JSON for each page wastes memory and transfer. Removing legacy APIs would
break existing clients. Pagination and a bounded matrix add navigation and omit some
chart detail; labels disclose this, and full exports remain available.

Inferring a legacy manifest would falsely certify unchanged inputs. Refusing legacy
resume is inconvenient, so old stores remain readable and original-version recovery is
documented. A full artifact chmod rewrite would touch historical files; restricting the
root closes traversal instead. Online backups would need a stronger artifact snapshot
protocol, so the supported command requires an idle store.

An unbounded disk volume would let candidate code exhaust runtime storage. Tmpfs makes
the workspace ceiling explicit but needs a keeper container and actual runtime checks.
Container isolation still depends on the runtime/kernel; hostile users should use a
disposable dedicated VM. Docker remains unqualified for this path.

## Evidence

See READINESS.md, tests/test_resume_contract.py, tests/test_recovery_privacy.py,
tests/test_api_history.py, tests/resource_e2e.py and evidence/readiness/. Live integration passed on a separately versioned 120-second task copy; original
30-second benchmark failures remain unchanged.
