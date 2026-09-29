## Problem

In a repository with no commits, `scm::default_branch` finds no remote head, no `init.defaultBranch` and no existing main/master, and answers `main` — while HEAD is an unborn `master` (git's own default). Reproduced on a scratch repo: `kanbanr git status` reports `default: main`; the first commit on `master` is refused because the branch names no item; `kanbanr start` then says it branched `from main`, a branch that does not exist. A new project set up through the interview (katalog) cannot make its first commit without `--no-verify`.

## Behavior

- In a repo with no commits, the default branch is the unborn HEAD's name.
- The pre-commit check allows the **root commit** on the default branch: nothing can branch from a repository with no commits, so the first one has to land there.
- `start` in a repo with no commits refuses with the one-line fix (make the initial commit first) rather than branching from nothing.

## Out of scope

- Renaming branches for the user.