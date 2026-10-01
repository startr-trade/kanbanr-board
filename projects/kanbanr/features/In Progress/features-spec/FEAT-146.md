# Release v0.1.1: the container image fixes

## Problem
v0.1.0's container image reports `(unknown, built unknown)` and its kanbanr carries no skill
(FEAT-144, FEAT-145). Both are fixed on `main`, but a release ships them. Moving the v0.1.0 tag a
second time would make every installed v0.1.0 report a rebuilt binary under a moved tag, so the fixes
go out as the next version.

## Behavior
- The workspace, the web app and the Claude Code plugin say 0.1.1; `ears-classifier` keeps its own
  0.1.0 (unchanged, and its publish job treats an already-published version as success).
- The changelog keeps v0.1.0 as released on 2026-10-01 and gives the image fixes a `[0.1.1]` section.
- `make ci` passes; the maintainer pushes and tags `v0.1.1`; the release run, the image's
  `--version` and skill, and the archives are verified afterwards.

## Out of scope
The VS Code extension's version, which is published on its own cadence.
