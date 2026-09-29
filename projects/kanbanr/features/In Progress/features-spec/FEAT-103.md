## Problem

In a folder with no `.kanbanr` marker and no `$KANBANR_DATA_DIR`, every command that only reads — `whoami`, `board`, `feature list`, `charter show`, `doctor` — creates `./data/projects` as a side effect of resolving the legacy default. Found in the katalog setup: `kanbanr whoami`, run during the plan-mode interview (the phase that must not write), left a `data/` folder in the project that a later session would mistake for a board. `kanbanr where` does not do it.

## Behavior

A read never creates a data folder. When no board resolves and the legacy `./data` does not exist, a read says there is no board here and how to get one (`kanbanr init`, or the marker), and exits non-zero; writes that need a board say the same. An existing legacy `./data` keeps working.

## Out of scope

- Removing legacy `./data` support.