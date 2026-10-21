# macOS: two daemon tests refuse their own scratch board

## Why
CI's macos-15 leg failed on 21 Oct 2026, after main was pushed for 0.2.0. Two tests in
`api/crates/kanbanr-cli/tests/view_daemon.rs` (`promote_through_the_daemon_uses_the_repository_it_was_started_in`
and `monitor_promote_matches_cli`, from FEAT-183/185) assert that the board `kanbanr where` reports
lies under the test's scratch folder (lesson L-41). On macOS the system temp dir is
`/var/folders/…`, a symlink to `/private/var/folders/…`; kanbanr reports the resolved path, the test
compares it with the unresolved one, and the guard refuses the test's own board. Linux has no such
symlink, so `make ci` (which cannot run the macOS leg) passed.

## Design

### Change
- In both tests, compare against `std::fs::canonicalize(&base)` (the folder exists by then), so the
  guard still refuses any board outside the scratch folder and accepts the one inside it on every
  platform. No product code changes.

### Test plan
| Req | Test |
|---|---|
| R-1 | `promote_through_the_daemon_uses_the_repository_it_was_started_in`, `monitor_promote_matches_cli` pass on Linux, and on CI's macOS leg after push |

### Implementation tasks
1. The two assertions; a changelog line is not needed (test-only). Depends on: none.

### Affects docs
None.
