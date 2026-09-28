## Problem

The session-summary hooks built under FEAT-099 (`session-summary.sh`, `summarise_session.py`) live in `.claude/hooks/`, and `/.claude/` is gitignored wholesale. They are unversioned, exist on one machine only, and no other kanbanr project gets them. The blanket ignore also hides `.claude/commands/`, which is worth sharing, while the parts that really are machine-local (`worktrees/`, `settings.local.json`, `__pycache__`, the generated `settings.json` with absolute paths) are what the ignore is actually for.

## Behavior

- The two scripts move to `skill/kanbanr/hooks/`, shipped with the skill and the plugin.
- `kanbanr hooks install` registers them for PostCompact, SessionEnd and SessionStart alongside the existing hooks; `hooks status` reports them, and `uninstall` removes them. They stay best-effort: a missing `python3`, `jq` or `claude` means no summary, never a failed hook.
- `.gitignore` narrows from `/.claude/` to the machine-local parts: `worktrees/`, `settings.local.json`, `settings.json` (generated per machine by `hooks install`), `__pycache__/`.

## Out of scope

- Changing what the summaries say or where they are saved.