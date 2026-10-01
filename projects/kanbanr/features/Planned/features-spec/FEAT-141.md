## Problem

kanbanr is two installs: the program (CLI and monitor, from the release installer) and the skill (from the plugin marketplace, or a clone and `make install-skill`). Each step is friction, and the second has no version tie to the first: a marketplace plugin follows the repository's `main`, so the skill a user gets can describe commands their installed program does not have, or miss ones it does. A user who installs only one half gets nothing — the hooks stay silent without the program, and the setup interview fails at its first command.

## Behavior

- **The program carries its skill**, as it carries the monitor: `skill/kanbanr/` (SKILL.md, the hook scripts and their prompt) is embedded at build time, so the skill always matches the release it ships with.
- **`kanbanr skill install`** writes it to `~/.claude/skills/kanbanr/` (or `$CLAUDE_CONFIG_DIR/skills/`), replacing an earlier copy kanbanr wrote; `kanbanr skill status` reports whether the installed copy matches this program; `kanbanr skill uninstall` removes it. A folder there that kanbanr did not write — a developer's link to a clone — is left alone and reported.
- **The installers run it.** After installing the program, `install.sh` and `install.ps1` run `kanbanr skill install` when the `claude` command is on PATH, and say what they wrote; without it, they print the one command for later. `--no-skill` (and `KANBANR_NO_SKILL=1`) skips it. The installer's "nothing else" promise is reworded to say exactly this.
- **`kanbanr self-update` updates the skill** too, when one kanbanr installed is present.
- **The missing half is named:** the SessionStart hook, finding no `kanbanr` program, says once how to install it; the skill's setup interview checks for the program before anything else.
- The README quick start and the installation chapter become one step: the installer, then "set up kanbanr for this project" in Claude. The plugin stays available for people who manage everything through Claude Code's plugins; the docs say to use one route, not both.

## Out of scope

- Pinning the marketplace plugin to a release (it stays on `main`; the installer route is the release-tied one).
