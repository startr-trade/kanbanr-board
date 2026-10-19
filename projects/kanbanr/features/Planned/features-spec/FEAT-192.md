# Defect: marker resolution inside worktrees

The `.kanbanr` marker stores the board path relative to the marker file. A git worktree created inside the repository (for example `.claude/worktrees/<name>`) checks out its own copy of the marker, so the relative path resolves from the worktree and points at a folder that does not exist. Board commands and the commit hook then fail or need `KANBANR_DATA_DIR` set.

Fix: when the marker is inside a git worktree, resolve its relative `data_dir` against the main worktree (`git rev-parse --git-common-dir` gives it), unless the resolved path exists.
