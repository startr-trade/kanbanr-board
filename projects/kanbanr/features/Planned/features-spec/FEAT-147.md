# Release v0.1.2: features frozen until 1.0

## Problem
The product is to be frozen: no new features until 1.0.0, only fixes and the readiness work. Nothing
says so yet, and the VS Code extension's packaging fix (FEAT-014) is on `main` but unreleased.

## Behavior
- The workspace, web app and plugin say 0.1.2; `ears-classifier` keeps 0.1.0.
- The changelog has a dated 0.1.2 section: the freeze, and the extension packaging fix.
- The README and the roadmap chapter say the feature set is frozen until 1.0, what the 0.1.x line
  will still take (fixes, docs, the 1.0 readiness items), and point at the 1.0 milestone.
- `make ci` passes; after the maintainer tags v0.1.2, the release run and its artifacts are verified.

## Out of scope
The 1.0 readiness work itself (its own items).
