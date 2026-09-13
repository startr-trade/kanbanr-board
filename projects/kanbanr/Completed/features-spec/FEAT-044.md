# Install the Claude Code hooks automatically

## Problem
The skill's SessionStart (recover the board) and Stop (record-your-work nudge) hooks only work once they're registered in Claude Code settings, which today is a manual copy-paste from `skill/kanbanr/hooks/settings.snippet.json`. `kanbanr init` neither installs nor mentions them, so most projects run without them.

## Behavior
- **`kanbanr init` registers the hooks automatically** (opt out with `--no-hooks`) and says what it did.
- **Once per machine, not per project:** they go into the user's global Claude Code settings (`$CLAUDE_CONFIG_DIR/settings.json`, default `~/.claude/settings.json`). The scripts act only in folders kanbanr tracks (a `.kanbanr` marker or `$KANBANR_PROJECT`), so nothing is written into the project folder.
- **Safe merge:** existing settings and hooks are preserved in their order; the file is written atomically; invalid JSON is left untouched with a warning.
- **Idempotent:** entries already pointing at the kanbanr hook scripts are not added again. If the kanbanr Claude Code plugin is enabled (it brings its own hooks), nothing is added.
- **Needs the installed skill:** commands point at `<claude config>/skills/kanbanr/hooks/`. If the skill isn't installed there, `init` prints how to install it and run `kanbanr hooks install` later; `init` never fails because of hooks.
- **`kanbanr hooks install | status | uninstall`** for doing it by hand. Windows registers the PowerShell scripts.
