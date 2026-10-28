# Return, filter and export
Author: Ethan

## Sub-features
Saved filters, direct links, automatic refresh, keyboard details, charts and downloads.

## How to get to it (user POV)
Reopen the same dashboard, filter runs or tasks, choose an attempt, expand comparison
details if needed, and use Export JSON or Export CSV.

## Driving it with Playwright
Run the helper against the installed candidate. Existing browser tests check real
saved rows and export downloads, filter persistence, automatic refresh, keyboard
focus, mobile width and axe accessibility. Fixture tests cover loading/API failures,
large histories, partial costs and legacy context. Open the comparison disclosure
before checking attempt metrics and charts.

## Gotchas
The run outcome panel identifies one selected or latest matching run. Attempt metrics
and export rows cover the active filters, which can span several runs. Chart samples
are not full-history denominators. The API remains read-only and bound to loopback.
