# Git model derived from the cadence

With sprints and releases each on or off, a project needs one of four branch topologies. kanbanr should derive it rather than leave it to convention.

| Cadence | Line of integration | Production happens at |
|---|---|---|
| neither | `main` (trunk) | merge to main |
| sprints only | `sprint/<SP>` | sprint close (sprint → main) |
| releases only | `integration` | release cut (release → main) |
| both | `sprint/<SP>` | release cut |

Scope:
- `kanbanr git model` shows the derived model.
- `kanbanr start` branches from the current integration line, not always from main.
- `sprint start` creates `sprint/<SP>`, from main or from the previous unreleased sprint branch.
- Promoting a release to candidate creates `release/<VERSION>` from the integration line (with FEAT-183).
- The commit hook accepts `feat/<CODE>-*`, `fix/<CODE>-*` and `spike/*`. It refuses direct commits on `main` and on integration lines; merges into them must carry `Refs:`.
- Pushing is never automatic.

## Design

### Summary
A new core module, `gitmodel`, derives the project's **git model** from its cadence and from facts
read from the code repository. The model has one vocabulary, shared by
[FEAT-190](/p/kanbanr/feature/FEAT-190) and [FEAT-191](/p/kanbanr/feature/FEAT-191):
- **main**: `cadence.main_branch`, else the repository's default branch
  ([FEAT-183](/p/kanbanr/feature/FEAT-183)). Production is what main holds.
- **item branches**: `feat/<CODE>-<slug>` (the project's `branch_pattern`), its `fix/` twin for
  defects, and `spike/*`. One per item; never protected.
- **line of integration** (the "line"): where finished items are merged. It follows the topology:

| Topology | Cadence | Line | Production at |
|---|---|---|---|
| `trunk` | neither | main | the integrate merge |
| `sprints` | sprints only | `sprint/<SP>` of the active sprint | sprint close (fast-forward main) |
| `releases` | releases only | `cadence.integration_branch`, default `integration` | release cut |
| `sprints_and_releases` | both | `sprint/<SP>` of the active sprint | release cut |

- **release branches**: `release/<V>`, made when a release is promoted to its first stage
  (FEAT-183), from `release_base` (below).
- **protected branches**: main, the integration branch, `sprint/*` and `release/*`. They take only
  merges carrying `Refs:` trailers. kanbanr never pushes any of them.

The topology is always derived and shown (`kanbanr git model`). The automation (where `start`
branches from, sprint branches, protection of lines, and FEAT-190's merges) runs only when
`cadence.git_model` is on (Q1). Off, everything behaves as today.

### Components and files
- `api/crates/kanbanr-core/src/gitmodel.rs` (new): `Topology`, `GitModel`, `BranchFacts`, `derive`,
  `line_for`, `release_base`, `sprint_base`, `is_protected`, `line_commit_verdict`,
  `is_integrated`. Pure decisions over facts; no I/O except `load` (board + `coderepo` facts).
- `api/crates/kanbanr-core/src/coderepo.rs` (FEAT-183 task 1): adds `branch_facts`,
  `delete_branch`, and a `push` refusal inside its `git()` wrapper.
- `api/crates/kanbanr-core/src/config.rs`: `Cadence` gains `git_model: bool`. FEAT-183 adds
  `integration_branch` and `main_branch`.
- `api/crates/kanbanr-core/src/scm.rs`: `item_code_from_branch` (pattern and its `fix/` twin);
  `SPRINT_PREFIX`, `RELEASE_PREFIX`.
- `api/crates/kanbanr-core/src/dispatch.rs`: `GET /projects/:p/git/model` (needs the repository
  root, as FEAT-183's promote route); `POST …/sprints/:code/start` calls `gitmodel::sprint_start`;
  `PUT …/config/cadence` accepts `git_model`.
- `api/crates/kanbanr-cli/src/main.rs`: `GitCmd::Model`; `run_start` takes its base from the
  model; `run_check_branch`, `run_check_msg` and `run_guard` use `line_commit_verdict`;
  `config cadence --git-model on|off`; `sprint start` prints the branch.
- `api/crates/kanbanr-core/src/releases.rs`: `promote` to the first stage branches from
  `gitmodel::release_base` (replaces FEAT-183's "integration branch").

### Data model / Interfaces
```rust
// config.rs — Cadence
/// Branching follows the derived git model (FEAT-189): off by default, so no board changes.
#[serde(default, skip_serializing_if = "std::ops::Not::not")] pub git_model: bool,

// gitmodel.rs
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)] #[serde(rename_all = "snake_case")]
pub enum Topology { Trunk, Sprints, Releases, SprintsAndReleases }
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)] #[serde(rename_all = "snake_case")]
pub enum Production { IntegrateMerge, SprintClose, ReleaseCut }
/// Facts from the code repository, collected by `coderepo::branch_facts`.
#[derive(Debug, Clone, Default)]
pub struct BranchFacts {
    pub main: String,
    pub branches: BTreeMap<String, String>,   // local branch -> tip sha
    pub merged_into_main: BTreeSet<String>,   // `git branch --merged <main>`
}
#[derive(Debug, Clone, Serialize)]
pub struct GitModel {
    pub topology: Topology, pub production: Production,
    pub automated: bool,                 // cadence.git_model
    pub main: String,
    pub integration_branch: Option<String>, // Releases topology only
    /// The current line; None with sprints on and no active sprint (see `sprint_base`).
    pub line: Option<String>,
    pub item_patterns: Vec<String>,      // [branch_pattern, its fix/ twin, "spike/*"]
    pub protected: Vec<String>,          // [main, integration?, "sprint/*", "release/*"]
}
pub fn topology(c: &Cadence) -> Topology;
pub fn derive(config: &ProjectConfig, sprints: &[Sprint], facts: &BranchFacts) -> GitModel;
pub fn load(store: &Store, id: &str, repo: &Path) -> Result<(GitModel, BranchFacts)>;
/// The line an item integrates into: its release's branch when it is planned into an unshipped
/// release that has one (a fix during test), else the current line.
pub fn line_for(model: &GitModel, item: &FeatureItem, releases: &[Release]) -> Option<String>;
/// Where `sprint/<SP>` is created: the latest sprint branch not merged into main, else main.
pub fn sprint_base(sprints: &[Sprint], facts: &BranchFacts) -> String;
/// Where `release/<V>` is created: Releases → the integration branch; with sprints → the most
/// recently closed sprint whose branch is not merged into main, else the active sprint's branch;
/// Trunk → main.
pub fn release_base(model: &GitModel, sprints: &[Sprint], facts: &BranchFacts) -> String;
pub fn is_protected(model: &GitModel, branch: &str) -> bool;
pub enum LineVerdict { NotALine, Allowed, Refused(String) }
pub fn line_commit_verdict(model: &GitModel, branch: &str, merging: bool, message: Option<&str>) -> LineVerdict;
/// At the integrate-role status or the release-role status, or an end status that is not a no-op.
pub fn is_integrated(config: &ProjectConfig, status: &str) -> bool;
/// FEAT-190 task 4 adds `catch_up: Vec<CatchUp>` to this result.
pub struct SprintStarted { pub sprint: Sprint, pub branch: Option<(String, String)> /* (name, base) */ }
pub fn sprint_start(store: &Store, id: &str, code: &str, repo: Option<&Path>) -> Result<SprintStarted>;

// coderepo.rs (added here)
pub fn branch_facts(root: &Path, main: &str) -> Result<BranchFacts>; // for-each-ref + branch --merged
pub fn delete_branch(root: &Path, name: &str) -> Result<()>;         // `git branch -D`, rollback only
// scm.rs
pub const SPRINT_PREFIX: &str = "sprint/"; pub const RELEASE_PREFIX: &str = "release/";
pub fn item_code_from_branch(pattern: &str, branch: &str) -> Option<String>;
```

### Behaviour
- **`kanbanr git model [--json]`** prints topology, main, the line (and what it was made from),
  item patterns, protected branches, open release branches with their stage, "pushing: never
  automatic", and whether automation is on. Works with automation off (it is a description).
- **`start` (R-2).** With automation on, the base for a new item branch is `line_for(item)`.
  - If that line does not exist yet (`integration` before first use), it is created from main
    first and reported ("created integration from main").
  - With sprints on and no active sprint, the base is `sprint_base` and a note says integration
    will need a sprint (Q2).
  - Defects (`kind: defect`) get the `fix/` twin when the pattern is the default (Q3).
  - With automation off, today's behaviour: the default branch.
- **`sprint start` (R-3).** `sprint_start`:
  1. preflight: board checks of `sprints::start` (no other active sprint, not closed), and with
     automation on and a repo: `sprint/<SP>` absent, or present already (then reused, "already
     exists", nothing created);
  2. git: `create_branch_from(sprint/<SP>, sprint_base)`;
  3. board: `sprints::start`;
  4. if 3 fails: `delete_branch(sprint/<SP>)`, return the error;
  5. (FEAT-190) catch-up merges for items carried into this sprint.
  With no repo and automation on: refuse ("needs the code repository: run it from the project
  folder"), as FEAT-183's first stage.
- **Release candidate.** FEAT-183's `promote` into the first stage creates `release/<V>` from
  `release_base` instead of the integration branch.
- **Hooks (R-4).** `line_commit_verdict` on a protected branch:
  - not merging → `Refused("<branch> is a line of integration: work belongs on an item branch
    (kanbanr start <CODE>); it receives merges only")`;
  - merging with a message: `parse_refs` non-empty → Allowed; `[no-ref] <why>` → Allowed (Q4);
    otherwise Refused ("a merge into <branch> must say which items it brings: Refs: kanbanr:…").
    The "Merge …" generated-commit exemption does **not** apply on a protected branch.
  - a repository with no commits: Allowed (FEAT-105).
  - Not protected → NotALine, and today's item-branch rule applies (pattern, `fix/` twin, spike).
  With automation off, `protected` is only the default branch, which is today's rule.
  `run_check_branch` (pre-commit) passes `merging = merge_in_progress`; `run_check_msg` passes the
  message and `merging = merge_in_progress` (MERGE_HEAD exists while `git merge` runs commit-msg);
  `run_guard` denies a `git commit` on a protected branch unless a merge is in progress.
- **Never pushes (R-5).** `coderepo::git` refuses any call whose first argument is `push`.

### Failure handling
- Preflight before any write; git before board; a board failure deletes the sprint branch it
  created (never one it reused).
- Branch facts come from one `for-each-ref` and one `branch --merged`; a failure to read them makes
  `git model` print "repository facts unavailable: <git error>" and the topology alone.
- Nothing is ever pushed, and no existing branch is ever moved by this item.

### Compatibility
- `git_model` is an optional key; absent means off; `Cadence::is_off` still holds for a default.
- An older binary keeps it through `Cadence.extra`.
- Hooks: unchanged behaviour with automation off. With it on, `git merge` without `-m` onto a
  protected branch is refused: use `kanbanr` merges (FEAT-190) or add `Refs:`.

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `git_model_follows_cadence` (four cadences → topology, line, production, protected; `sprint_base` picks the unreleased sprint branch; `release_base` per topology) | core gitmodel.rs |
| R-2 | `start_branches_from_integration_line` (releases on: `integration` created from main, item branched from it; a fix planned into a branched release starts from `release/<V>`) | cli local_mode.rs |
| R-3 | `sprint_start_creates_branch` (first sprint from main; second from the unreleased first; once the first is merged into main, from main; board failure leaves no branch) | cli local_mode.rs |
| R-4 | `hook_guards_integration_lines` (plain commit on main and `sprint/SP-001` refused; `git merge --no-ff -m "…Refs: kanbanr:FEAT-001"` accepted; generated merge message refused; `feat/`, `fix/`, `spike/` accepted) | cli local_mode.rs |
| R-5 | `git_model_never_pushes` (`coderepo::git(root, ["push", …])` errors; no `"push"` literal in coderepo.rs, gitmodel.rs) | core gitmodel.rs |
Plus: `scm::tests::fix_twin_names_the_item`, `line_commit_verdict` unit cases.

### Implementation tasks
1. **Config.** config.rs `Cadence.git_model`; dispatch `PUT …/config/cadence` reads `git_model`;
   CLI `config cadence --git-model on|off` and its printout. Test: round trip in core lib.rs.
   Depends on FEAT-183 task 2 (Cadence branch fields).
2. **scm.rs.** `SPRINT_PREFIX`, `RELEASE_PREFIX`, `item_code_from_branch` (pattern; if the pattern
   starts with `feat/`, also `fix/` + rest). Test: `fix_twin_names_the_item`. Depends on none.
3. **coderepo additions.** `branch_facts`, `delete_branch`, push refusal in `git()`. Test: R-5.
   Depends on FEAT-183 task 1.
4. **gitmodel.rs, pure.** Everything above except `load` and `sprint_start`. `is_integrated` uses
   FEAT-188's `ProjectConfig::role_status(Role::Integrate | Role::Release)`. Test: R-1, verdict
   cases. Depends on 2 and FEAT-188's role task.
5. **gitmodel load and sprint start.** `load`; `sprint_start` with the ordering above;
   dispatch route uses it with the repo FEAT-183 passes to dispatch. Test: R-3. Depends on 3, 4,
   FEAT-183 tasks 4 and 6.
6. **Release base.** releases.rs `promote` first stage uses `release_base`. Test: extend FEAT-183's
   `promote_candidate_creates_branch` with the releases topology. Depends on 4, FEAT-183 task 3.
7. **CLI.** `GitCmd::Model` (text and `--json`); `run_start` base and line creation; the three
   hook paths use `line_commit_verdict` and `item_code_from_branch`. Add the shared test helper
   `git_model_board(base, work, sprints, releases)` to local_mode.rs (repo with a first commit,
   default preset, charter adopted, cadence set, `--git-model on`, hooks installed). Tests: R-2,
   R-4. Depends on 4, 5.
8. **Docs.** traceability.md (branches and hooks), processes.md "Sprints and releases" (the
   topology table), cli.md, SKILL.md command reference, CHANGELOG. Depends on 7.

### Decisions (19 Oct 2026: every recommended answer accepted)
- **Q1.** Opt-in? Automation changes where `start` branches and refuses merges without Refs.
  Decided: **`cadence.git_model`, off by default**; `git model` always shows the topology.
- **Q2.** Sprints on, no active sprint: where does `start` branch, and may an item integrate?
  Decided: start from `sprint_base`; integrating refuses "start a sprint first" (FEAT-190).
- **Q3.** Should `start` name a defect's branch `fix/<CODE>-<slug>`? Decided: yes, when the
  pattern is the default; a custom pattern is used as is.
- **Q4.** Keep the `[no-ref] <why>` escape for merges into protected branches? Decided: yes;
  removing it teaches `--no-verify`, which leaves no record.
- **Q5.** Releases-only: the line defaults to `integration`, which overrides FEAT-183 Q3's
  "integration = the default branch". Decided: yes, per this approved spec; setting
  `cadence.integration_branch: main` restores trunk-like behaviour.

### Affects docs
- [FEAT-183](/p/kanbanr/feature/FEAT-183), [FEAT-188](/p/kanbanr/feature/FEAT-188),
  [FEAT-190](/p/kanbanr/feature/FEAT-190), [FEAT-191](/p/kanbanr/feature/FEAT-191)
- docs/src/using/traceability.md, docs/src/using/processes.md, docs/src/reference/cli.md,
  docs/src/reference/http-api.md, docs/src/architecture/overview.md (gitmodel, coderepo),
  skill/kanbanr/SKILL.md
