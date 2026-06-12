# Plugin packaging & distribution (P1)

Ship kanbanr's Claude integration as a Claude Code PLUGIN so one `claude plugin install` delivers the skill + enforcement hooks (+ optional slash commands) together.

## Scope
- `.claude-plugin/marketplace.json` + plugin manifest bundling skill/kanbanr/ (SKILL.md + hooks/).
- Hook commands use `${CLAUDE_PLUGIN_ROOT}` paths (no hardcoded absolute paths).
- Cross-platform hooks: PowerShell variants (per-hook `shell: powershell`) so SessionStart/Stop work on Windows (bash today = Linux/macOS or Git Bash/WSL only).
- The `kanbanr` binary ships via crates.io / GH releases; the plugin drives it.
- Document `claude plugin marketplace add <repo>` + install in README/OPEN_SOURCING.