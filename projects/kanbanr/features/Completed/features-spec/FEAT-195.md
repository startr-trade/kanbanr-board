# Tests cannot reach a real board

## Why
On 19 Oct 2026 a FEAT-183 test ran `kanbanr init shop --author A --email a@x` from a scratch folder
under `CARGO_TARGET_TMPDIR`, which is inside this repository. The CLI walked up to the repository's
`.kanbanr` marker and used the real board. It created a project, changed the board's commit
identity, and the board's auto-push published seven commits to GitHub. Lesson L-41 records it.

The push policy is now `off`, so nothing reaches the remote unreviewed. But a careless test can
still write to the real board. This item makes that impossible by construction rather than by
care: a test run can only touch boards inside the system temporary directory.

## Design

### Summary
A new environment variable, `KANBANR_BOARD_FENCE`, confines kanbanr to boards inside one directory.
Cargo sets it for every test process through `api/.cargo/config.toml`, so every CLI the tests spawn
inherits it. The special value `temp` means `std::env::temp_dir()`. Any board outside the fence
makes the process stop before it reads or writes anything. Every test scratch folder moves into
`temp_dir()`. `make ci` also fails if the real board, when there is one, changed during the run.

### Components and files
- `api/crates/kanbanr-core/src/project.rs`: `pub fn fence() -> Option<PathBuf>` and
  `pub fn assert_inside_fence(dir: &Path)`.
- `api/crates/kanbanr-core/src/store.rs`: `Store::new` calls `assert_inside_fence`.
- `api/crates/kanbanr-core/src/git.rs`: `ensure_repo_as`, `set_identity`, `commit`, `commit_local`
  and `sync_all` call it.
- `api/.cargo/config.toml` (new): `[env] KANBANR_BOARD_FENCE = "temp"`.
- `api/crates/kanbanr-cli/tests/local_mode.rs`, `view_daemon.rs`: the 9 `CARGO_TARGET_TMPDIR`
  scratch folders move to `std::env::temp_dir()`.
- `Makefile`, the `ci` target: a guard around the run (see Behaviour).
- `docs/src/project/contributing.md` (or the testing section it has): one paragraph.

### Signatures
```rust
// project.rs
/// The directory boards must be inside, from `KANBANR_BOARD_FENCE` (FEAT-195). `temp` means the
/// system temporary directory. None when unset or empty. Canonicalised.
pub fn fence() -> Option<PathBuf>;

/// Stop the process if `dir` is outside the fence. A board outside it is a test about to write
/// to someone's real data: nothing must be read or written, so this panics with
/// "refusing board <dir>: outside KANBANR_BOARD_FENCE (<fence>)". Without a fence, it does
/// nothing. `dir` need not exist yet: its nearest existing ancestor is canonicalised.
pub fn assert_inside_fence(dir: &Path);
```
A panic, not an error, on purpose. The fence exists only under test, and an error could be caught
and the run continue with a fallback board. A panic ends the process before any write.

### Behaviour
- The check compares canonical paths, so symlinks are handled, as is macOS's `/var` → `/private/var`.
  A relative `dir` is resolved against the current directory first.
- `Store::new` is the choke point: every read and write of a board makes one. The git functions are
  covered too, because identity and commits can be reached without a store.
- **make ci guard.** Before the run, the Makefile records `kanbanr where --json`'s board path from
  the repository root, plus that board's `git rev-parse HEAD` and `git status --porcelain`. It
  compares them after. A difference fails the run, naming what moved. With no board found (GitHub
  Actions, a fresh clone), the guard says so and skips.
  - Board writes made by the developer during a long CI run would also trip it. That is acceptable:
    the run then says to rerun.

### Security and failure handling
The fence narrows access and never widens it. Unset, behaviour is unchanged. A wrong value can only
refuse boards, never redirect to one.

### Compatibility
Users never set the variable. No data format changes.

### Performance
One canonicalize per `Store::new` and per git write, only when the fence is set.

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `board_outside_the_fence_is_refused` | cli `local_mode.rs`. A board made with plain file writes under `CARGO_TARGET_TMPDIR` (outside temp), opened with `--data-dir` and `KANBANR_BOARD_FENCE=temp`. It must fail, name the fence, and leave the folder byte-identical. |
| R-2 | `tests_run_inside_the_fence` | cli `local_mode.rs`: `KANBANR_BOARD_FENCE` is set in the test process, and every scratch helper's folder is inside `temp_dir()`. |
| R-3 | `manual: make ci fails when the real board moves` | review. Run make ci while committing to a scratch clone that `kanbanr where` points at, and see it fail. |
Plus `project::tests::fence_*` (unset, temp, inside, outside, not-yet-existing dir). The guardrail
is seen failing once (ADR-0008): unset the fence in config.toml and watch R-2 go red.

### Implementation tasks
1. **Fence.** project.rs: `fence`, `assert_inside_fence`, with `project::tests::fence_*`. Depends
   on: none.
2. **Choke points.** Calls from `Store::new` and the git write functions. Tests: the core suite
   still passes (all of it uses temp_dir). Depends on 1.
3. **Cargo env.** `api/.cargo/config.toml`. Test: R-2. Depends on 1.
4. **Migrate scratch folders.** The 9 `CARGO_TARGET_TMPDIR` uses move to `temp_dir()`, each with a
   unique name (tag plus pid, as `togaf_scratch` does). Test: the CLI suite passes with the fence on.
   Depends on 3.
5. **R-1 test.** As in the test plan. Depends on 2.
6. **make ci guard.** The Makefile before/after check. Test: R-3. Depends on none.
7. **Docs.** The contributing note, and a CHANGELOG line under "Changed" (for contributors) with the
   docs sync. Depends on 1–6.

### Open questions
None. The decision to do this before the rest of FEAT-180 was made on 19 Oct 2026.

### Affects docs
docs/src/project/contributing.md (a code-repo file, not a board doc).
