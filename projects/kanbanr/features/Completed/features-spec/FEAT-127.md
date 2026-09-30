## Problem

The Claude Code PreToolUse guard (`kanbanr git guard`) decides against the repository of the session's working directory. A Bash command of the form `cd other-repo && git commit …` is judged as a commit in the session's repository: preparing the public repository, a root commit on a fresh `main` in `kanbanr-public` was refused as "would commit straight to master" — the branch of the other folder. The workaround was to run the commit from a script, which the guard does not see.

## Behavior

When the command changes directory before `git commit` (`cd <dir> && …`, or `git -C <dir> commit`), the guard judges the repository at that directory: its branch, its default branch, whether it has commits, and its board. If it cannot resolve the directory, it says nothing (the git hooks in that repository still decide).

## Out of scope

- Commits made by scripts the command runs.