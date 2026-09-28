# Pre-publication secrets sweep

Run before making the repository public (FEAT-024/T3). Every check below was run against the tracked
tree and the full history, not the working directory — an untracked file is not the risk; a committed
one is, and it survives deletion.

**Date:** 2026-09-28 · **Commit swept:** master at the FEAT-081 merge

## What was checked

| Check | Command shape | Result |
|---|---|---|
| Sensitive filenames, tracked | `git ls-files \| grep -iE 'secret\|credential\|\.env\|\.pem\|\.key$\|id_rsa\|token\|security\.yaml'` | none |
| Sensitive filenames, ever added | `git log --all --diff-filter=A --name-only` filtered the same way | none |
| Board data inside the repo | `git ls-files data/` | none — the board is a sibling repository (FEAT-041) |
| Token-shaped strings | `ghp_`, `github_pat_`, `sk-…`, `AKIA…`, `BEGIN … PRIVATE KEY` | none |
| Credential literals | `auth_secret`/`password`/`passwd` assigned a non-placeholder string | none |
| Real email addresses | any `…@…` outside `example.com`, `you@`, package scopes and the project's own support address | none |
| Absolute local paths | `/home/<name>`, `/Users/<name>`, the author's directory names | **one found — fixed** |

## What was found

`skill/kanbanr/hooks/settings.snippet.json` registered both hooks by absolute path, pointing at
`/path/to/kanbanr/…`. Two problems, not one:

1. It publishes the author's directory layout.
2. It had **already rotted** — that path has not existed since the repository moved, so anyone
   following the snippet would have registered two hooks that silently do nothing. A hook that cannot
   run exits 0 by design (ADR-0004), so the failure would have been invisible.

Fixed: the paths are now the placeholder `<PATH-TO-KANBANR>`, and the file leads with the fact that
`kanbanr hooks install` resolves them for you and `kanbanr init` runs it — the snippet is the manual
fallback, not the first thing to reach for. The JSON was re-validated after the edit.

## Deliberately published

- `ci@kanbanr.local` in `api/crates/kanbanr-cli/tests/integration.rs` — a synthetic identity for a
  test fixture.
- `git@github.com` in `docs/OPEN_SOURCING.md` — the standard SSH test host, part of the instructions.
- `/home/<name>/...` in `.claude-plugin/plugin.json` — inside prose explaining that absolute paths are
  what `${CLAUDE_PLUGIN_ROOT}` exists to avoid. Illustrative, not configuration.

## Still the user's to do

Making the repository public, and deciding which board data (if any) ships with it. The sweep says
nothing sensitive is *in* the repository; it does not decide what the project wants to publish.

## Limits of this sweep

Pattern-matching finds shaped secrets — a token with a known prefix, a key with a known header. It
cannot find a credential that looks like ordinary text, and it does not judge whether published prose
reveals something the author would rather it did not. It reduces the risk; it does not retire it.
