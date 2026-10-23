# Dashboard qualification
Author: Ethan

The initial source snapshot passed four Playwright tests against the Python 3.12 API and
historical real `.abl/hardening-regression-v2` records. The fourth test substitutes
a controlled 250-row API fixture to exercise pagination and large evidence content;
it is not a provider or live API integration result.

Verified: same filters/summary values as persisted API, CSV/JSON downloads, cross-run
filtering, details and actual verifier text, Escape, return focus, all evidence text
tab stops, forward/reverse focus wrapping, replayable onboarding, local dismissal
persistence, narrow viewport width, and axe checks on main view and dialog.

Reproduced then fixed: Reference label contrast (4.34:1 on its background), a matrix
scroll region without keyboard focus, native dialog tab escape to browser chrome,
return focus attempted while the background remained inert, and a header overflowing
320px after the help label expanded. The earlier test incorrectly expected Tab to
skip evidence text; the corrected test checks every evidence tab stop and both wraps.
No assertion was removed to conceal a failing behavior.

Screenshots: `dashboard/test-results/dashboard.png` and `dashboard-mobile.png`.
Mobile screenshot inspected locally; no overall page overflow, tables scroll inside
their regions. Very long metric labels should receive a final mobile readability pass.

## Skill review findings

`dashboard/src/main.tsx:73` — failed detail fetch previously showed a compact row as
if evidence were loaded; now reports the fetch error. Loading state and a retry path
specific to details remain to be checked.

`dashboard/src/main.tsx:102` — matrix was not keyboard-scrollable; now a named,
focusable region. `dashboard/src/style.css` — Reference label contrast repaired.

Current Web Interface Guidelines were fetched from the Vercel primary source on
2026-10-22. Still to assess: URL-synced filter/page state, skip navigation, number
format consistency, very large task/configuration matrices, and explicit empty,
request-error, reduced-motion and zoom scenarios. No hosted analytics is introduced.

React best-practices skill (`react-best-practices/SKILL.md`, advertised name
`vercel-react-best-practices`) and `async-parallel`/`client-localstorage-schema`
rules reviewed: independent page and overview requests run together; only a versioned
dismissal flag is stored, guarded against storage errors. No credentials or result
payloads are stored in browser storage. Server/Next.js-only rules do not apply.

The worker read Impeccable context/Operate/craft floor/onboarding/audit/critique/harden/
polish references and preserved the existing stack. Its engine critique was not run
because it required additional agents outside the assigned worker limit. Final
manual design assessment and complete skill evidence are still required.

## Resume pass — 2026-10-22

The dashboard now initializes run, provider, model, task, and page offset from the
query string and updates the URL as those values change. A copied filtered URL
restores the same controls and rows after reload. Invalid offsets are rounded down
to a valid 100-row page. A keyboard-first skip link targets the results main region.

Loading, API failure with Retry, and a valid empty filtered result are covered with
controlled Playwright responses. The persisted-data browser tests still use the
Python API and historical `.abl/hardening-regression-v2` store. The large-history
fixture uses 2,000 chart records with 2,000 distinct tasks/configurations and checks
that the matrix caps itself at 100 tasks by 20 configurations (2,000 cells) with an
explicit disclosure. It checks matrix totals and reloads page 2 from its URL. This is
controlled fixture evidence, not API load or field-performance evidence.

Mobile review found the “Median time to first output” metric title crowded its icon.
It now wraps in a reserved text column. At 320, 390, and 640 CSS pixels, the browser
suite checks that the page does not overflow; 640 pixels represents a 200% zoom
reflow on a 1280-pixel CSS viewport. The 390-pixel screenshot was rechecked after
the change. There is no disabled browser zoom, and the detail drawer honors safe-area
padding and reduced-motion settings.

The task/configuration matrix previously rescanned the entire chart sample for every
cell and could expand a 2,000-record unique-task/configuration sample into four
million table cells. It now accumulates counts in one pass, caps the visible matrix at
100 tasks by 20 configurations, and states the omitted counts. The 2,000-record
controlled case passes with 2,000 rendered cells. An uncapped probe stalled beyond
30 seconds and was stopped; it is not treated as a performance benchmark. The capped
case is also not browser profiling.

Current verification: `npm run build --prefix dashboard` passed, and all six
Playwright tests passed against the real local API plus the explicitly controlled
large-history/error-state fixtures. Axe reported no violations on the main view and
detail dialog. The Impeccable detector returned no findings for the changed UI files.
The new E2E file uses `ABL_BASE_URL` to keep this server on port 8766; no test-port
configuration was changed. Additional ` 2` suffixed files in the checkout were
preserved separately by the coordinator and are not canonical dashboard inputs.

Remaining UI limitation: trial rows render a bounded page of at most 100 records,
but are not virtualized. Detail requests still surface through the shared page error
banner, whose wording describes general benchmark loading; a detail-specific inline
recovery message would be clearer. These items remain open for final review.

## Controlled history performance

`tests/history_performance.py` builds 10,000 SQLite records with 12 KiB of evidence
each. It compares baseline Git source `381caf2` with current compact API operations,
alternating order across three observations under Python 3.12.14. All baseline scalar
summary values match; chart sampling is explicit and summary denominators stay complete.

| Median measurement | Baseline | Revised |
|---|---:|---:|
| JSON response bytes | 127,952,195 | 1,256,915 |
| Peak Python allocated bytes | 410,863,740 | 15,910,897 |
| Query plus JSON encoding seconds | 1.047 | 0.391 |

The first compact implementation made three facet scans and measured 1.222 seconds.
That attempt and its limits are retained in `history-performance-1.json`. Combining
facets into one scan produced the revised result in `history-performance-2.json`.
These are synthetic local measurements with warm OS caches and Python allocation
tracking, not real-user field latency. The run-ID index is used by SQLite's query plan.

## Final candidate check

Eight Playwright cases now pass against the clean wheel's actual API on port 8767.
The suite includes real persisted history plus explicitly controlled response fixtures.
Known subtotal/unknown final cost, separate corpus groups and truncated trace warnings
are checked. A new test reproduced a detail-request failure whose Retry only reloaded
the list. The UI now reports the affected task and retries that exact evidence request;
the new regression passes. Build and TypeScript checks pass. Axe remains clear for main
view and detail. The old shared-error-banner limitation is resolved. Bounded 100-row
rendering, no field telemetry and CSS-width rather than actual OS zoom remain limitations.
