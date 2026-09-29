## Problem

When nothing is serving, `kanbanr open` prints `kanbanr serve --ui-dir web/dist`. Since FEAT-084 the monitor is compiled into the binary, so the flag is unnecessary and `web/dist` exists only in kanbanr's own checkout. In the katalog setup Claude followed the hint, searched the disk, and started the monitor from this repository's development build — tying another project's monitor to a working tree.

## Behavior

The hint says `kanbanr serve` (and `kanbanr serve --allow-writes` only where writes are wanted), with no `--ui-dir`. Any other user-facing text naming `--ui-dir web/dist` as the normal way to serve is corrected.

## Out of scope

- The `--ui-dir` flag itself, which stays for SPA development.