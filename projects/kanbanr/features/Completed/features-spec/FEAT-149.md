# The release verifies the installer on macOS and Windows

## Problem
The release's "verify the installer" job runs only in two Linux containers. The macOS and Windows
binaries are built and tested, but nobody has ever run `install.sh` on macOS or `install.ps1` on
Windows from a published release.

## Behavior
- `verify-install` gains a macOS leg (install.sh, Apple Silicon runner) and a Windows leg
  (install.ps1), each installing the just-published release and checking `--version` names the
  version and commit, and that `kanbanr serve` serves the monitor — the checks the Linux legs make.
- Their run blocks are checked by `make ci` like every other step; what cannot run locally is listed
  as GitHub-only.
- The next release (v0.1.2) is the first to run them.

## Out of scope
The Intel macOS archive gets no installer leg (same script, same OS; the binary is already built
and checked on its own runner).
