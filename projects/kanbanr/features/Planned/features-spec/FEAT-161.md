# Defect: the container image ships Debian packages with known fixes

## Problem
The release scans its image before pushing it and refuses a fixable HIGH or CRITICAL finding. A new
Debian advisory (CVE-2026-103111, libpcre2-8-0, fixed in 10.42-1+deb12u2) now fails that scan:
`debian:bookworm-slim` has not been rebuilt with the fix yet, and the runtime stage installs only
`ca-certificates`, so the image keeps the base image's older package. v0.1.5 would be refused at the
image step, and every release would wait on Debian's base-image rebuilds.

## Behavior
- The runtime stage applies Debian's published security updates (`apt-get upgrade`) when the image
  is built, so a fix in the archive reaches the image without waiting for a new base image.
- `make ci`'s image scan passes; the release's scan before the push passes.

## Out of scope
Changing the base image or distribution.
