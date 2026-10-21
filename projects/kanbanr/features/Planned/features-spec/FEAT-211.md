# Release 0.2.1

## Why
Two fixes found after 0.2.0 are finished on `sprint/SP-001`:
[FEAT-209](/p/kanbanr/feature/FEAT-209) (a diagram opened from the book drew as black boxes) and
[FEAT-210](/p/kanbanr/feature/FEAT-210) (the release's install check misread the monitor's relative
bundle path). The user chose a patch release, 0.2.1 (21 Oct 2026). The release workflow refuses a
tag unless the workspace version, the VS Code extension's version and `docs/src/releases/<tag>.md`
all name it.

## Design

### Change
- Version `0.2.1` in `api/Cargo.toml` (and `api/Cargo.lock`), `editor/vscode/package.json`,
  `web/package.json`, `.claude-plugin/plugin.json` (and their lockfiles).
- `docs/src/releases/v0.2.1.md`: what's fixed (the two items, plus the release workflow now
  publishing `mermaid-lint`, which is already on crates.io); listed in `docs/src/releases/index.md`
  and `docs/src/SUMMARY.md`.
- `CHANGELOG.md`: `[Unreleased]` becomes `[0.2.1] - 2026-10-21`, with the two fixes added under
  Fixed; compare links; `tools/docs/sync.sh`.
- On an item branch from `sprint/SP-001`; Completed merges it there (git model).

### The release flow for 0.2.1 (the user's, 21 Oct 2026)
1. This item merges into `sprint/SP-001`.
2. The user promotes v0.2.1 to **candidate**: `release/v0.2.1` is made from `sprint/SP-001`.
3. Main is fast-forwarded to `release/v0.2.1` by hand (`git merge --ff-only`), standing in for the
   release stage [FEAT-212](/p/kanbanr/feature/FEAT-212) will add.
4. The user pushes main and waits for CI.
5. The user promotes v0.2.1 to **production** (the cut): the tag goes on the release tip, which is
   main; the fast-forward has nothing left to do.
6. The user pushes the tag.

### Test plan
| Req | Test |
|---|---|
| R-1 | `manual: release.yml's tag checks pass for v0.2.1` (version, extension version and notes file, run locally) |
| R-2 | `cargo test --workspace` and `npm run check:docs` after the bump |

### Implementation tasks
1. Versions; notes; index, SUMMARY; changelog heading and sync; checks. Depends on: none.

### Affects docs
docs/src/releases/v0.2.1.md, docs/src/releases/index.md, docs/src/project/changelog.md.
