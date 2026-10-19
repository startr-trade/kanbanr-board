# Defect: marker resolution inside worktrees

The `.kanbanr` marker stores the board path relative to the marker file. A git worktree created inside the repository (for example `.claude/worktrees/<name>`) checks out its own copy of the marker, so the relative path resolves from the worktree and points at a folder that does not exist. Board commands and the commit hook then fail or need `KANBANR_DATA_DIR` set.

Fix: when the marker is inside a git worktree, resolve its relative `data_dir` against the main worktree (`git rev-parse --git-common-dir` gives it), unless the resolved path exists.

## Design

### Change
- `api/crates/kanbanr-core/src/project.rs`, `FoundMarker::data_dir(&self, home) -> Option<PathBuf>`.
  It resolves the marker's `data_dir` against the marker's folder, as today.
  - If that path does not exist, the value is relative, and the marker's folder is inside a
    **linked** git worktree, it resolves the same relative path from the **main** worktree's
    equivalent folder instead, and uses that when it exists.
  - Otherwise it keeps today's answer, so `where` and the "no board here" message are unchanged.
- New private helper:
  `fn main_worktree_equivalent(dir: &Path) -> Option<PathBuf>`. It uses
  `git2::Repository::discover(dir)` and requires `repo.is_worktree()`. The main worktree's root is
  the parent of `repo.commondir()` (a non-bare main repository's `.git`). The result is that root
  joined with `dir` relative to `repo.workdir()`. Paths are normalized with `project::normalize`,
  so symlinked temp folders compare equal.
- Absolute and `~` paths never fall back. `KANBANR_DATA_DIR` and `--data-dir` still win, as before.

### Test plan
| Req | Test |
|---|---|
| R-1 | `marker_resolves_from_linked_worktree` (local_mode.rs): a repo with a marker pointing at `../shop.kanbanr`; `git worktree add .claude/worktrees/w1`; `kanbanr board` and `where` from inside the worktree find the main board; from the main checkout, unchanged; a worktree of a repo whose board really is missing still says "no kanbanr board here" |
| unit | `project::tests::linked_worktree_falls_back_only_when_missing` |

### Implementation tasks
1. project.rs: the helper and the fallback in `FoundMarker::data_dir`, plus the unit test. Depends
   on: none.
2. local_mode.rs: the R-1 integration test. Depends on 1.
3. CHANGELOG ("Fixed") with the docs sync; `make ci`. Depends on 2.

### Affects docs
docs/src/using/installing.md, if it mentions worktrees (otherwise none); CHANGELOG.
