# Windows: a release test assumes a push by path leaves origin/main alone

## Why
CI on main for v0.3.0 (22 Oct 2026) failed on windows-2025 in one test,
`releases::tests::promote_fetches_and_works_offline` (FEAT-212 R-7): "the remote-tracking ref has
not seen the push". The test pushes main to the bare remote by its path, expecting the clone's
`origin/main` not to know yet, so the cut has to fetch first. On Windows git matches that path to
the configured `origin` and updates `origin/main` during the push, so the "pushed, not fetched"
state never exists. The product is right; the test's setup is platform-dependent.

## Design
- In `api/crates/kanbanr-core/src/releases.rs` `promote_fetches_and_works_offline`: read
  `origin/main` before the push and restore it with `git update-ref refs/remotes/origin/main <old>`
  right after, so every platform has the same "pushed, not yet fetched" state. Nothing else changes.
- Planned into v0.3.0: without it CI cannot pass and the release cannot be tagged. Branched from
  `release/v0.3.0`, merged back there; v0.3.0 is then promoted to main again.

### Test plan
| Req | Test |
|---|---|
| R-1 | `releases::tests::promote_fetches_and_works_offline` passes here; CI's windows-2025, macos-15 and ubuntu legs after the push |

### Implementation tasks
1. The test change; the test run. Depends on: none.

### Affects docs
None.
