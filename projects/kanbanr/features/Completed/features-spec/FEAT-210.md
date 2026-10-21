# The release's install check misreads the monitor's relative bundle path

## Why
The v0.2.0 release run's three "verify the installer" jobs (debian:bookworm-slim, ubuntu:24.04,
windows-2025) failed on 21 Oct 2026 with `index.html names no bundle`. The binary was right: it
installed, named its commit and served the monitor. Since
[FEAT-178](/p/kanbanr/feature/FEAT-178) the monitor is built with relative paths (Vite `base: "./"`)
so the standalone bundle works under any folder, and the daemon injects `<base href="/">`. Its
`index.html` names `./assets/index-….js`; `scripts/verify-install.sh` and `verify-install.ps1` look
for exactly `src="/assets/…"`. `make ci` runs the scripts against the latest published release,
which was 0.1.7 with `/assets/`, so nothing failed before 0.2.0 was published.

## Design

### Change
- `scripts/verify-install.sh`: read the bundle from `src="/assets/…"` or `src="./assets/…"`.
- `scripts/verify-install.ps1`: the same (`src="\.?/assets/([^"]+)"`).
- No product change; the published v0.2.0 is not re-released.

### Test plan
| Req | Test |
|---|---|
| R-1 | `manual: verify-install.sh passes against the published v0.2.0` (run locally, as make ci does) |

### Implementation tasks
1. Both scripts; run the sh one against v0.2.0. Depends on: none.

### Affects docs
None.
