# A cached build can ship without the monitor or the skill

## Why
On 20 Oct 2026 an installed kanbanr served no monitor ("this build has no built-in monitor") and
carried no skill ("this binary carries no skill"), built from a full checkout. Both build scripts
find their files through `env!("CARGO_MANIFEST_DIR")`, which is fixed when the build script is
*compiled*. With `sccache` as the rustc wrapper (this machine's setup), a build script compiled in
one folder is reused in another with the same sources: here, one compiled in a temporary
worktree that was later deleted. It looked for `web/dist` and `skill/kanbanr` there, found nothing,
and embedded empty tables. `make install-cli` and a plain `cargo build --release` were both
affected; nothing failed, the binary was just missing its monitor and skill.

## Design

### Fix
- `api/crates/kanbanr-server/build.rs` and `api/crates/kanbanr-cli/build.rs`: read
  `CARGO_MANIFEST_DIR` with `std::env::var` (set by cargo each time the script *runs*), never
  `env!`. Same for any other build-time path.
- A release or `make install-cli` build that finds no monitor or no skill under a full checkout
  fails loudly rather than producing a binary without them: the build script panics with the path
  it looked in, unless `KANBANR_ALLOW_BARE_BUILD=1` (a crate built outside the repository, as
  today's message describes).

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `build_scripts_read_the_manifest_dir_at_run_time` (no `env!("CARGO_MANIFEST_DIR")` in either build.rs) | cli tests |
| R-1 | `manual: a release build reused from another folder through sccache still carries the monitor and the skill` (build in a scratch copy, delete it, build here, `skill install` into a temp folder and serve `/`) | review |

### Implementation tasks
1. Both build.rs: runtime `CARGO_MANIFEST_DIR`; the loud failure and its opt-out. Depends on: none.
2. The source check test; the manual check; CHANGELOG "Fixed". Depends on 1.

### Affects docs
docs/src/project/contributing.md (building and installing from source).
