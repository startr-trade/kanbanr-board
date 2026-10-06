# Release v0.1.7: your own process, designed with Claude and shared on the board

## Problem
The process library (FEAT-168 to FEAT-171), four defect fixes (FEAT-167, FEAT-172, FEAT-173,
FEAT-174, the last two security advisories) and the walkthrough guide changes (FEAT-166) are on
`main` with `make ci` passing, but unreleased. They should get real use before 1.0 promises them.

## Behavior
- The workspace, web app, Claude Code plugin and VS Code extension say 0.1.7; `ears-classifier`
  keeps 0.1.0.
- `docs/src/releases/v0.1.7.md` and the index; the changelog's Unreleased entries move under a dated
  `[0.1.7]`.
- `make ci` passes; the maintainer pushes, waits for CI to go green, then tags `v0.1.7`. The run,
  the release page, the image and the Open VSX publish are verified afterwards.

## Out of scope
Anything not already on `main`.
