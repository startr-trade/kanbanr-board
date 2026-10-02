# The installers can install the VS Code extension too

## Problem
The extension ships with every release (FEAT-152), but installing it is a second, manual step:
download the `.vsix`, then run the editor's install command. VS Code users can't get it any other
way, because VS Code doesn't read Open VSX. The installers already install the matching Claude
Code skill; the editor extension should be just as easy, without being forced on anyone.

## Behavior
- `install.sh --vscode` (or `KANBANR_VSCODE=1`), and `install.ps1` with `$env:KANBANR_VSCODE = 1`
  (or `-VSCode`), also install the extension: the `kanbanr-vscode-<version>.vsix` of the same
  release, verified against `SHA256SUMS`, into every editor found on PATH among `code`, `codium`,
  `cursor` and `windsurf`. `--vscode=codium` names one editor.
- Without the option, nothing is installed into any editor; when an editor is found, the installer
  prints a one-line hint naming the option.
- `kanbanr self-update` updates the extension in each editor that already has `kanbanr.kanbanr`
  installed, as it does the skill.
- The installation chapter documents the option.

## Out of scope
Installing an editor. Managing extensions kanbanr did not install, beyond updating its own.
