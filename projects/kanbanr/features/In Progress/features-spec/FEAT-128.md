## Problem

A new board's first commit is authored `kanbanr <kanbanr@local>`, not by the person who set it up. `git::ensure_repo` does two things on a fresh data folder before any identity is known:

- it writes the placeholder `user.name = kanbanr`, `user.email = kanbanr@local` into the repository's own git config, and
- it makes the "initialize data repository" commit with that placeholder.

`kanbanr init --author … --email …` sets the real identity only afterwards, so the first commit is always wrong. Worse, the placeholder is repository-local, so it overrides the user's global git identity: without `--author/--email` (or a later `kanbanr identity`), every later commit is also `kanbanr@local`. `commit_local` and the merge commit fall back to the same placeholder silently. On this project's own board, 53 commits carried placeholder identities and had to be rewritten.

## Behavior

- A fresh data repository gets no placeholder identity in its config.
- The identity is settled before the first commit: `--author/--email` when given, otherwise the user's own git identity (global/system config).
- If no identity can be found anywhere, kanbanr refuses to commit and says how to set one (`kanbanr identity --name … --email …`) instead of committing as a placeholder. This applies to every commit kanbanr makes: writes, the initial commit, and merge commits from a pull.
- A repository that already holds the old placeholder is treated as having no identity, and `kanbanr doctor` reports it with the fix.

## Out of scope

- Rewriting history of existing boards (a user decision; done by hand for this board).
