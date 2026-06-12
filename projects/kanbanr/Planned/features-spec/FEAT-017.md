# Enforcement via Claude Code hooks (P1)

The SKILL.md contract is a soft prompt — followed reliably-ish but not guaranteed. Make it enforceable with harness-run hooks (settings.json), which the model can't skip.

## Scope
- SessionStart hook: run `kanbanr board` + `kanbanr activity`, inject state so Claude recovers from kanbanr, not memory.
- Stop/PostToolUse hook: verify substantive work was reflected in kanbanr this session (a kanbanr write/commit happened); nudge or block otherwise.
- Ship sample hooks + a `kanbanr hooks install` helper and document the altitude: kanbanr tracks the PLAN (features/tasks/specs/decisions); code lives in the project's own git.
- Note: enforcement belongs to the harness (hooks), not the skill prompt.