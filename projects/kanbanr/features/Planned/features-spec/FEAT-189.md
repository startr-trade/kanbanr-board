# Git model derived from the cadence

With sprints and releases each on or off, a project needs one of four branch topologies. kanbanr should derive it rather than leave it to convention.

| Cadence | Line of integration | Production happens at |
|---|---|---|
| neither | `main` (trunk) | merge to main |
| sprints only | `sprint/<SP>` | sprint close (sprint → main) |
| releases only | `integration` | release cut (release → main) |
| both | `sprint/<SP>` | release cut |

Scope:
- `kanbanr git model` shows the derived model.
- `kanbanr start` branches from the current integration line, not always from main.
- `sprint start` creates `sprint/<SP>`, from main or from the previous unreleased sprint branch.
- Promoting a release to candidate creates `release/<VERSION>` from the integration line (with FEAT-183).
- The commit hook accepts `feat/<CODE>-*`, `fix/<CODE>-*` and `spike/*`. It refuses direct commits on `main` and on integration lines; merges into them must carry `Refs:`.
- Pushing is never automatic.
