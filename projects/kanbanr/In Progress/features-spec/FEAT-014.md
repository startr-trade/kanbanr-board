# VS Code extension (P1)

kanbanr's view is pluggable; ship it as a VS Code extension colocated with the dev.

## Scope
- A board webview inside VS Code that reads the local data folder live (spawns `kanbanr serve` and embeds it, or links kanbanr-core directly).
- Commands/palette: add feature, move, add task, open board, set identity.
- Single runtime, no Docker; bundle the one `kanbanr` binary.
- Future viewers (TUI, etc.) follow the same read-the-folder pattern.