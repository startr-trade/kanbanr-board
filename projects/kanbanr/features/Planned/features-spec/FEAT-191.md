# Git drift check

`kanbanr git doctor`, also run by `kanbanr doctor` when the git model is in use, reports:
- items in the integrate role whose branch is not merged into the line of integration;
- commits on a line of integration whose item is not at integrate or later;
- item branches whose item is finished or parked;
- branches that name no item;
- release branches whose fixes have not been merged forward.

## Design

### Summary
`kanbanr git doctor` compares the board with the code repository's branches, using the git model
from [FEAT-189](/p/kanbanr/feature/FEAT-189) (main, item branches, lines of integration, release
branches) and the role order from [FEAT-188](/p/kanbanr/feature/FEAT-188). It is a **read**: it
runs only read-only git commands and never changes the board or the repository. Its findings are
ordinary `doctor::Issue`s, so `kanbanr doctor` includes them when the git model's automation is on
(`cadence.git_model`) and a repository is at hand.

Two halves, as FEAT-176 asks: `gitdrift::collect` gathers facts with read-only git calls
(`coderepo`), and `gitdrift::check` decides over those facts, and is unit-tested without a
repository.

| Finding | Severity | Req |
|---|---|---|
| An integrated item whose branch is not merged into its line (or main) | error | R-1 |
| A commit on a line serving only items that are not integrated | error | R-2 |
| A branch naming no item, an unknown item, sprint or release | warning | R-3 |
| A release branch with commits its line lacks (not merged forward) | warning | R-3 |
| An item branch whose item is finished (merged: delete it) or parked | warning | spec |

### Components and files
- `api/crates/kanbanr-core/src/gitdrift.rs` (new): `DriftFacts`, `collect`, `check`, `scan`.
- `api/crates/kanbanr-core/src/coderepo.rs`: `branches_merged_into` (one `git branch --merged`
  per target); `commits_between` with a limit, from FEAT-190 task 1.
- `api/crates/kanbanr-core/src/gitmodel.rs` (FEAT-189): `is_parked`, `is_finished`.
- `api/crates/kanbanr-core/src/dispatch.rs`: `GET /projects/:p/git/doctor`; `GET
  /projects/:p/doctor` appends `gitdrift::scan` when automation is on and the caller passed a
  repository (FEAT-183's mechanism).
- `api/crates/kanbanr-cli/src/main.rs`: `GitCmd::Doctor { json }`, printed like `run_doctor`, exit
  status 1 when there is an error.

### Data model / Interfaces
```rust
// gitdrift.rs
pub struct DriftFacts {
    pub branches: gitmodel::BranchFacts,                       // FEAT-189: tips, merged into main
    /// For each line checked: the local branches merged into it.
    pub merged_into: BTreeMap<String, BTreeSet<String>>,
    /// For each line checked: its commits not on main (main itself: the last LIMIT commits).
    pub line_commits: BTreeMap<String, Vec<coderepo::Commit>>,
    /// For each release branch: its commits the current line lacks.
    pub unforwarded: BTreeMap<String, Vec<coderepo::Commit>>,
}
/// Commits read per line; also the window on main in the trunk topology (Q1).
pub const LIMIT: usize = 200;
/// The lines checked: the current line, every `sprint/*` not merged into main, and every
/// `release/*` of a release on the board; main too in the trunk topology.
pub fn lines(model: &GitModel, facts: &gitmodel::BranchFacts, releases: &[Release]) -> Vec<String>;
pub fn collect(root: &Path, model: &GitModel, releases: &[Release]) -> Result<DriftFacts>;
pub fn check(project: &Project, sprints: &[Sprint], releases: &[Release],
             model: &GitModel, facts: &DriftFacts) -> Vec<doctor::Issue>;
/// Load board and model, collect, check. Read-only.
pub fn scan(store: &Store, id: &str, root: &Path) -> Result<Vec<doctor::Issue>>;

// gitmodel.rs (added here)
/// Finished: `counts_as_done`, or the release-role status.
pub fn is_finished(config: &ProjectConfig, status: &str) -> bool;
/// Parked: a no-op status, or a status before the build-role status in `statuses` order.
pub fn is_parked(config: &ProjectConfig, status: &str) -> bool;

// coderepo.rs
pub fn branches_merged_into(root: &Path, target: &str) -> Result<BTreeSet<String>>;
// commits_between (FEAT-190) gains `limit: Option<usize>` → `git log -n <limit>`
```

### Behaviour
`check` runs these rules, item by item and branch by branch, sorted by code then branch:
- **Item branches.** For each local branch, `item_code_from_branch` (FEAT-189) gives its item.
  - **R-1.** The item `is_integrated` (FEAT-189) and its branch is in neither
    `merged_into[line_for(item)]` nor `branches.merged_into_main` → error, code set: "<CODE> is
    <status> (integrated) but <branch> is not merged into <line>: move it back, or merge it
    (FEAT-190 does this on the move)". With no line (no active sprint), main is the only target.
  - The item `is_finished` and the branch is merged → warning: "<CODE> is finished and <branch> is
    merged: delete it with `git branch -d <branch>`".
  - The item `is_parked` → warning: "<CODE> is <status> (parked) but <branch> remains".
- **R-2, commits on lines.** For each line and each commit in `line_commits[line]`:
  - `parse_refs(message)` gives its items. A commit naming no item is skipped (a `[no-ref]` escape
    or a generated commit is on the record already).
  - If **none** of those items `is_integrated` → one error per (line, item), with the count and
    the newest sha: "<line> has 3 commits serving <CODE> (newest abc1234), which is <status>, not
    integrated". A commit that also serves an integrated item is justified and not reported.
  - A `Refs:` naming an item not on the board → error: "commit abc1234 on <line> names <CODE>,
    which is not on the board".
- **R-3, orphans.** A branch is accounted for when it is main, the integration branch, `spike/*`,
  or names an item that exists. Otherwise a warning:
  - "<branch> names no item" (no code in it);
  - "<branch> names <CODE>, which is not on the board";
  - `sprint/<SP>` for a sprint not in sprints.yaml: "<branch> names no sprint";
  - `release/<V>` for a version not in releases.yaml: "<branch> names no release".
- **R-3, forward merges.** For each release branch with `unforwarded` commits → warning: "<branch>
  has N commits <line> lacks (newest abc1234): `kanbanr git forward <V>`". None when there is no
  line, or the line is main and main already has them.
- **Output.** `kanbanr git doctor` lists errors then warnings, as `doctor` does, plus a first line
  naming the topology and whether automation is on; with automation off it still runs (on
  demand) and says the findings are against the derived model. `--json` prints the issues.
- **In doctor.** The project doctor route appends `scan` when `cadence.git_model` is on and a
  repository was passed; with no repository, one warning: "git drift not checked: run from the
  project folder". `doctor --all-projects` checks only the project whose marker the repository has.

### Failure handling
- Read-only by construction: `collect` calls only `for-each-ref`, `branch --merged`, `log` and
  `rev-parse`. A test checks that the repository's refs and the board files are byte-identical
  before and after a scan.
- A git failure while collecting becomes one warning ("git drift not checked: <git error>"),
  never a failed doctor.
- Budget: one `for-each-ref`, one `branch --merged` and one `log -n LIMIT` per line, plus one log
  per release branch; under 1 s for 200 branches and 10 lines.

### Compatibility
No stored data changes. `doctor` output gains issues only for projects that turned automation on.
The doctor route's JSON shape is unchanged (more `issues`).

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `git_doctor_unmerged_integrated_items` (FEAT-001 moved to Completed with automation off, so not merged; `git doctor` errors naming it and the line; after the merge, clean) | cli local_mode.rs |
| R-2 | `git_doctor_unfinished_commits_on_line` (sprints on: FEAT-002's branch merged into `sprint/SP-001` by hand while FEAT-002 is In Progress → error with count and sha; a commit also serving an integrated item → not reported) | cli local_mode.rs |
| R-3 | `git_doctor_orphans_and_forward_merges` (branches `wip`, `feat/FEAT-999-x`, `sprint/SP-099`, `release/v9` warned; a fix on `release/v1` not forwarded warned; after `git forward v1`, gone; `spike/x` not warned) | cli local_mode.rs |
Plus unit tests in gitdrift.rs over synthetic `DriftFacts` (one per rule, including finished and
parked branches), `git_doctor_is_read_only` (refs and board unchanged), and `doctor` including the
findings only with automation on (local_mode.rs).

### Implementation tasks
1. **coderepo.** `branches_merged_into`; the `limit` on `commits_between`. Unit test on a scratch
   repo. Depends on FEAT-190 task 1, FEAT-183 task 1.
2. **gitmodel predicates.** `is_finished`, `is_parked` using FEAT-188's
   `role_status(Role::Build | Role::Release)`. Unit tests on the default and TOGAF presets.
   Depends on FEAT-189 task 4.
3. **gitdrift check.** `lines`, `check` with the rules and messages above. Unit tests per rule.
   Depends on 2.
4. **gitdrift collect and scan.** `collect`, `scan`; `git_doctor_is_read_only`. Depends on 1, 3.
5. **Routes.** `GET …/git/doctor`; the project doctor route appends `scan` per the rule above.
   Depends on 4, FEAT-183 tasks 4–6 (repository passed to dispatch).
6. **CLI.** `GitCmd::Doctor { json }` and its printout and exit status. Tests: R-1, R-2, R-3 using
   FEAT-189's `git_model_board` helper. Depends on 5, FEAT-190 task 6 (for R-3's forward step).
7. **Docs.** traceability.md "Drift between board and branches", housekeeping.md (doctor),
   cli.md, http-api.md, SKILL.md, CHANGELOG. Depends on 6.

### Open questions
- **Q1.** In the trunk topology the line is main, which has no base to compare with. Recommended:
  check main's last `LIMIT` (200) commits; older history predates the drift worth reporting.
- **Q2.** Should drift errors make `kanbanr doctor` exit non-zero (and so fail `make ci`)?
  Recommended: yes for errors, as the other doctor errors do; warnings never fail.
- **Q3.** Report merged branches of finished items at all? They are harmless clutter.
  Recommended: yes, as warnings; they are the only reminder to delete them (FEAT-190 Q3).

### Affects docs
- [FEAT-176](/p/kanbanr/feature/FEAT-176), [FEAT-183](/p/kanbanr/feature/FEAT-183),
  [FEAT-188](/p/kanbanr/feature/FEAT-188), [FEAT-189](/p/kanbanr/feature/FEAT-189),
  [FEAT-190](/p/kanbanr/feature/FEAT-190)
- docs/src/using/traceability.md, docs/src/using/housekeeping.md, docs/src/reference/cli.md,
  docs/src/reference/http-api.md, docs/src/architecture/overview.md, skill/kanbanr/SKILL.md
