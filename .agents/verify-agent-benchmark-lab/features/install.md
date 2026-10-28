# Install and prerequisites
Author: Ethan

## Sub-features
Installed wheel, packaged dashboard/corpus and container readiness.

## How to get to it (user POV)
Install the wheel in Python 3.12, then run `abl check` in Terminal.

## Driving it with CLI
Follow SKILL.md's build/install steps. Compare installed files with wheel bytes.
Run `abl check` before and after starting the named existing VM when it was stopped.
`tests/test_guided.py` checks missing engine and missing image guidance without mutation.

## Gotchas
The existing VM and image do not prove fresh Mac installation. Do not initialize,
reset or remove a VM just to exercise that branch. No Node is needed by the installed
wheel; Node is required only to build or test the dashboard in the development checkout.
