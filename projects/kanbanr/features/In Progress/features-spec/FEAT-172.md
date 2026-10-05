# Defect: the release's monitor check measures size, which code growth defeats

## Problem
`release.yml`'s "Check the monitor is embedded, and compressed" brackets the binary's size: at
least 12,000,000 bytes (the monitor is in) and at most 20,000,000 (its assets are compressed). The
binary without the monitor is now about 19 MB, and raw assets would add only ~2.7 MB more than
compressed ones, so both bounds are stale: a binary missing the monitor passes the floor, and code
growth alone failed the ceiling — FEAT-169's make ci, at 20,099,776 bytes, with the assets
compressed (3.8 MB raw, ~1.06 MB gzipped). Raising the ceiling would stop it catching raw assets.

## Behavior
Check what the step's name says, directly:
- embedded: every file under `web/dist` is named in the binary (the asset table carries each path);
- compressed: a 256-byte stretch from the middle of the largest JS asset is not in the binary.
The same script runs in make ci. Seen failing on a binary built without the monitor, and on one
with the assets stored raw.

## Out of scope
How the assets are compressed (FEAT-084).
