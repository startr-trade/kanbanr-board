# Release v0.1.6: timestamps as instants; the release waits for CI

## Problem
FEAT-162 (timestamps compared as text, so an item created in the same second as the charter could
escape its gates) and FEAT-163 (the release now refuses a commit that has not passed CI) are on
`main`, with CI green on every platform, but unreleased. A release also needs its notes page.

## Behavior
- The workspace, web app, Claude Code plugin and VS Code extension say 0.1.6; `ears-classifier`
  keeps 0.1.0.
- `docs/src/releases/v0.1.6.md` and the index; the changelog's Unreleased entries move under a dated
  `[0.1.6]`.
- `make ci` passes; the maintainer pushes, waits for CI to go green, then tags `v0.1.6`. The
  release's new CI check confirms it, and the run, the release page, the image and the Open VSX
  publish are verified afterwards.

## Out of scope
Anything not already on `main`.
