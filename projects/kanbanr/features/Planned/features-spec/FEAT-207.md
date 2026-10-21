# Release 0.2.0

## Why
Every planned item for the next release is merged on main, and `make ci` passed over it on 21 Oct
2026 (67 checks). The release workflow refuses a tag unless the workspace version, the VS Code
extension's version and `docs/src/releases/<tag>.md` all name it, so the release needs one commit
that sets them. The user chose 0.2.0 (21 Oct 2026): this release adds features and needs a one-time
board migration, which a 0.1.x patch number would hide; 1.0.0 stays
[FEAT-150](/p/kanbanr/feature/FEAT-150).

## Design

### Change
- `api/Cargo.toml` `[workspace.package] version = "0.2.0"` (and `api/Cargo.lock`);
  `editor/vscode/package.json`, `web/package.json`, `.claude-plugin/plugin.json` version `0.2.0`
  (and their lockfiles).
- `docs/src/releases/v0.2.0.md`: the release notes (what's new, changed, fixed, security, upgrade
  notes with `kanbanr migrate`); listed in `docs/src/releases/index.md` and `docs/src/SUMMARY.md`.
  The index's "features are frozen until 1.0" line says 0.2.0 took the work agreed before 1.0.
- `docs/src/releases/schema-5.md`: "For 0.2.0".
- `CHANGELOG.md`: `[Unreleased]` becomes `[0.2.0] - 2026-10-21`, with a new empty `[Unreleased]`;
  `tools/docs/sync.sh`.
- No code change. The user pushes main, then tags `v0.2.0`; nothing is pushed or tagged by Claude.
- Not in this release: publishing mermaid-lint to crates.io (FEAT-200 T10) needs the release
  workflow's publish job extended; it stays open.

### Test plan
| Req | Test |
|---|---|
| R-1 | `manual: release.yml's tag checks pass for v0.2.0` (the version, extension version and notes file checks, run locally) |
| R-2 | `cargo test --workspace` and `npm run check:docs` after the bump |

### Implementation tasks
1. Versions; notes; index, SUMMARY, schema-5; changelog heading and sync; checks. Depends on: none.

### Affects docs
docs/src/releases/v0.2.0.md, docs/src/releases/index.md, docs/src/project/changelog.md.
