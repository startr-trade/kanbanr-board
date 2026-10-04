# The release refuses a tag whose commit has not passed CI

## Problem
v0.1.5 was tagged while CI was still running on the same commit. CI then failed on macOS (FEAT-162),
but the release had already built, published and announced v0.1.5: the release workflow builds and
checks its own artifacts, but never asks whether the commit passed the test suite on every platform.
"Wait for green before tagging" is a rule a person has to remember, and the tag check is where
kanbanr already refuses a bad tag before anything is built.

## Behavior
- The release's tag check asks GitHub for the CI workflow's run on the tagged commit. It proceeds
  only if that run succeeded; if CI is still running it waits (up to a time limit) and then decides;
  if CI failed or never ran on that commit, it refuses before anything is built, naming the run.
- The open-sourcing guide's release steps say to tag after CI is green, and that the release
  enforces it.

## Out of scope
Branch protection rules on GitHub (the maintainer's settings).
