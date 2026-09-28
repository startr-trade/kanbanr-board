# Defect: three places reconstructed a path the tool already knows

## Problem
The `.kanbanr` marker records where a board lives, and `kanbanr where` resolves it. Three convenience call sites ignored that and rebuilt the path from the repository's folder name instead:

- `Makefile`: `DATA_DIR ?= $(CURDIR)/../$(notdir $(CURDIR)).kanbanr`
- `tools/screenshots/capture.sh`: `$ROOT/../$(basename "$ROOT").kanbanr`
- `docker/docker-compose.yml`: a literal `../../kanbanr.kanbanr`

The derivation held only while a board happened to be named after its repository. Renaming one to `kanbanr-board` broke all three at once, while the CLI — which reads the marker — was unaffected. The convention was being treated as a rule.

## Behavior
- Anything that needs the board asks `kanbanr where`, which reads the marker. The derivation survives only as a fallback for a fresh clone with no CLI installed yet.
- Compose cannot run a command, so the value is passed in: `make docker-up` supplies it, and the file documents `KANBANR_DATA_DIR="$(kanbanr where)"` for a direct invocation.
- Documentation refers to `<name>.kanbanr`, not to this repository's own board name.

## Out of scope
Making compose resolve it by itself, which it cannot do.