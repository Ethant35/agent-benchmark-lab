# Dashboard usability qualification

Author: Ethan

## Changes

- First-use view stays focused on saved benchmark results. A replayable Quick start panel gives a free reference command returned for the current workspace. It explains that optional model runs need an explicit provider/model configuration and can cost money.
- A workspace with no runs has a distinct empty state. A valid filter with no matches offers Clear filters. An empty page with records outside its offset has separate guidance. API errors remain errors and do not also render an empty state.
- The dashboard waits for its workspace ID before loading persisted filters or results. If that lookup fails, it shows a retry and does not guess a results path. Filters and page offset restore from local storage scoped by the opaque workspace ID; URL state takes precedence. On a plain return without query filters, the last opened trial evidence restores by ID even when the trial is outside the current page. Closing it clears the remembered detail.
- Visible pages poll every three seconds. Polling pauses while hidden or while filters load, and it does not replace loaded results with a loading screen. Filter changes show a compact loading state. The UI reports active run status and directs cancellation to the CLI terminal, where process-group cleanup applies.
- Trial rows and details label reference controls, model benchmarks, and versioned integration checks. Agent configuration labels use the actual `streaming`, `reasoning_effort`, and `spend_limit_usd` fields; the last is called a reserve rather than a billed cap. Reference controls show their `reference_mode` and omit non-streaming/reserve fields. Configuration and corpus hashes remain visible when their sample trials are outside chart limits. Summary scope and independent comparison groups are stated when multiple contract/configuration groups are selected.
- Cost display keeps at least four and up to twelve fractional digits. Unknown final costs and known subtotals remain distinct.

## Verification

- `npm run build --prefix dashboard`: passed (TypeScript and Vite production build).
- `ABL_BASE_URL=http://127.0.0.1:8771 npm run test:e2e --prefix dashboard`: 15 passed. Axe reported zero violations in the tested main and detail views. Coverage includes workspace lookup failure/retry, delayed identity plus saved-filter/evidence restoration, empty vs no-match states, active-run polling, compact filter loading, stale-page recovery, actual config-field labels, exact small-cost rendering, groups outside chart samples, 320px layout, details, pagination, exports, and API retry/error paths.
- Browser served from source-built static files and the local API on loopback against the existing `.abl/hardening-regression-v2` result directory. No provider request or container run was started by these checks. The dashboard server was stopped after verification.
- A 390px mobile capture was inspected. Automated viewport checks cover 320px, 390px, and 640px. No unfamiliar-user, assistive-technology, or OS zoom study was performed.

## Limits

The dashboard is read-only. It does not launch or cancel runs. Cancellation remains a terminal CLI action; status polling reflects persisted run status. Quick start uses the CLI-provided absolute command for the active results root, so the displayed root can contain a local path. The browser stores only filters, page offset, and the last opened trial ID under a workspace-hash key. A query-string state takes precedence over saved state and does not restore the saved evidence drawer. The browser does not store evidence payloads or credentials. Integration labels identify the versioned task; they do not imply that a longer integration deadline changed a historical benchmark score.
