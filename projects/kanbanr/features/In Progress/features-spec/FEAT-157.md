# Release v0.1.4: Completed means proven

## Problem
FEAT-156 is on `main` but unreleased: until it ships, ticking an item's last task can still
complete it with requirements unproven, on every installed kanbanr. A release also has to carry its
notes page (FEAT-154), or the tag check refuses it.

## Behavior
- The workspace, web app, Claude Code plugin and VS Code extension say 0.1.4; `ears-classifier`
  keeps 0.1.0.
- `docs/src/releases/v0.1.4.md` tells the release's story, and the release-notes index lists it.
- The changelog moves the Unreleased entries under a dated `[0.1.4]` section.
- `make ci` passes; the maintainer pushes and tags `v0.1.4`; the run, the release page, the image,
  the `.vsix`, and the extension's first automatic Open VSX publish are verified afterwards.

- The installation chapter says how to install the VS Code extension as it now is: from Open VSX
  (published, with its link) in VSCodium, Cursor and Windsurf, and from the release's `.vsix` in
  VS Code — with a plain `curl` download as well as `gh`. The architecture overview stops calling
  the extension "on the roadmap".

## Out of scope
Anything not already on `main`; features stay frozen until 1.0.
