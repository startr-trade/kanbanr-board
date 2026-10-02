# Distribute the VS Code extension: on every release, and on Open VSX

## Problem
The extension packages and works (FEAT-014) but is published nowhere. The Visual Studio Marketplace
needs a Microsoft account, and Microsoft blocks creating one for the maintainer's address. Two
channels need no Microsoft account: the GitHub release itself, and Open VSX (open-vsx.org, the
Eclipse Foundation's registry used by VSCodium, Cursor, Windsurf, Gitpod and Theia), whose
`kanbanr` namespace claim is pending.

## Behavior
- Every release attaches `kanbanr-vscode-<version>.vsix`, built from the tag; the extension's
  version is the release's (bumped with the workspace from now on), so the file says which release
  it belongs to, and SHA256SUMS covers it.
- `vsce` is a pinned dev dependency of the extension, not `npx …@latest`.
- The release publishes the same file to Open VSX when the repository variable
  `PUBLISH_OPENVSX` is `true` and the `OVSX_PAT` secret is set; otherwise the step is skipped, as
  the crates.io one is. Publishing a version that is already there counts as success.
- `make ci` builds and packages the extension, so a broken manifest fails locally, not in a release.
- The installation chapter and the extension README say how to install it: Open VSX in VSCodium-
  family editors; the release's `.vsix` (`code --install-extension …`) in VS Code.

## Out of scope
The Visual Studio Marketplace (no account possible now; revisit later).
