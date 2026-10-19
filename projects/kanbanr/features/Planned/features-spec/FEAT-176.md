# Refactor: domain logic lives in kanbanr-core; front ends are thin wrappers

kanbanr-cli carries a large share of the code (about 12k lines, against about 25k in kanbanr-core). Some of it is behaviour rather than argument parsing and output formatting. Every front end (CLI, monitor server, editor extension, any future one) should get identical behaviour from one library, and each should be packageable on its own.

Scope:
- Move domain behaviour from kanbanr-cli into kanbanr-core's public API. kanbanr-cli keeps argument parsing, output rendering and process concerns only.
- Keep kanbanr-server equally thin.
- Add an architecture test that fails when a front-end crate implements domain logic, measured by imports of core internals or of parser and validation code outside the public API.

## Design

### Summary
kanbanr-cli (11.4k lines) holds a good deal of behaviour, and so does the daemon. The worst case
is the write recipe (lock → dispatch → activity → events → commit → push), which exists twice:
once in the CLI's backend.rs and once in the server's write.rs.

This item moves each piece of behaviour into kanbanr-core's public API, as functions that take
plain inputs, so the CLI and the daemon call the same code. The front ends keep three jobs:
- argument parsing and output rendering;
- process concerns: installing, self-update, the skill, the editor extension, Claude Code hook
  settings;
- collecting facts from outside the board, such as code-repository state or a test run's output,
  which they hand to core to decide on.

An architecture test keeps it that way. Behaviour is unchanged: every existing CLI and server test
passes **unmodified** (R-1).

### Principles
- Core **decides**, the front end **acts**.
  - Example: commit-guard policy becomes `scm::commit_verdict(&RepoFacts, &Project) -> Verdict`.
    The CLI collects the `RepoFacts` (branch, merge state, message) and prints the verdict as
    hook JSON.
- **One copy.** The CLI and the server both call `core::write::apply`. The Workflow-file → workflow
  body conversion exists once, as `WorkflowFile::to_request()`.
- **Code-repo git commands move into core** as `coderepo.rs` (shell git, as scm.rs does now). Then
  the daemon can do what the CLI does (FEAT-183/185). Board git stays in `git.rs` (libgit2).
- Text heuristics about how Claude Code issues a commit (heredoc and quote parsing, about 330
  lines) **stay in the CLI**. They concern the front end's own input, not board behaviour.

### What moves (themes, from the inventory)
| # | Theme | From (CLI or server) | To (core) |
|---|---|---|---|
| 1 | Write recipe | backend.rs 145–271, server write.rs 28–119 | `write::apply(store, dir, policy, method, path, body, sender) -> Result<Applied>`; `write::project_of`, `item_of` |
| 2 | Code-repo git | cli scm.rs `git`, `repo_root_in`, `current_branch`, `merge_in_progress`, `has_commits`, `default_branch` | `coderepo.rs`, the same functions plus FEAT-183's tag, merge and branch helpers |
| 3 | Moving through the workflow | main.rs `first_active_status`, `branch_status`, `status_path`, `require_reachable`, finish's terminal choice | `ProjectConfig::{first_active_status, branch_status, path_between, finish_target}`; `flow::plan_start`, `flow::plan_finish` |
| 4 | Commit and branch policy | `run_guard`, `run_check_msg`, `validate_doc_and_adr_refs`, `run_check_branch` (decisions only) | `scm::{commit_verdict, branch_verdict, validate_trailers}` over a `RepoFacts` struct |
| 5 | Test evidence | `parse_test_results`, `run_capture` op planning, `run_tests` stale-evidence planning, `run_sources` | `evidence::{parse_results, plan_capture, plan_stale_tests(repo_search: &dyn Fn(&str)->bool), plan_sources}` |
| 6 | Process library | `resolve_process`, `personal_only`, `run_process_list` merge, `projects_behind`, `project_drift`, three hand-built workflow bodies | `library::{resolve(store, name, personal_dir), list(store, personal_dir), behind(store, name, lib, rev), drift(store, project, personal_dir)}`; `WorkflowFile::to_request()`; `Store::process_drift` gains a personal dir |
| 7 | Documents generated | `retro_markdown`, retro write scaffold, `definition_template` | `retro::markdown(&Retro)`, `retro::scaffold()`, `models::definition_template(kind)` |
| 8 | Small rules | `print_board`'s displayed fallback (also server routes.rs 243), activity "ongoing" filter (server routes.rs 229–266), `days_ago` parsing (twice), `verdict_author`, Defect field merge, `found_in` as one write, ADR `--for` filter, batch normalization, init marker-conflict rule, `ask_the_user`, `marker_path`/`portable_path` | `ProjectConfig::board_states()`, `activity::read_filtered`, `report::parse_since`, `git::verdict_author`, `defect::merge`, one `feature.add` with `found_in`, `adr::for_item_filter`, `batch::normalize`, `project::Marker::{may_repoint, render}`, `project::setup_questions` |
| 9 | Issue mirror orchestration | cli mirror.rs `enable`, `status`, `sync_inner`, `link`, `pull` | `mirror::{enable, status, sync, link, pull}` over a core `IssueTracker` trait; the `gh` adapter stays in the CLI |
| 10 | Docs guard policy | `run_docs_guard`, `board_path_for`, `belongs_on_the_board` | `claude::{belongs_on_board, board_path_for}` |
| 11 | Server duplicates | `export_feature` copy, `content_type_for` copy, string-matched error codes | dispatch export; `docs::content_type`; `CoreError::status()` |
| 12 | `check` composition | Command::Check scope and merge, `check_definition_file` parse and note | `readiness::check_board(store, project, scope) -> CheckReport`; `readiness::check_definition_text(yaml)` |

**Staying in the CLI:**
- `self_update.rs`, `skill.rs`, `editor.rs`, `hooks.rs`;
- `run_serve`/`open`;
- shell-line parsing for the guard;
- every renderer and printer;
- the `gh` adapter;
- the `git blame` and `git grep` calls (as facts handed to core).

### The architecture test (R-2): `architecture::front_ends_are_thin`
A test in `api/crates/kanbanr-core/src/architecture.rs` (cfg(test)). It reads the front-end crates'
sources and manifests with `std::fs` from `CARGO_MANIFEST_DIR/..` and fails, naming each offender,
in four cases:
1. **Dependencies.** `kanbanr-cli` or `kanbanr-server` lists `git2`, `serde_yaml` or
   `ears-classifier` as a direct dependency. Board YAML and git belong to core.
   - The CLI's current `serde_yaml` uses (YAML **output** for `--export` and `show`) move to core
     helpers such as `WorkflowFile::to_yaml()` and `config::to_yaml`.
2. **Board model parsing.** A front-end source deserializes a board model type:
   `from_str::<FeatureDefinition|WorkflowFile|Charter|ProjectConfig|Release|Sprint>` or
   `from_value::<…>` for those types.
3. **Hand-built domain values.** A front-end source constructs a domain struct literal
   (`Transition {`, `ApprovalEvent {`, `Signoff {`, `ProcessSource {`) or assigns
   `.status =` / `.definition =` on a model value.
4. **Calling dispatch directly.** The front end calls `kanbanr_core::dispatch::dispatch` anywhere
   except the single entry point allowed per crate: CLI `backend.rs`, server `routes.rs`.

The patterns live in the test as a list, each with the reason it is banned. An exception needs a
comment on the line itself, `// architecture: allowed because …`. **Seen failing** (ADR-0008): the
test is first run against today's tree, and its offender list is recorded in the item before the
moves start.

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `cargo test --workspace` with **no test file changed**: CLI local_mode.rs (32), view_daemon.rs (5), server unit tests, core (194) | workspace |
| R-2 | `architecture::front_ends_are_thin`, red on today's tree and green at the end | core |
Also: each moved function gets core unit tests beside it (moved from the CLI's unit tests where
they exist: guard parsing stays, `parse_test_results` moves, `portable_path` moves), and `make ci`
is run after every theme.

### Implementation tasks
Order: each task ends green on `cargo test --workspace` and is committed on its own.
1. **Architecture test first.** architecture.rs with the rules; record today's offenders on the
   item. Test: R-2, red, with the list recorded. Depends on: none.
2. **Write recipe (theme 1).** `core::write::apply`; backend.rs and server write.rs both call it,
   and the duplicates are deleted. Tests: R-1 plus moved unit tests. Depends on 1.
3. **coderepo.rs (theme 2).** Move the git plumbing; CLI scm.rs keeps only hook-file install.
   Depends on 1.
4. **Workflow movement (theme 3).** The `ProjectConfig` methods and `flow::plan_start` /
   `plan_finish`; run_start and run_finish become fact collection plus printing. Depends on 3.
5. **Commit and branch policy (theme 4).** `RepoFacts`, `commit_verdict`, `branch_verdict`,
   `validate_trailers`. Depends on 3.
6. **Evidence (theme 5).** Depends on 2.
7. **Process library (theme 6).** Plus `WorkflowFile::to_request` and `to_yaml`. Depends on 2.
8. **Generated documents and small rules (themes 7, 8, 10, 12).** Depends on 2.
9. **Mirror orchestration (theme 9).** Depends on 2.
10. **Server duplicates (theme 11).** Depends on 2.
11. **Drop the CLI's serde_yaml dependency and finish.** R-2 green; architecture docs updated
    (`docs/src/architecture/overview.md` crate responsibilities); CHANGELOG. Depends on 4–10.

### Decisions (19 Oct 2026: every recommended answer accepted)
- **Q1.** Shell-line parsing for the commit guard (about 330 lines): keep it in the CLI as
  front-end input parsing, or move it to core?
  - Decided: **keep it in the CLI**.
- **Q2.** Should the CLI stop calling core through HTTP-like strings (`dispatch("POST",
  "/projects/…")`) and use typed functions?
  - Decided: **not in this item**. It's a large, separate change. The architecture test allows
    `dispatch` only in backend.rs.
- **Q3.** Order relative to the other items:
  - Decided: tasks 1–3 **first**, because FEAT-183 needs `coderepo.rs` and `write::apply`.
  - The rest after FEAT-185, so the moves aren't made twice.

### Affects docs
docs/src/architecture/overview.md (crate responsibilities), docs/src/architecture/testing.md
(architecture test), CONTRIBUTING.md (where new behaviour goes).
