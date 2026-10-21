# macOS and Windows: CI fails on paths and line endings

## Why
CI's macos-15 leg failed on 21 Oct 2026, after main was pushed for 0.2.0. Two tests in
`api/crates/kanbanr-cli/tests/view_daemon.rs` (`promote_through_the_daemon_uses_the_repository_it_was_started_in`
and `monitor_promote_matches_cli`, from FEAT-183/185) assert that the board `kanbanr where` reports
lies under the test's scratch folder (lesson L-41). On macOS the system temp dir is
`/var/folders/…`, a symlink to `/private/var/folders/…`; kanbanr reports the resolved path, the test
compares it with the unresolved one, and the guard refuses the test's own board. Linux has no such
symlink, so `make ci` (which cannot run the macOS leg) passed.

## Design

### Windows (found in the same push; the wider fix approved by the user, 21 Oct 2026)
CI's windows-2025 leg failed 7 tests, none from the program:
- the runner checks text files out with CRLF, and tests compare committed files byte for byte
  (`SKILL.md`, `testdata/typed_responses.txt`, `openapi.json`): the two skill guards,
  `typed_responses_put_the_same_bytes_on_the_wire`, `contract_matches_openapi`;
- `promote_production_cuts_tags_merges` reads back a file committed in its own scratch repository,
  which Windows's git checked out with CRLF;
- the same scratch-board guard: Windows reports `C:\Users\runneradmin\…` where the temp dir can be
  a short name.

### Change
- Both guards compare `std::fs::canonicalize` of the board with that of the scratch folder, so they
  still refuse any board outside it and accept the one inside it on every platform.
- A root `.gitattributes`, `* text=auto eol=lf`: every text file is checked out with LF on every
  platform. Every file in the index was already LF, so no committed file changes; the v0.1.7
  fixture keeps its own `-text`.
- The release tests' scratch repository sets `core.autocrlf false`.
- No product code changes.

### Test plan
| Req | Test |
|---|---|
| R-1 | `promote_through_the_daemon_uses_the_repository_it_was_started_in`, `monitor_promote_matches_cli` pass on Linux, and on CI's macOS and Windows legs after push; a clone with `core.autocrlf=true` checks the compared files out with LF |

### Implementation tasks
1. The two assertions; a changelog line is not needed (test-only). Depends on: none.

### Affects docs
None.
