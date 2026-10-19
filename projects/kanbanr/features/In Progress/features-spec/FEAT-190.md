# Stage-driven merges and carry-over

Scope:
- **Integrate.** When an item enters the status with the `integrate` role and its gate is met (tests green), kanbanr merges its branch into the line of integration with `--no-ff` and the item's `Refs`. It refuses on conflict and leaves everything as it was.
- **Release terminal.** When a release is cut (FEAT-183), or a sprint closes in the sprints-only model, the line is fast-forwarded into main and tagged. If that is not a fast-forward, it stops.
- **Carry-over.** `sprint close --carry-to` keeps unfinished item branches open. When the next sprint branch exists, kanbanr merges it *into* each carried item branch (catch-up, never a rebase). Conflicts are reported for the item.
- **Fixes move forward.** Fixes on a release branch, and patch releases, are merged forward into the current line of integration.

## Design

### Summary
With the git model's automation on ([FEAT-189](/p/kanbanr/feature/FEAT-189), `cadence.git_model`),
board moves and cadence events make the merges themselves, using FEAT-189's vocabulary (main, item
branches, the line of integration, release branches):
- **Integrate.** An item that moves into the integrate role
  ([FEAT-188](/p/kanbanr/feature/FEAT-188)) has its item branch merged `--no-ff` into its line
  (`gitmodel::line_for`), with a `Refs:` trailer. A conflict refuses the move and changes nothing.
- **Terminal.** Sprints topology: `sprint close` fast-forwards main to `sprint/<SP>` and tags it.
  Release topologies: FEAT-183's production step fast-forwards main to `release/<V>` (Q2, decided: fast-forward).
  Not a fast-forward: it stops.
- **Carry-over.** Carried items keep their branches; once the next sprint's branch exists, it is
  merged *into* each of them (catch-up, never a rebase). Conflicts are reported per item.
- **Forward.** A fix integrated into `release/<V>` is reported as needing a forward merge, and
  `kanbanr git forward <V>` performs it into the current line.
Every git step follows FEAT-183's order: preflight → git → board → undo git if the board fails.
Nothing is pushed.

### Components and files
- `api/crates/kanbanr-core/src/gitmodel.rs` (FEAT-189): `move_item`, `sprint_close`, `catch_up`,
  `forward`, and their result types; `SprintStarted` gains `catch_up`.
- `api/crates/kanbanr-core/src/coderepo.rs` (FEAT-183 task 1): the worktree-free `merge_no_ff`
  contract, plus `merge_preview`, `is_ancestor`, `fast_forward`, `commits_between`.
- `api/crates/kanbanr-core/src/store.rs`: `Store::gate_preview` (public, read-only `check_gate`).
- `api/crates/kanbanr-core/src/batch.rs`: refuses a batch move that would integrate, when
  automated.
- `api/crates/kanbanr-core/src/releases.rs`: FEAT-183's production step uses `fast_forward`
  (Q2); a patch's `forward_merge` list (FEAT-184) is unchanged.
- `api/crates/kanbanr-core/src/dispatch.rs`: the move route calls `gitmodel::move_item`; the
  sprint close route calls `gitmodel::sprint_close`; new `POST /projects/:p/git/forward/:version`.
- `api/crates/kanbanr-cli/src/main.rs`: `move`, `start`, `finish` print the merge; `sprint close`
  and `sprint start` print catch-ups; `GitCmd::Forward { version }`.

### Data model / Interfaces
```rust
// coderepo.rs
pub struct MergePreview { pub clean: bool, pub conflicts: Vec<String> } // paths
/// `git merge-tree --write-tree --name-only --no-messages <into> <from>`; exit 1 = conflicts.
pub fn merge_preview(root: &Path, into: &str, from: &str) -> Result<MergePreview>;
pub fn is_ancestor(root: &Path, ancestor: &str, of: &str) -> bool; // merge-base --is-ancestor
/// Merge `from` into branch `into` with a merge commit; returns (old, new) tips of `into`.
/// `into` not checked out: merge-tree → commit-tree -p into -p from → update-ref <into> <new> <old>
/// (working tree untouched). `into` checked out: requires a clean tree, `git merge --no-ff -m`.
pub fn merge_no_ff(root: &Path, into: &str, from: &str, message: &str) -> Result<(String, String)>;
/// Move `branch` to `to` only if it is an ancestor; returns the old tip. update-ref with the old
/// value, or `git merge --ff-only` when `branch` is checked out.
pub fn fast_forward(root: &Path, branch: &str, to: &str) -> Result<String>;
pub struct Commit { pub sha: String, pub subject: String, pub message: String }
pub fn commits_between(root: &Path, base: &str, head: &str) -> Result<Vec<Commit>>; // base..head

// store.rs
/// What moving `code` to `to` would meet at its gate, without moving it.
pub fn gate_preview(&self, id: &str, code: &str, to: &str, reason: Option<&str>) -> Result<GateOutcome>;

// gitmodel.rs
pub struct Merged { pub branch: String, pub into: String, pub sha: String, pub already: bool }
pub struct Moved { pub feature: FeatureItem, pub warnings: Vec<Gap>, pub merged: Option<Merged>,
                   /// Set when `into` is a release branch: run `kanbanr git forward <V>`.
                   pub forward_needed: Option<String> }
pub fn move_item(store: &Store, id: &str, code: &str, to: &str, reason: Option<&str>,
                 repo: Option<&Path>) -> Result<Moved>;
pub enum CatchUpOutcome { Merged(String), UpToDate, Conflicts(Vec<String>), Skipped(String) }
pub struct CatchUp { pub code: String, pub branch: String, pub outcome: CatchUpOutcome }
pub fn catch_up(store: &Store, id: &str, sprint: &str, repo: &Path) -> Result<Vec<CatchUp>>;
pub struct SprintClosed { pub sprint: Sprint, pub tagged: Option<String>, pub catch_up: Vec<CatchUp> }
pub fn sprint_close(store: &Store, id: &str, code: &str, carry_to: Option<&str>,
                    repo: Option<&Path>) -> Result<SprintClosed>;
pub struct Forwarded { pub from: String, pub into: String, pub sha: String, pub refs: Vec<String> }
pub fn forward(store: &Store, id: &str, version: &str, repo: &Path) -> Result<Forwarded>;
```

### Behaviour
- **`move_item` (R-1, R-2).** A plain gated move (today's route) unless all hold: automation on;
  `!is_integrated(from) && is_integrated(to)` (entering the integrate role, or skipping past it);
  `to` is not a no-op. Then:
  1. **Preflight**, nothing written:
     - a repository is given, else refuse "integrating CODE merges its branch: run it from the
       project folder";
     - `gate_preview(to)` passes (an override reason passes as it does today, and is recorded);
     - the item branch: the local branches whose `item_code_from_branch` is CODE. None → the
       move proceeds with "no branch: nothing merged" (an item started with `--no-branch`). Two
       or more → refuse, naming them;
     - the line: `line_for(item)`. None (sprints on, no active sprint) → refuse "start a sprint
       first". A missing `integration` branch is created from main, as `start` does;
     - `is_ancestor(branch, line)` → nothing to merge (`already: true`);
     - `merge_preview(line, branch)` not clean → refuse **R-2**: "cannot integrate CODE: merging
       <branch> into <line> conflicts in: <paths>. Merge <line> into <branch>, resolve, commit,
       then move again." The item stays where it was;
     - if the line is checked out, its working tree is clean.
  2. **Git**: `merge_no_ff(line, branch, "Merge <branch> into <line>\n\n<CODE>: <title>\n\nRefs:
     kanbanr:<CODE>")`.
  3. **Board**: the gated move.
  4. If 3 fails: `reset_branch_to(line, old)` (FEAT-183), then the error.
  The item branch is kept (Q3). When `into` starts with `release/`, `forward_needed = Some(<V>)`
  and the CLI prints "release/<V> has a fix the line lacks: kanbanr git forward <V>" (R-4).
- **Batch.** A batch move that `move_item` would merge is refused when automated: "move CODE on
  its own: integrating it merges its branch".
- **`sprint_close`.** Board checks of `sprints::close` first. Then:
  - **Sprints topology**, automated, repo, and `sprint/<SP>` exists:
    1. preflight: `is_ancestor(main, sprint/<SP>)`, else refuse "main has commits sprint/<SP>
       lacks: not a fast-forward"; tag `<SP>` absent (Q4); clean tree if main is checked out;
    2. git: `create_tag(<SP>, sprint/<SP>)`, `fast_forward(main, sprint/<SP>)`;
    3. board: `sprints::close`;
    4. if 3 fails: `reset_branch_to(main, old)`, `delete_tag(<SP>)`.
  - Other topologies: board only (production is the release cut).
  - Then, when `carry_to` names a sprint whose branch exists, `catch_up(carry_to)`.
- **`catch_up` (R-3).** For each item planned into `sprint` that a closed sprint's `carried` lists
  with `to == sprint`, not `is_integrated`, with exactly one item branch:
  - `is_ancestor(sprint/<SP>, branch)` → `UpToDate`;
  - the branch is checked out with a dirty tree → `Skipped("uncommitted changes")`;
  - `merge_preview(branch, sprint/<SP>)` conflicts → `Conflicts(paths)`, branch untouched, and the
    CLI prints `git checkout <branch> && git merge sprint/<SP>` to resolve by hand;
  - else `merge_no_ff(branch, sprint/<SP>, "Merge sprint/<SP> into <branch>\n\nRefs:
    kanbanr:<CODE>")` → `Merged(sha)`.
  Each item is independent; a conflict never undoes another item's catch-up or the sprint change.
  Never rebases, never deletes a branch. `sprint_start` (FEAT-189) calls it after step 3.
- **Release terminal.** FEAT-183's production preflight checks `is_ancestor(main, release/<V>)`
  in place of `merge_is_clean`, and its git step is `fast_forward(main, release/<V>)` after the
  tag. Rollback is unchanged (Q2).
- **`forward` (R-4).** `kanbanr git forward <V>`: the release has a branch; the line is
  `GitModel.line` (refuse if None); `commits_between(line, release/<V>)` empty → "nothing to
  forward"; `merge_preview(line, release/<V>)` conflicts → refuse with paths; else
  `merge_no_ff(line, release/<V>, "Merge release/<V> forward into <line>\n\nRefs: <every
  kanbanr:CODE parsed from those commits>")`. With no Refs found, the message carries
  `[no-ref] forward merge of release/<V>`. FEAT-184's production report keeps listing what a
  patch needs forwarded; kanbanr performs it only when asked (Q1).

### Failure handling
- Every refusal is found in preflight; `merge_no_ff` is the only write before the board, and its
  old tip is kept for `reset_branch_to`.
- `update-ref` with the expected old value fails if the line moved in between: reported, nothing
  changed.
- Catch-ups are per item and reported; they never fail the sprint operation.
- Git's stderr is included in every error. No `push`, ever (FEAT-189 R-5).

### Compatibility
- Automation off (the default): moves, sprint close and promote behave exactly as today.
- `POST …/move` responses gain optional `merged` and `forward_needed` keys.
- `sprint close` JSON gains `tagged` and `catch_up`.

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `integrate_merges_item_branch` (default preset, trunk: finish FEAT-001 → a merge commit on main whose message has `Refs: kanbanr:FEAT-001`; sprints: lands on `sprint/SP-001`; a board failure resets the line) | cli local_mode.rs |
| R-2 | `integrate_merge_conflict_refused` (conflicting edits on main and the item branch → refused, the paths named, status, line tip and working tree unchanged) | cli local_mode.rs |
| R-3 | `carry_over_catch_up_merge` (SP-001 closes carrying FEAT-002; SP-002 starts; `sprint/SP-002` is an ancestor of FEAT-002's branch; branch still exists; a conflicting carried item reports its paths and is untouched) | cli local_mode.rs |
| R-4 | `fixes_forward_merged` (releases on: a defect planned into release v1 at candidate integrates into `release/v1`, the move reports `forward_needed`; `git forward v1` merges into `integration` with the defect's Refs; a second run says nothing to forward) | cli local_mode.rs |
Plus coderepo unit tests: `merge_no_ff_leaves_worktree_untouched`, `fast_forward_refuses_divergence`,
`merge_preview_names_conflicts`; and `sprints_close_fast_forwards_and_tags` (local_mode.rs).

### Implementation tasks
1. **coderepo.** `merge_preview`, `is_ancestor`, `fast_forward`, `commits_between`; make
   `merge_no_ff` follow the contract above. Unit tests listed. Depends on FEAT-183 task 1.
2. **gate_preview.** store.rs public wrapper over `check_gate` on a loaded project. Test: core
   unit, preview equals the move's outcome and writes nothing. Depends on none.
3. **move_item.** gitmodel.rs as specified; dispatch move route calls it with the repository
   FEAT-183 passes; batch refusal. Tests: R-1, R-2. Depends on 1, 2, FEAT-189 tasks 4–5.
4. **catch_up and sprint_close.** gitmodel.rs; `SprintStarted.catch_up` filled by
   `sprint_start`; dispatch close route. Tests: R-3, `sprints_close_fast_forwards_and_tags`.
   Depends on 1, 3, FEAT-189 task 5.
5. **Release terminal.** releases.rs production step per above. Test: FEAT-183's
   `promote_production_*` tests updated for fast-forward. Depends on 1, FEAT-183 task 3, Q2.
6. **forward.** gitmodel.rs `forward`; route; `GitCmd::Forward`. Test: R-4. Depends on 3.
7. **CLI output.** `move`/`start`/`finish` print `merged` and `forward_needed`; `sprint close`
   and `start` print tags and catch-ups. Depends on 3, 4.
8. **Docs.** processes.md (merges by stage, carry-over, forward merges), traceability.md,
   cli.md, http-api.md, SKILL.md, CHANGELOG. Depends on 7.

### Decisions (19 Oct 2026: every recommended answer accepted)
- **Q1.** Forward merges: automatic, or on request? Decided: **reported automatically,
  performed by `kanbanr git forward <V>`**, consistent with FEAT-184.
- **Q2.** FEAT-183 merges the release branch into main `--no-ff`; this spec fast-forwards. Which?
  Decided: **fast-forward**, so main's tip is exactly the tagged, tested commit. For a patch
  of an older release (main has moved on), tag without touching main.
- **Q3.** Delete the item branch after the integrate merge? Decided: no; FEAT-191 reports
  merged branches of finished items so the user deletes them.
- **Q4.** The tag a sprints-only close makes: Decided: the sprint code (`SP-004`).

- **Q5 (19 Oct 2026).** An item that would complete because its last task was ticked, where
  that move would merge its branch (git model on): merge, hold, or leave? Decided: **hold** — the
  task is recorded, the item stays, and the write says "run `kanbanr move <CODE> <stage>` from the
  project folder to integrate it". No merge happens without the code repository in hand. Test:
  `auto_complete_holds_when_it_would_merge` (core).

### Affects docs
- [FEAT-183](/p/kanbanr/feature/FEAT-183), [FEAT-184](/p/kanbanr/feature/FEAT-184),
  [FEAT-188](/p/kanbanr/feature/FEAT-188), [FEAT-189](/p/kanbanr/feature/FEAT-189),
  [FEAT-191](/p/kanbanr/feature/FEAT-191)
- docs/src/using/processes.md, docs/src/using/traceability.md, docs/src/reference/cli.md,
  docs/src/reference/http-api.md, docs/src/architecture/overview.md, skill/kanbanr/SKILL.md
