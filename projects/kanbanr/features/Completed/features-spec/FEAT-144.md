# Defect: the container image's kanbanr cannot say which build it is

## Problem
`docker run ghcr.io/startr-trade/kanbanr:v0.1.0 kanbanr --version` prints
`kanbanr 0.1.0 (unknown, built unknown)`. The release archives name their commit; the image does not.
The Docker build context excludes `.git` (`.dockerignore`), and the Dockerfile passes no
`KANBANR_GIT_SHA`, so build.rs falls back to `unknown`. The build date has no override at all — it is
read only from git. The release checks the archives' `--version` but never the image's, so this
shipped without a failure.

## Behavior
- The Dockerfile takes the commit and its date as build arguments; the release (and make ci) pass them.
- build.rs accepts `KANBANR_BUILD_DATE` as it already accepts `KANBANR_GIT_SHA`.
- The release refuses to push an image whose binary reports `unknown`; make ci builds the image the
  same way and runs the same check.

## Out of scope
Re-publishing the v0.1.0 image — the fix ships with the next release.
