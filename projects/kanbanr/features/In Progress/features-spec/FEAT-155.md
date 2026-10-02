# Defect: the v0.1.2 installer check fails on every platform — inside the checkout

## Problem
v0.1.2 published correctly: every binary, the image, and `kanbanr-vscode-0.1.2.vsix` (its checksum
verifies). On all four installer legs — Debian, Ubuntu, macOS, Windows — the installer worked and
`--version` named 0.1.2 and the tagged commit. Then `scripts/verify-install.sh` (and the `.ps1`)
ran `kanbanr init ci-check --data-dir …` **in the working directory**, which is now the repository
checkout (FEAT-149 checked it out to get the script). The repository commits a `.kanbanr` marker,
so init refused: "this folder already names a board, and init would replace it".

`make ci` ran the same script against the latest release, but from `/` in the container — not from
a checkout — so it passed.

## Behavior
- Both scripts run the monitor check from a fresh empty directory of their own, wherever they are
  started from.
- `make ci` runs the script from the repository root, exactly as the release does, so a dependence
  on the working directory fails locally.

## Out of scope
Re-releasing: the fix ships with the next version.
