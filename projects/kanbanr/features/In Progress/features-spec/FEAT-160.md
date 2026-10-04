# Release v0.1.5: decisions in Claude Code

## Problem
FEAT-159 is on `main` but unreleased: until it ships, scoping and deciding work still need the
browser or a terminal for every verdict. A release also has to carry its
notes page (FEAT-154), or the tag check refuses it.

## Behavior
- The workspace, web app, Claude Code plugin and VS Code extension say 0.1.5; `ears-classifier`
  keeps 0.1.0.
- `docs/src/releases/v0.1.5.md` tells the release's story, and the release-notes index lists it.
- The changelog moves the Unreleased entries under a dated `[0.1.5]` section.
- `make ci` passes; the maintainer pushes and tags `v0.1.5`; the run, the release page, the image,
  the `.vsix`, and the extension's first automatic Open VSX publish are verified afterwards.


## Out of scope
Anything not already on `main`; features stay frozen until 1.0.
