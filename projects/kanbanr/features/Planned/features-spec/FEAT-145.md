# Defect: the container image's kanbanr carries no skill

## Problem
`kanbanr skill install` inside the GHCR image fails with "this binary carries no skill (it was built
outside the kanbanr repository)". The program embeds `skill/kanbanr/` at build time (FEAT-141), but
the Dockerfile copies only `api/` into the build stage, so the build script finds no skill and embeds
nothing. The image's binary is therefore not the program the release archives carry, though both
report the same version — and no check compares them.

## Behavior
- The image build copies `skill/` beside `api/`, so the binary embeds the same skill as the archives.
- The release refuses to push an image whose kanbanr carries no skill, or a different one than the
  archives; make ci builds the image and runs the same check.

## Out of scope
Re-publishing the v0.1.0 image — the fix ships with the next release. Making the image a Claude Code
environment: it stays the monitor; the skill is there so its binary is the released program.
