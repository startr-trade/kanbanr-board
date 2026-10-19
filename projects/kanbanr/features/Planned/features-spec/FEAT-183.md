# Release stages and promotion

Today a release is planned or cut. A team that deploys a release branch to test and staging environments before production has nowhere to record where the release is, and the cut, which is the production event, does nothing to the code repository beyond an optional tag.

Scope:
- **A release has a current stage.** It is configurable per project, with a default list of `candidate` → `test` → `staging` → `production`. The stage is recorded with who moved it and when, as history.
- **`kanbanr release promote <VERSION> <stage>`** moves a release to the next or a named stage. Moving to `production` is the cut: it ships the finished items, writes the notes, tags the code repository, and merges the release branch into the main branch. If the merge cannot be clean, it refuses rather than forcing.
- **Candidate creates a branch.** Promoting to `candidate` (or `release add --branch`) creates `release/<VERSION>` from the integration branch the project names.
- **Operations follows the cut.** Items enter the project's terminal status only through the production stage of a release they are planned into. The existing `in_release` gate check plus the cut cover this; the docs say so.

## Design

### Summary
A release gains a **stage**: one of a project's configured list, by default `candidate → test →
staging → production`. Every move between stages is recorded with who made it and when.
`kanbanr release promote <V> [<stage>]` moves a release forward:
- to the next stage, or to the named one;
- to **candidate**, it creates `release/<V>` from the integration branch;
- to **production**, it is the cut: the board ships the release's items and writes the notes; the
  code repository gets a tag, and the release branch is merged into the main branch.

The code-repository work runs in core's new `coderepo` module (moved there from the CLI's `scm.rs`
under FEAT-176), so the CLI and the daemon behave the same way. **Nothing changes unless
everything can**:
1. preflight the board and the repository first;
2. do the git steps;
3. make the board change;
4. if the board change still fails, undo the git steps.

### Components and files
- `api/crates/kanbanr-core/src/releases.rs`:
  - `Release` gains `stage`, `stages` (history), `branch` and `extra`;
  - `promote`, `promote_plan` and `cut_preview` are added;
  - `cut` becomes the production step.
- `api/crates/kanbanr-core/src/config.rs`: `Cadence` gains `release_stages: Vec<String>`,
  `integration_branch: Option<String>` and `main_branch: Option<String>`.
- `api/crates/kanbanr-core/src/coderepo.rs` (new; shared with FEAT-176): shells out to `git`, as
  scm.rs does. It holds `repo_root_in`, `default_branch`, `branch_exists`, `create_branch_from`,
  `tag_exists`, `create_tag`, `is_clean`, `merge_is_clean` (`git merge-tree --write-tree`, git ≥
  2.38), `merge_no_ff`, `reset_branch_to`, `delete_tag` and `log_between`.
- `api/crates/kanbanr-core/src/dispatch.rs`: `POST /projects/:p/releases/:v/promote {stage?, by}`.
  It reaches the code repository only when the caller passes one (see Q1).
- `api/crates/kanbanr-cli/src/main.rs`: `release promote <V> [<stage>]`; `release add --branch`;
  `cut --tag` remains a synonym for `promote <V> production`.
- `api/crates/kanbanr-server`: passes the repository root the daemon was started in (Q1).
- `web/src/types.ts`: `Release` gains `stage` and `stages` (shown by FEAT-185).
- Docs: processes.md "Sprints and releases"; cli.md; CHANGELOG.

### Data model
```rust
// releases.rs
pub struct Release { /* existing fields */,
    /// Where the release is now, from `cadence.release_stages`. Empty until first promoted
    /// (a release added before stages existed reads as "not yet a candidate").
    #[serde(default, skip_serializing_if = "String::is_empty")] pub stage: String,
    /// Every stage change, oldest first.
    #[serde(default, skip_serializing_if = "Vec::is_empty")] pub stages: Vec<StageChange>,
    /// The code branch, set when promoted to the first stage (`release/<V>` by default).
    #[serde(default, skip_serializing_if = "String::is_empty")] pub branch: String,
    #[serde(flatten, default, skip_serializing_if = "Extra::is_empty")] pub extra: Extra,
}
pub struct StageChange { pub stage: String, pub by: String, pub at: String }
// config.rs — Cadence
#[serde(default, skip_serializing_if = "Vec::is_empty")] pub release_stages: Vec<String>, // default: candidate, test, staging, production
#[serde(default, skip_serializing_if = "Option::is_none")] pub integration_branch: Option<String>, // default: the repo's default branch
#[serde(default, skip_serializing_if = "Option::is_none")] pub main_branch: Option<String>,        // default: the repo's default branch
```
The **last** stage is always the cut. A stage list must have at least one entry and no
duplicates; `config cadence --release-stages a,b,c` validates both.

### Behaviour
- `promote(store, project, version, to: Option<&str>, by, repo: Option<&Path>) -> Result<Promoted>`:
  - The target is the next stage after the current one, or `to`, which must come later in the list.
    Promotion only moves forward; Q2 asks about backward moves.
  - **Into the first stage** (`candidate`), with a repository:
    - creates `release/<V>` from the integration branch;
    - refuses if the branch exists;
    - records `branch`.
  - **Into a middle stage**: a board change only.
  - **Into the last stage** (production):
    1. **Preflight.** `cut_preview` must show every planned item would ship or carry over. That's
       today's `ship_to` without writing; reported, never forced. The repository must have a clean
       working tree, `branch` must exist, the tag `<V>` must not exist, and the merge of `branch`
       into `main_branch` must be clean (`merge_is_clean`). Any failure refuses with its reason,
       and **nothing** changes (R-4).
    2. **Git.** `create_tag(<V>, on branch tip)`, then `merge_no_ff(branch into main_branch)`,
       remembering main's previous commit.
    3. **Board.** `cut(...)`, as today: ship, carry over, write the notes, mark shipped. Plus
       `stage = production` and a history entry.
    4. If step 3 fails, `reset_branch_to(main, previous)` and `delete_tag(<V>)`, then return the
       error.
  - With **no repository** (Q1), promoting into the first or last stage refuses ("needs the code
    repository: run it from the project folder"). Middle stages are allowed.
- Each step records a `StageChange {stage, by, at}`. `by` is the commit identity, as for verdicts.
- `release list` and the Releases page show the stage. `report_all` includes it.
- **Docs:** items reach the terminal status only through the production stage of a release they
  are planned into, enforced by the existing `in_release` gate plus the cut.

### Failure handling
- Preflight covers every refusal that can be known in advance.
- The git steps are ordered so a failure leaves at most a tag, which the rollback deletes.
- A board write failure after the git steps triggers the rollback.
- Git output goes into the error, so the user sees git's reason.

### Compatibility
- New optional fields, plus an `extra` passthrough so a future binary's fields survive.
- `Release` has no `extra` in 0.1.7, so a 0.1.7 binary that rewrites releases.yaml drops `stage`,
  `stages` and `branch`. That's acceptable before 1.0. The release notes say so.
- `cut --tag` keeps working.

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `release_stage_recorded_with_history` | core lib.rs |
| R-2 | `promote_candidate_creates_branch` (scratch code repo) | cli local_mode.rs |
| R-3 | `promote_production_cuts_tags_merges` | cli local_mode.rs |
| R-4 | `promote_production_refuses_unclean_merge` (conflicting commits on main and release, then board, tags and main untouched) | cli local_mode.rs |
Plus: coderepo unit tests (merge_is_clean on clean and conflicting repos, rollback), and a board
failure after the git steps rolling back.

### Implementation tasks
1. **coderepo.rs.** The shell-git helpers listed above, with a `scratch_repo` test fixture. Tests:
   `coderepo::tests::*`. Depends on: FEAT-176 task "move scm.rs git plumbing to core" (or done
   here first, then FEAT-176 removes the CLI copy).
2. **Model.** Add the `Release` fields, `StageChange`, `extra`, and the `Cadence` fields with their
   defaults and validation; `config cadence --release-stages` and the branch flags. Test: R-1
   (stage history round trip). Depends on: none.
3. **Logic.** releases.rs: `cut_preview`, `promote`, with the ordering and rollback above. Tests:
   R-1, plus a rollback unit test with a failing board step. Depends on 1, 2.
4. **Route.** dispatch.rs `POST …/releases/:v/promote`; commit message "promote release <V> to
   <stage>". Depends on 3.
5. **CLI.** `release promote`; `release add --branch`; `cut --tag` maps to promote production;
   the CLI passes the repository root from its working directory. Tests: R-2, R-3, R-4. Depends
   on 4.
6. **Daemon.** `kanbanr serve` records the repository root it was started in, when the marker
   there names this board's project, and passes it for that project only. Test: view_daemon.rs
   promote through the daemon. Depends on 4, and on Q1's answer.
7. **Docs.** processes.md, cli.md, SKILL.md command reference, CHANGELOG with the docs sync. Depends
   on 5.

### Open questions
- **Q1.** The daemon doesn't know where a project's code repository is. How should it promote?
  - Recommended: **the daemon uses the repository it was started in**, when that folder's marker
    names the project. Otherwise first-stage and production promotions from the monitor refuse
    with "use the CLI from the project folder".
  - Alternative: record the path in the project's config. It's shared through the board's remote,
    but a path is specific to one machine.
- **Q2.** Can a release move back a stage (staging to test after a failed check)?
  - Recommended: yes, as `promote <V> <earlier stage>` with a required `--reason`, recorded in the
    history. Never back from production.
- **Q3.** Should the integration branch and the main branch default to the same branch (the
  repository's default)?
  - Recommended: yes. Teams that integrate on `develop` set `cadence.integration_branch`.

### Affects docs
docs/src/using/processes.md (Sprints and releases), docs/src/reference/cli.md,
docs/src/architecture/overview.md (releases).
