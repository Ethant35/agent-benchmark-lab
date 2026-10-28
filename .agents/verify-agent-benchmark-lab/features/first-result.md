# First task and result
Author: Ethan

## Sub-features
Empty workspace, free reference task, progress, verifier outcome and task context.

## How to get to it (user POV)
Run `abl start --root <new-directory>`, accept the free reference plan, then open
`abl dashboard --root <same-directory>` and choose the saved attempt.

## Driving it with CLI and Playwright
The reused usability journey requires bugfix-rounding PASS, provider none, cost zero
and visible progress. The helper checks the installed detail API's verified task
description, expected artifacts and verifier exit 0. The browser suite opens the
attempt by keyboard and checks visible evidence, Escape and restored focus.

## Gotchas
A reference control validates the task contract, not a model score. Never substitute
current task instructions when a saved manifest, version, tree or corpus hash differs.
The unavailable-context branch must retain the saved verifier evidence.
