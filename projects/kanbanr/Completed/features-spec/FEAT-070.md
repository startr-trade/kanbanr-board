# Defect: a rebuilt UI is invisible to a running monitor

## Problem
`kanbanr serve --ui-dir web/dist` reads `index.html` **once at startup** and serves that string for the lifetime of the process. Vite writes hashed asset names on every build, so after a rebuild the cached index points at `assets/index-<old-hash>.js`, which no longer exists on disk. The browser gets a 404 for the bundle and runs whatever it has cached, or nothing.

The user reported diagrams not rendering in the monitor. The diagrams were fine — the monitor was serving a five-rebuild-old index referencing a deleted bundle. The failure looks like a broken feature rather than a stale process, which is what makes it worth fixing rather than remembering.

## Behavior
- The index is read per request. It is one small file, the daemon already touches the disk for every asset, and correctness here is worth more than a saved read.
- If the read fails, the last known good copy is served rather than an empty page, so a mid-rebuild request does not blank the app.

## Out of scope
Live reload or asset-hash invalidation in the browser — a refresh is enough once the index is current.