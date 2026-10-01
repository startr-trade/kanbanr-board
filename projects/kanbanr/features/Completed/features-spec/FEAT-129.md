## Problem

The first CI run on GitHub (`main` at 525a2e1) failed on all three operating systems, for three unrelated reasons. None shows locally, which is why none was caught before the push.

- **Linux — the monitor test runs against a binary without a monitor.** `the_monitor_is_served_from_the_binary_with_no_ui_dir` gets a 404 for `/`. The `rust` job never builds `web/dist`, so the binary under test embeds no monitor (ADR-0009). Locally `web/dist` exists, so it passes.
- **macOS — the docs guard misses a file reached through a symlink.** `cli_claude_sync_and_the_docs_guard` expects a loose note to be refused and it is allowed. The runner's temp folder is `/var/…`, a symlink to `/private/var/…`; `board_path_for` resolves the file path by text only, while the repository root comes from git already resolved, so `strip_prefix` fails and the file counts as outside the repository (FEAT-111).
- **Windows — the tests do not link.** `kanbanr-core`'s test binary fails with `LNK2019: unresolved external symbol __imp_OpenProcessToken / CheckTokenMembership / CopySid`, from vendored libgit2's ownership check. Those live in `advapi32.lib`, which libgit2-sys 0.17 does not ask the linker for, and the current MSVC toolchain no longer brings in by default.

## Behavior

- The `rust` CI job builds the web assets before it builds and tests, so the binary under test is the one a release ships.
- The docs guard resolves the existing part of a path on disk (symlinks included) before comparing it with the repository root, and still resolves `..` in the part that does not exist yet without letting it escape.
- Every binary that links libgit2 on Windows also links `advapi32`.

## Out of scope

- New CI jobs or scanners (FEAT-130).
