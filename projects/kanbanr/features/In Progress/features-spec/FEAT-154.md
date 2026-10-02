# Release notes for every release, on the release page and in the docs

## Problem
A kanbanr release page says only "Full Changelog: v0.1.0...v0.1.1" — a commit range. Someone
deciding whether to upgrade, or what a release means for their board, has to read the whole
changelog and work it out. The changelog is the running log; nothing tells the story of one
release.

## Behavior
- Each release has a notes page, `docs/src/releases/vX.Y.Z.md`, written for a user: a one-paragraph
  summary of the release's theme, then **Highlights**, **What's new**, **What changed**, **What's
  fixed**, **Known limits** and **Upgrade notes** (sections with nothing to say are left out). An
  index page lists every release, newest first, with a one-line summary; the book links it.
- The release workflow puts that page on the GitHub release page, above GitHub's generated list of
  commits and contributors.
- A tag with no notes page is refused by the tag check, before anything is built — a release is
  never published blank. `make ci` checks the workspace's version has its page.
- Notes are written for v0.1.0, v0.1.1 and v0.1.2. The two published release pages are updated
  with theirs by the maintainer (`gh release edit … --notes-file …`), since editing a published
  release is the maintainer's call.

## Out of scope
Generating notes automatically from the board; the changelog stays the complete log.
