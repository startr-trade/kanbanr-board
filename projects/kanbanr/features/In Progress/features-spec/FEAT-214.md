# Agent scopes: what a sub-agent may do, enforced by kanbanr

## Why
On 21 Oct 2026 the work was split across sub-agents (design agents, build agents in git worktrees).
Their limits lived only in each brief, as prose. Two failures followed from that:
- the briefs said "never write to the board", to keep tests away from the real board; so a build
  agent could not record its own progress, and FEAT-212's tasks read "Not started" while six of its
  commits were in;
- relaxing that by prose (agents may now record task states and tests on their own item) is still
  only as good as the agent's discipline.

The user (21 Oct 2026): "never write to the board is not the answer. We need boundaries defined for
the sub-agents precisely so that they do what is supposed to be allowed for them to do."

## The boundaries (as agreed for a build agent)
| Area | Allowed | Refused |
|---|---|---|
| Read the board | everything | — |
| Its item's record | `task state` on its item's todo-lists; `test` evidence on its item's requirements | moves, approvals, sign-offs, definitions, specs, other items, batch, docs |
| Code | commits on its item's branch only, each naming the item | commits on main, `sprint/*`, `release/*`, or any other item's branch |
| Remote | nothing | `git push`, `kanbanr sync`, pushing anything else |
| Tests | temporary boards only (the test fence) | a test reaching a real board |

A design agent's scope is read-only: every board write and every commit is refused.

## What it adds (to be designed)
- **A scope, issued per agent**: the item, the allowed operations, the branch, an expiry; recorded on
  the board (visible, auditable) and written into the agent's worktree where kanbanr reads it.
- **Enforced in three places**: the core write path (a write outside the scope is refused, naming
  the boundary it crossed); the commit guard and git hooks (commits outside the branch refused);
  pushing refused.
- **Attribution**: writes made under a scope are recorded as the person, by the agent for the item.
- **Roles**: `design` (read-only) and `build` (the table above); the skill tells Claude to issue the
  right scope before starting a sub-agent, and to brief the agent with it.
- **Drift**: a build scope expects its item's tasks to move; commits on the branch newer than the
  item's last task change are reported by name (Stop hook, `git doctor`, session start).

## Design

### Summary
FEAT-214 adds **agent scopes**. A scope is a board record that says what one sub-agent may do. It is bound to that agent's git worktree, and kanbanr enforces it at four points:

1. **The core write path.** `write::apply` checks every board write before dispatch.
2. **The commit guard and git hooks.** These refuse any commit outside the scope's branch or item.
3. **Pushing.** `git::sync_all` refuses to run from an agent worktree, and a new `pre-push` hook plus the Bash guard refuse `git push`.
4. **The CLI command gate.** Commands that write outside `write::apply` (for example `identity`, `hooks`, `migrate`, `serve --allow-writes`) are refused in an agent worktree.

The flow:
- The coordinator runs `kanbanr scope issue build FEAT-214`. kanbanr records `SC-007` on the board and prints the boundary table for the brief, including the claim command.
- The agent, started with `isolation: worktree`, runs `kanbanr scope claim SC-007` as its first step. This binds the scope on the board to its worktree path and writes a pointer file into the worktree's own git directory.
- From then on every kanbanr process, git hook and Claude Code guard started in that worktree resolves the scope. Anything outside it is refused, and the refusal names the boundary it crossed.
- Writes made under the scope are recorded as the person, "by the agent for FEAT-214", in the activity entry, the event, the board commit trailer and the code commit trailer.
- Drift is reported by name in three places: the Stop hook, `git doctor` and session start. Drift means commits on the scope's branch made after the item's tasks last changed.

The main session, and any board with no scopes, behave exactly as today. The test fence (FEAT-195) is untouched.

### Key decisions (with reasons)
**D1. Pointer file in the worktree's git dir, not an env var and not the worktree root.** The file is `<git-dir>/kanbanr-scope.yaml`, where git-dir is what `git rev-parse --git-dir` returns, i.e. `.git/worktrees/agent-x/`.
- **Why not an env var:** the Agent tool cannot set env vars for a sub-agent. Each Bash call is a fresh shell, so the agent would have to prefix every command. Git hooks would not see the variable, and `env -u` removes it.
- **Why not the worktree root:** a file at the worktree root can be committed by `git add -A`, removed by `git clean -fdx`, and shows in `git status`.
- **Why the git dir:** it is private to that one worktree. It cannot be committed, survives `clean`, `stash -u` and checkouts, and disappears when Claude Code removes the worktree.

**D2. The board is the authority; the file is only a pointer.** The file holds `{scope, project}` and nothing else. Role, operations, branch, expiry and revocation are always read from the board. Resolution fails closed:
- if a scope bound to this worktree loses its file, writes are still refused;
- if the file names a scope bound elsewhere, writes are refused;
- an agent worktree with no claimed scope is refused, on any board that has scopes.

**D3. Binding by claim.** The coordinator cannot write into the worktree before Claude Code creates it, so the agent's first command binds it. An agent that skips the claim gets M3 on every write and commit, and the message tells it what to run. `issue --worktree PATH` binds at once when the coordinator already knows the path.

**D4. Every scoped agent runs in its own worktree, design agents included.** A scope belongs to a worktree, never to the main checkout, which stays exactly as today.

**D5. Batch is a container, not an operation.** The agreed table lists "batch" as refused, but `kanbanr capture` (the PostToolUse hook) and `kanbanr tests --write` record evidence through `POST …/batch`. So a batch is allowed only when **every** op in it is in scope. Capture filters its ops down to the scope's item before writing. Nothing outside the table can be smuggled in a batch. **This departs from the table's wording; please confirm.**

**D6. Auto-advance is held under a scope.** If a scoped `task.state` completes the item's last task, the item stays where it is, with M13. Moves stay the coordinator's.

**D7. Boards inside the system temp dir are never governed.** This replaces the earlier rule ("a board with no scope records is never governed"). The fence alone is no help here: an agent could set `KANBANR_BOARD_FENCE=/`, so the check uses `std::env::temp_dir()` directly. Why this matters:
- Build agents run `cargo test` inside their worktrees. Scratch boards live in temp (FEAT-195 R-2), so those tests are unaffected.
- Integration tests that put their boards in temp would also be ungoverned. So the R-tests put their scope-issuing boards under `CARGO_TARGET_TMPDIR`, with `KANBANR_BOARD_FENCE` unset for those runs only, and FEAT-195's own tests are unchanged.

### Components and files
| File | Change |
|---|---|
| `api/crates/kanbanr-core/src/agentscope.rs` (new) | Model, storage, resolution, checks, brief, trailer, drift. |
| `api/crates/kanbanr-core/src/lib.rs` | `pub mod agentscope;` |
| `api/crates/kanbanr-core/src/write.rs` | `apply` resolves the process scope; new `apply_as` does the checks, attribution, push policy override and auto-advance hold. |
| `api/crates/kanbanr-core/src/git.rs` | `sync_all` and `set_identity` refuse in an agent context; new `is_clean(dir) -> Result<(), Vec<String>>`. |
| `api/crates/kanbanr-core/src/coderepo.rs` | `worktree_facts(cwd)`; `commits_since(root, range, since) -> Vec<Commit>` (`git log --since`). |
| `api/crates/kanbanr-core/src/models.rs` | `Task` gains `changed_at: Option<String>` (serde default, skipped when None). |
| `api/crates/kanbanr-core/src/store.rs` | `set_task_state_on` stamps `changed_at`. `set_task_state_reported` and `apply_batch_with` take `hold: Option<&str>`; Some skips `auto_advance_on` and returns that text as held. |
| `api/crates/kanbanr-core/src/dispatch.rs` | Scope routes; the task route and batch route read `hold_advance` from the body; `commit_message` entries for the scope routes. |
| `api/crates/kanbanr-core/src/activity.rs`, `eventing.rs` | `by_agent: Option<ByAgent>` on `Activity` and `Event`; `activity::append_by`; `eventing::record_by`. The old functions delegate with None. |
| `api/crates/kanbanr-core/src/gitdrift.rs` | `scan` appends `agentscope::drift_issues`. |
| `api/crates/kanbanr-core/src/guards.rs` | `Guards.agents: AgentGuards`. |
| `api/crates/kanbanr-core/src/architecture.rs` | New rule `board-commit` (see T4). |
| `api/crates/kanbanr-cli/src/main.rs` | `Command::Scope(ScopeCmd)`, `GitCmd::CheckPush`, `command_access`, `scope_gate`, `scoped_command_refusal`. Scope checks are added to `run_guard`, `run_check_msg`, `run_check_branch`, `run_commit`, `run_docs_guard`, `run_capture` and `run_serve`. |
| `api/crates/kanbanr-cli/src/scm.rs` | `HOOKS` gains `("pre-push", "check-push")`; `hooks_installed` keeps checking the two commit hooks; new `push_hook_installed`. |
| `api/crates/kanbanr-cli/src/backend.rs` | Outside-core writes (`sync`, `write_doc_asset`, `rebuild_index`, `migrate`, `emit_test_event`, remotes) call `agentscope::outside_core_refusal(cwd)` first. |
| `skill/kanbanr/hooks/` | `session-start.sh`/`.ps1`, `stop-check.sh`/`.ps1`, `README.md`. |
| `skill/kanbanr/SKILL.md` | Sub-agents subsection. |
| `web/src/` | `types.ts`, `api.ts`, new `agentScopes.ts`, `pages/FeaturePage.tsx`, `pages/WorkflowPage.tsx`, `pages/BoardPage.tsx`; new `web/scripts/check-agent-scopes.mjs` and `package.json` script `check:agent-scopes`. |
| Generated | `docs/src/reference/openapi.json` regenerated: `Activity.by_agent` and `Task.changed_at` are in published types. |

### Formats
**Board record**, `projects/<id>/scopes.yaml`, oldest first, never trimmed:
```yaml
- id: SC-007
  role: build                      # design | build
  item: FEAT-214
  operations: [task.state, test.state, commit]   # design: []
  branch: feat/FEAT-214-agent-scopes-what-a-sub-agent-may-do   # build only
  base: 8404bd2…                   # tip of `branch` at issue; drift counts base..branch
  issued_by: Venkatraman B         # git::identity name
  issued_at: 2026-10-21T10:00:00Z
  expires_at: 2026-10-21T18:00:00Z
  note: "TL-001 T1–T4"             # optional
  worktree: .claude/worktrees/agent-a88e8d72cf7a084b6   # set by claim; relative to the main worktree root
  claimed_at: 2026-10-21T10:01:12Z
  revoked_at: …                    # optional, with revoked_by and revoked_reason
```
The worktree path is stored relative, so the public board carries no home paths. State is derived and never stored:
- `issued`: not claimed;
- `active`: claimed and not expired;
- `expired`: `now >= expires_at`;
- `revoked`: `revoked_at` is set (revoked wins over expired).

**Pointer file**, `<worktree git-dir>/kanbanr-scope.yaml`:
```yaml
scope: SC-007
project: kanbanr
```

**Trailer.** The same trailer goes on board commits and code commits:
`Agent-Scope: SC-007 (build, by the agent for FEAT-214)`

**Operation vocabulary.** It matches the batch op names. Adding an operation later means one enum variant plus its route mapping:

| Op | What it covers |
|---|---|
| `task.state` | `PUT /projects/:p/features/:item/todos/:t/tasks/:k`, or batch op `task.state` with `feature == item` |
| `test.state` | `PUT /projects/:p/features/:item/tests/:r/:t`, or batch op `test.state` with `feature == item` |
| `commit` | Code commits on `branch` whose message names `item` |
| (implicit) | Reads, always allowed. `scope.claim` is allowed only from an unbound agent worktree. |

Every other write route maps to a label taken from `dispatch::commit_message` and is refused.

### Public signatures (`agentscope.rs`)
```rust
pub const SCOPES_FILE: &str = "scopes.yaml";
pub const POINTER_FILE: &str = "kanbanr-scope.yaml";
pub const TRAILER: &str = "Agent-Scope";
pub const AGENT_WORKTREES: &str = ".claude/worktrees";
pub const DEFAULT_HOURS: u32 = 8;
pub const MAX_HOURS: u32 = 72;

pub enum Role { Design, Build }                       // parse/name; operations(): preset
pub enum Operation { TaskState, TestState, Commit }   // as_str/parse "task.state"…
pub enum ScopeState { Issued, Active, Expired, Revoked }
pub struct Scope { pub id, project, role: Role, item, operations: Vec<Operation>, branch: Option<String>,
  base: Option<String>, issued_by, issued_at, expires_at, note: String, worktree: Option<String>,
  claimed_at: Option<String>, revoked_at: Option<String>, revoked_by: Option<String>, revoked_reason: Option<String> }
impl Scope { pub fn state(&self, now: &str) -> ScopeState; pub fn by_agent(&self) -> ByAgent;
             pub fn allows(&self, op: Operation, item: &str) -> bool; }
#[derive(Serialize, Deserialize)] pub struct ByAgent { pub scope: String, pub role: String, pub item: String }
// Display: "by the agent for FEAT-214 (SC-007)"
pub struct PointerFile { pub scope: String, pub project: String }
pub struct WorktreeFacts { pub root: PathBuf, pub git_dir: PathBuf, pub main_root: PathBuf,
                           pub linked: bool, pub branch: Option<String> }
pub enum ProcessScope { Unscoped, Scoped(Scope), Refused { why: String, may_claim: bool } }
pub struct Requested { pub op: Option<Operation>, pub project: String, pub item: Option<String>, pub label: String }
pub struct Refusal(pub String);                       // Display = the message

// storage + lifecycle (dispatch routes call these)
pub fn load(store: &Store, id: &str) -> Result<Vec<Scope>>;
pub fn load_all(store: &Store) -> Result<Vec<Scope>>;
pub struct IssueRequest { pub role: Role, pub item: String, pub hours: Option<u32>, pub note: String,
                          pub worktree: Option<PathBuf> }
pub struct Issued { pub scope: Scope, pub brief: String, pub branch_created: bool }
pub fn issue(store: &Store, id: &str, req: &IssueRequest, by: &str, repo: Option<&Path>, now: &str) -> Result<Issued>;
pub fn claim(store: &Store, id: &str, scope: &str, wt: &WorktreeFacts, now: &str) -> Result<Scope>;
pub fn revoke(store: &Store, id: &str, scope: &str, by: &str, reason: &str, now: &str) -> Result<Scope>;
pub fn renew(store: &Store, id: &str, scope: &str, hours: u32, now: &str) -> Result<Scope>;
pub fn active<'a>(scopes: &'a [Scope], now: &str) -> Vec<&'a Scope>;   // expiry is derived; nothing is rewritten

// resolving the active scope for a process
pub fn read_pointer(git_dir: &Path) -> Option<PointerFile>;
pub fn write_pointer(git_dir: &Path, p: &PointerFile) -> std::io::Result<()>;
pub fn resolve_with(scopes: &[Scope], wt: Option<&WorktreeFacts>, pointer: Option<&PointerFile>, now: &str) -> ProcessScope; // pure
pub fn resolve(store: &Store, cwd: &Path) -> ProcessScope;              // facts + resolve_with
pub fn agent_context(cwd: &Path) -> Option<WorktreeFacts>;              // pointer present or under AGENT_WORKTREES; no board needed
pub fn outside_core_refusal(cwd: &Path, what: &str) -> Option<String>;  // M11 when agent_context is Some

// checking
pub fn requested(method: &str, path: &str, body: Option<&Value>) -> Vec<Requested>;
pub fn check(scope: &Scope, req: &[Requested], now: &str) -> Result<(), Refusal>;
pub fn commit_verdict(p: &ProcessScope, facts: &scm::RepoFacts, now: &str) -> scm::Verdict;
pub fn push_verdict(p: &ProcessScope) -> scm::Verdict;
pub fn retain_permitted(scope: &Scope, ops: Vec<Value>) -> (Vec<Value>, usize);
pub fn trailer(scope: &Scope) -> String;
pub fn with_trailer(message: &str, scope: &Scope) -> String;            // idempotent
pub fn brief(scope: &Scope, project: &Project) -> String;               // markdown boundary table

// drift
pub struct Drift { pub scope: String, pub item: String, pub branch: String, pub since: String, pub commits: Vec<coderepo::Commit> }
pub fn last_task_change(item: &FeatureItem) -> Option<String>;          // max Task.changed_at
pub fn drift(store: &Store, id: &str, root: &Path, now: &str) -> Result<Vec<Drift>>;
pub fn drift_issues(store: &Store, id: &str, root: &Path, now: &str) -> Vec<doctor::Issue>;
```

**`resolve_with` rules, in order:**
1. If `scopes` is empty, the answer is `Unscoped`. A board that never used scopes behaves as today. (`resolve` also returns `Unscoped` for boards under `temp_dir()`, D7.)
2. If there is no work tree, the answer is `Unscoped`.
3. If a pointer is present and names a scope on this board:
   - project mismatch, or `scope.worktree` ≠ this worktree's path relative to `main_root`: `Refused` (M4);
   - revoked: `Refused` (M6);
   - expired: `Refused` (M5);
   - otherwise `Scoped`.
4. Otherwise, if the worktree is `linked` and any of these hold, the answer is `Refused { may_claim: true }` (M3):
   - its path is under `main_root/.claude/worktrees/`;
   - a scope records this worktree;
   - a non-revoked scope's `branch` equals the worktree's current branch.
5. Otherwise `Unscoped`. This covers the main checkout and the person's own linked worktrees elsewhere.

**`issue` preconditions:**
- The item exists, and the caller is unscoped.
- For **build**, the item's status must be the status holding `Role::Build` in `ProjectConfig::roles()`. If not, it refuses with "move it first: `kanbanr move <CODE> "<status>"`".
- The commit hooks and the `pre-push` hook must be installed in `repo`. If not, it refuses with "run `kanbanr git install-hooks`". (The CLI checks this through `scm::hooks_installed` and `push_hook_installed` and passes the result as a fact.)
- The branch is the existing item branch (`scm::item_code_from_branch` over `branch_facts`), or `scm::branch_for(pattern, code, title)` created with `coderepo::create_branch_from(root, name, base)`. Base is `gitmodel::start_base(..)` when `cadence.git_model` is on, else `coderepo::default_branch`. It is never checked out.
- It refuses if `coderepo::worktree_of(root, branch)` is a checkout that is not an agent worktree.
- `hours` must be ≤ `MAX_HOURS`.

**`claim` preconditions:**
- The scope is `Issued` and not expired, and the worktree is `linked`.
- For build, the worktree is switched to `branch` (`git switch`) when it is clean. Otherwise it refuses.
- Order follows FEAT-183: preflight → git switch → board record → pointer file. If the board write fails, the switch is undone.

### Enforcement points (the functions that change)
1. **Board writes: `write::apply`.**
   - It becomes `let scope = agentscope::resolve(store, &cwd)` followed by `apply_as(..., &scope)`.
   - Inside `apply_as`, under the lock and before `require_identity`, when the request is a mutation and not a dry run:
     - `Refused` is returned as `WriteError::Refused(why)`, except a `scope.claim` route with `may_claim`.
     - `Scoped(s)` goes through `agentscope::check(&s, &requested(..))`. Then `git::is_clean(data_dir)` must pass, else M12.
     - For task and batch routes, `body["hold_advance"]` is set to M13.
   - Under `Scoped`, after dispatch:
     - the commit message becomes `with_trailer(msg, s)`;
     - activity goes through `activity::append_by(.., Some(&s.by_agent()))`;
     - events go through `eventing::record_by(.., Some(..))`;
     - `git::after_commit` runs with `PushPolicy::Off`, so the commit is marked unpushed and never pushed.
   - The CLI and server signatures are unchanged.
2. **Writes that do not go through `write::apply`.**
   - `main.rs` gets `fn command_access(cmd: &Command) -> Access { Read | Core | Hook | Outside(&'static str) }`. It is an exhaustive `match` with **no wildcard arms**, including the subcommand enums, so a new command will not compile until it is classified.
   - `fn scope_gate(cli)` runs at the top of `run()`. When `agent_context(cwd)` is Some, it refuses `Outside` commands with M11.
   - `Outside` covers: `Init`, `Identity`, `SelfUpdate`, `Skill` and `Editor` install, `Hooks` install/uninstall, `Process` save/update, `Serve` with `allow_writes`, `Sync`, `Remote` add/remove, `Migrate`, `Index`, `Events` test, `Claude` sync, `Mirror` writes, `Start`, `Finish`, and `Git` `InstallHooks`/`UninstallHooks`/`Forward`.
   - The `Backend` methods named in the components table repeat the check, as a second line.
3. **Pushing.**
   - `git::sync_all` (the only board push, used by `push_pending` and the daemon's `sync`) returns a failure without pushing when `agent_context(cwd)` is Some.
   - The new `GitCmd::CheckPush` runs as the `pre-push` hook and uses `push_verdict`.
   - `run_guard` denies `git push` in an agent context.
   - `coderepo::git` already refuses `push`.
4. **Commits.**
   - `run_guard` (the PreToolUse Bash hook) resolves the scope from the payload `cwd` **before** its `is_git_commit` early return. It denies `scoped_command_refusal(command, &wt, board)` (below). For commits it puts `agentscope::commit_verdict` in front of `scm::commit_verdict`.
   - `run_check_branch` (pre-commit) puts `commit_verdict` in front of `branch_verdict`.
   - `run_check_msg` (commit-msg) does the same in front of `message_verdict`, then **appends the trailer** to the message file when it is missing. A different scope id in the trailer is refused.
   - When the scope cannot be resolved because the board is unreachable but a pointer file exists, all three refuse (fail closed).
   - `run_commit` adds the trailer itself.
5. **Bash heuristics: `scoped_command_refusal`.** These live in the CLI, because shell text is the front end's concern (FEAT-176). In an agent context they deny:
   - `git push`, `kanbanr sync`;
   - `--data-dir` or `KANBANR_DATA_DIR=`/`KANBANR_PROJECT=` on a kanbanr call;
   - `cd`/`pushd`/`git -C`/`--git-dir`/`--work-tree` to a path outside the worktree and `temp_dir()`, when the command also runs git or kanbanr;
   - any mention of `kanbanr-scope`;
   - `git worktree remove|move`, `git config core.hooksPath`, `--no-verify` (already denied today);
   - write verbs (`>`, `>>`, `tee`, `sed -i`, `rm`, `mv`, `cp`) aimed at the board directory.
6. **Write|Edit guard: `run_docs_guard`.** In an agent context it denies paths inside the board dir and paths outside the worktree and `temp_dir()`. Under a design scope it denies every path outside `temp_dir()`.
7. **Capture: `run_capture`.** Under `Scoped`, the ops are filtered with `retain_permitted`, and the command stays quiet when none are left. Under `Refused` it does nothing.

### Refusal messages (exact text; `{…}` are filled in)
- **M1:** `refused by agent scope {id} ({role}, {item}): \`{label}\` is not one of its operations. Under this scope you may: {allowed}. Report what you needed to the coordinator; do not work around it.`
- **M2:** `refused by agent scope {id} ({role}, {item}): \`{label}\` is on {other}; this scope covers {item} only.`
- **M3:** `refused: this is an agent worktree ({path}) and no agent scope is bound to it. If you are the agent, run the claim command from your brief (\`kanbanr scope claim SC-…\`); otherwise ask the coordinator to issue one (\`kanbanr scope issue <design|build> <CODE>\`).`
- **M4:** `refused: the scope file here names {id}, which is bound to {other worktree | no worktree yet — claim it}.`
- **M5:** `refused: agent scope {id} expired at {time}. The coordinator renews it (\`kanbanr scope renew {id} --for 4h\`) or issues a new one.`
- **M6:** `refused: agent scope {id} was revoked by {by} at {time} ({reason}). Nothing more is recorded under it.`
- **M7:** `refused by agent scope {id} (build, {item}): this commit is on {branch}; this agent commits only on {scope.branch}.`
- **M8:** `refused by agent scope {id} (build, {item}): a commit under this scope must name {item} (\`Refs: kanbanr:{item}/R-n\`); use \`kanbanr commit -m "…"\`.` (`[no-ref]` is also refused.)
- **M9:** `refused by agent scope {id} (design, {item}): a design agent does not commit or edit code.`
- **M10:** `refused by agent scope {id}: agents never push. The coordinator reviews the branch and pushes it.`
- **M11:** `refused by agent scope {id|none}: \`kanbanr {command}\` {changes kanbanr itself | writes outside the board's write path}, which no agent scope allows.`
- **M12:** `refused by agent scope {id}: the board has changes not made through kanbanr ({paths}). An agent writes the board only through kanbanr; tell the coordinator.`
- **M13:** `all of {item}'s tasks are done, but it stays in {status}: under agent scope {id} the coordinator moves it.`

### CLI and routes
**CLI:**
```
kanbanr scope issue <design|build> <CODE> [--for 8h] [--note …] [--worktree PATH] [--json]
      → prints the id, then the brief (below)
kanbanr scope claim <SC-id>        # in the agent's worktree; switches to the branch for build
kanbanr scope here                 # which scope applies in this folder, and what it allows
kanbanr scope list [--all] [--item CODE] [--json]   # default: issued + active
kanbanr scope show <SC-id> | brief <SC-id>
kanbanr scope revoke <SC-id> [--reason "done"]
kanbanr scope renew <SC-id> --for 4h
kanbanr scope drift [--brief] [--json]
kanbanr git check-push             # the pre-push hook
```

**Core dispatch routes.** These are internal, like `/guards`: served but not in openapi v1.
- `GET /projects/:p/scopes`: views with the derived `state`.
- `GET /projects/:p/scopes/:id` and `GET /projects/:p/scopes/:id/brief` (`text/markdown`).
- `GET /projects/:p/scopes/drift`: needs `repo`.
- `POST /projects/:p/scopes` with `{role, item, hours?, note?, worktree?}`: needs `repo`.
- `POST /projects/:p/scopes/:id/claim`, where `repo` is the worktree root.
- `POST /projects/:p/scopes/:id/revoke` with `{reason}`.
- `POST /projects/:p/scopes/:id/renew` with `{hours}`.

`commit_message` gains: `issue agent scope {id} ({role}, {item})`, `claim agent scope {id}`, `revoke agent scope {id}: {reason}`, `renew agent scope {id}`. The daemon serves the GETs through `read_passthrough` with no wiring needed.

**Generated brief** (for build; for design, the record and code rows read "nothing" / "every write, every commit, every file edit"):
```
## Your boundaries — kanbanr agent scope SC-007 (build, FEAT-214), enforced by kanbanr
First, in your worktree: `kanbanr scope claim SC-007` (switches you to feat/FEAT-214-…)
| Area | Allowed | Refused |
|---|---|---|
| Read the board and the code | everything | — |
| FEAT-214's record | `kanbanr task state FEAT-214 <TL> <T> <state>` as each task starts and lands; `kanbanr test FEAT-214 R-n "<name>" green --rev <sha>` | moves, approvals, sign-offs, definitions, specs, docs, config, other items |
| Code | commits on feat/FEAT-214-…, each naming FEAT-214 (`kanbanr commit`) | commits on any other branch |
| Remote | nothing | `git push`, `kanbanr sync` |
| Tests | temporary boards only | a real board |
Expires 2026-10-21 18:00 UTC. A refusal names the boundary it crossed: report it to the coordinator, never work around it.
```

### Drift
`drift` looks at every non-revoked **build** scope (expired ones included, since their work may still be unrecorded):
- `since` = the later of `last_task_change(item)` and `issued_at`;
- commits = `coderepo::commits_since(root, "{base}..{branch}", since)`.

Where it appears:
- **`git doctor`:** `gitdrift::scan` adds a Warning per drifting scope: `"{item}: {n} commit(s) on {branch} since its tasks last changed at {since} (agent scope {id}): {sha7} {subject}; …"`. It also warns when an active scope's worktree no longer exists ("revoke it").
- **Stop hook:** `stop-check.sh` and `.ps1` run `kanbanr scope drift --brief` **before** rule 1, with their own per-session stamp. When there is output, they block with: "kanbanr: agent work is ahead of the board: <lines>. Look at the branch and bring the item's tasks up to date now (`kanbanr task state …`)."
- **Session start:** `session-start.sh` and `.ps1` print a `### Agents at work` section from `kanbanr scope list` and `kanbanr scope drift --brief`.

### Monitor
- **Item page (`FeaturePage.tsx`):** a new "Agents" section after the todo-lists.
  - A banner for any active scope: role, id, branch, issued by and when, time to expiry, and drift count.
  - Below it, the item's scope history, including expired and revoked scopes with the revoke reason.
  - Activity lines render `{actor}, by the agent for {item} ({scope}) · time`.
- **Workflow page (`WorkflowPage.tsx`):** under "Guard rails", an "Agent scopes" group fed by `Guards.agents`. It shows the two roles with their operations, every issued or active scope across items, and whether the pre-push hook is installed.
- **Board page (`BoardPage.tsx`):** the activity feed gets the same suffix.

`web/src/agentScopes.ts` holds the pure helpers `scopeRows`, `scopeBanner` and `byAgentText`, checked by `check-agent-scopes.mjs`. The monitor stays read-only (`check:read-only`).

### Skill changes (`skill/kanbanr/SKILL.md`, "Sub-agents: what each may do", from FEAT-215)
The subsection now says:
- before starting any sub-agent, run `kanbanr scope issue <role> <CODE>` (one command);
- start the agent with `isolation: worktree`, design agents included;
- paste the printed brief **verbatim** at the top of the agent's brief;
- revoke the scope (`--reason done`) when the agent's work has been reviewed;
- never issue scopes from inside an agent;
- when a refusal comes back, decide it or ask the user.

The static table stays as the description of the roles, and its wording is updated: "batch only of these ops". The existing build-role and design-role lines point to the subsection.

### Compatibility
- A board with no `scopes.yaml`, and the main checkout, behave as today (R-11).
- `Task.changed_at`, `Activity.by_agent` and `Event.by_agent` are optional fields. Older binaries keep `changed_at` through `extra` (FEAT-151). Readers ignore the other two.
- The `write::apply` signature is unchanged. `set_task_state_reported` and `apply_batch_with` gain a parameter (internal callers only).
- An existing hooks install lacks `pre-push`: `scope issue` refuses until `kanbanr git install-hooks` is re-run, which is idempotent. `hooks_installed` keeps its meaning.
- The FEAT-195 fence is unchanged.
- FEAT-192 marker resolution is reused as is.
- `openapi.json` is regenerated.

### Security: what local enforcement can and cannot do
**Prevented (structurally, for any process started in the agent's worktree):**
- every board write outside the scope, through any front end (CLI, daemon, capture, batch);
- commits outside the branch or item, through the git hooks in the shared common hooks dir, `kanbanr commit` and the Bash guard;
- board pushes (`sync_all`) and `git push` through the hook and the guard;
- commands that would change kanbanr's own enforcement (identity, hooks, `migrate`, `serve --allow-writes`);
- deleting or editing the pointer file, which fails closed (M3/M4);
- direct edits to the board files, which are blocked before the next kanbanr write (M12).

**Not prevented, because the agent runs as the user with the user's file permissions:**
- a process that leaves the worktree in ways the Bash heuristics cannot see, for example a script that `chdir`s to the main checkout and runs kanbanr there unscoped;
- `git commit --no-verify` or `git -c core.hooksPath=/dev/null` hidden inside a script;
- ref moves with `update-ref` or `branch -f`;
- edits to `.git/worktrees/*` or to the board's `scopes.yaml` by hand, the latter followed by a write from the main checkout.

**What makes those visible after the fact:**
- every scoped write carries `by_agent` plus a trailer, so an unattributed change during a scope stands out in history;
- `git doctor` reports commits on protected lines (FEAT-191) and scope drift;
- `scopes.yaml` is versioned in board git, so a hand edit shows in its history.

Scopes guard against mistakes and casual crossings, not a hostile local process. That stays true until Claude Code itself can sandbox a sub-agent.

### Requirements (EARS) and tests
| R | Requirement | Tests |
|---|---|---|
| R-1 | WHEN the coordinator runs `kanbanr scope issue <role> <CODE>`, THE SYSTEM SHALL record the scope on the board with its issuer, item, operations, branch, issue time and expiry, and print the boundary table and claim command for the brief. | `agentscope::tests::brief_names_item_branch_and_claim` (unit); `scope_issue_records_and_prints_the_brief` (integration) |
| R-2 | WHEN `kanbanr scope claim` runs in a linked worktree, THE SYSTEM SHALL bind the scope to that worktree on the board and in the worktree's git directory. | `scope_claim_binds_a_worktree` (integration) |
| R-3 | IF a board write under a scope is outside its operations or its item, THEN THE SYSTEM SHALL refuse it before anything changes and name the scope and the boundary crossed. | `agentscope::tests::build_scope_allows_only_own_item_task_and_test_states`, `design_scope_refuses_every_write`, `requested_maps_routes_and_batch_ops` (unit); `scoped_agent_records_task_and_test_but_cannot_move` (integration; board byte-identical after a refusal) |
| R-4 | IF a board write or commit comes from an agent worktree with no valid scope bound to it, THEN THE SYSTEM SHALL refuse it. | `agentscope::tests::resolve_fails_closed` (unit, all `resolve_with` cases); `agent_worktree_without_scope_is_refused` (integration, including a deleted and an altered pointer) |
| R-5 | IF a commit under a scope is on another branch, does not name the scope's item, or is made under a design, expired or revoked scope, THEN THE SYSTEM SHALL refuse it in the commit guard and the git hooks. | `agentscope::tests::commit_verdict_scoped` (unit); `scoped_commits_only_on_item_branch` (integration: hooks plus guard JSON) |
| R-6 | IF a process in an agent worktree pushes the board or the code, THEN THE SYSTEM SHALL refuse it. | `scoped_agent_cannot_push_or_sync` (integration: `kanbanr sync`, push policy `auto`, `git push` through pre-push, guard) |
| R-7 | THE SYSTEM SHALL record each write and commit made under a scope as the person, by the agent for its item, in the activity entry, the event, the board commit and the code commit. | `scoped_writes_are_attributed` (integration) |
| R-8 | WHEN a scope is revoked or its expiry passes, THE SYSTEM SHALL refuse every further write and commit under it. | `agentscope::tests::scope_state_derives_issued_active_expired_revoked` (unit); `revoked_and_expired_scopes_refuse` (integration) |
| R-9 | WHEN a build scope's branch has commits newer than its item's last task change, THE SYSTEM SHALL name them in the Stop hook, `git doctor` and session start. | `agentscope::tests::drift_counts_commits_after_last_task_change` (unit); `scope_drift_is_reported` (integration: `scope drift --brief`, `git doctor`) |
| R-10 | THE SYSTEM SHALL show each project's scopes and their state on the monitor's item page and Workflow page. | `npm run check:agent-scopes` (`scopeRows`, `byAgentText`); `dispatch::tests::scopes_route_lists_state` (unit) |
| R-11 | WHERE no scope applies, THE SYSTEM SHALL behave as before. | `main_session_unchanged_with_scopes_on_board` (integration); existing suites unchanged |
| R-12 | THE SYSTEM SHALL state in the skill that Claude issues a scope with one command before starting each sub-agent, starts it in its own worktree, and puts the generated brief into its brief. | `skill::tests::skill_issues_a_scope_before_each_sub_agent` (unit); `manual: an orchestrated build agent records its own tasks and is refused a move` |
| R-13 | IF a command run in an agent worktree would change kanbanr's own enforcement or write outside the board's write path, THEN THE SYSTEM SHALL refuse it. | `outside_core_commands_refused_in_agent_worktree` (integration); `architecture::tests::front_ends_are_thin` (`board-commit` rule) |
| R-14 | IF a task change under a scope would complete its item, THEN THE SYSTEM SHALL keep the item where it is and say the coordinator moves it. | `scoped_task_completion_holds_auto_advance` (integration); `store::tests::hold_skips_auto_advance` (unit) |

Integration tests go in `api/crates/kanbanr-cli/tests/local_mode.rs` and follow `marker_resolves_from_linked_worktree`. They use `git worktree add .claude/worktrees/agent-t1`, install the hooks without `--no-hooks`, and put their boards under `CARGO_TARGET_TMPDIR` with the fence unset (D7).

### Affects docs
- `skill/kanbanr/SKILL.md`
- `skill/kanbanr/hooks/README.md`
- `docs/src/using/with-claude.md` (sub-agents and scopes)
- `docs/src/using/the-method.md` (the sub-agents subsection)
- `docs/src/using/the-monitor.md` (Agents section, Workflow page)
- `docs/src/using/traceability.md` (the `Agent-Scope` trailer)
- `docs/src/reference/cli.md` (`scope`, `git check-push`)
- `docs/src/reference/data-layout.md` (`scopes.yaml`, the pointer file)
- `docs/src/reference/http-api.md` (internal scope routes)
- `docs/src/architecture/data-model.md` (`Scope`, `Task.changed_at`)
- `docs/src/architecture/overview.md` (the write path)
- `docs/src/reference/openapi.json` (regenerated)
- `CHANGELOG.md` and `docs/src/project/changelog.md`

### Open questions (recommended answers)
- **Q1. Must design agents run in a worktree too?** Recommended: **yes**. A scope can only bind to a worktree, and the main checkout must stay unscoped (R-11). The cost is one worktree per design agent. Otherwise a design agent's limits stay prose only.
- **Q2. Rely on Claude Code passing `agent_id` in PreToolUse hook input, to scope agents with no worktree?** Recommended: **no**. Nothing in this repository shows that field, so it cannot be verified from the code. Revisit if Claude Code documents it.
- **Q3. Lifetime.** Recommended: **8h by default, 72h maximum, renewable**. It covers a working day without leaving forgotten scopes live.
- **Q4. Batch (D5).** Recommended: **allow a batch only when every op is in scope**. The table's "batch refused" would otherwise break evidence capture for build agents.

### Decisions (21 Oct 2026, by the user)
- Q1: every scoped agent runs in its own worktree, design agents included.
- Q2: no reliance on an `agent_id` in hook input.
- Q3: scopes last 8h by default, 72h at most, and are renewable.
- Q4 / D5: a batch is allowed only when every op in it is within the scope (the test-capture hook
  records evidence through a batch); this replaces the table's "batch refused".

### Implementation tasks (ordered)
1. **Scope model and checks (core).**
   - Files: `agentscope.rs` (types, `load`/`load_all`/save, `Scope::state`/`allows`/`by_agent`, `Role::operations`, `requested`, `check`, `retain_permitted`, `trailer`/`with_trailer`, `brief`, `last_task_change`); `lib.rs`; `models.rs` (`Task.changed_at`); `store.rs` (stamp `changed_at` in `set_task_state_on`).
   - Unit tests: `scope_state_derives_issued_active_expired_revoked` (R-8), `requested_maps_routes_and_batch_ops` (R-3), `build_scope_allows_only_own_item_task_and_test_states` (R-3), `design_scope_refuses_every_write` (R-3), `brief_names_item_branch_and_claim` (R-1).
   - Depends on: none.
2. **Resolution.**
   - Files: `coderepo::worktree_facts`; `agentscope::{read_pointer, write_pointer, resolve_with, resolve, agent_context, outside_core_refusal}`.
   - Unit test: `resolve_fails_closed` (R-4) covers every rule.
   - Depends on: 1.
3. **Lifecycle and routes.**
   - Files: `agentscope::{issue, claim, revoke, renew, active}`; the dispatch routes and `commit_message` entries.
   - Behaviour: as in Formats and the preconditions. `issue` takes a hooks-installed fact in the body (`hooks_ready: bool`) from the CLI.
   - Unit test: `dispatch::tests::scopes_route_lists_state` (R-10).
   - Depends on: 2.
4. **The write path.**
   - Files: `write.rs` (`apply` → `apply_as`); `git::is_clean`; the hold parameter in `store.rs` and the dispatch task and batch routes; `activity::append_by`; `eventing::record_by`; `by_agent` fields; `sync_all` and `set_identity` refusals.
   - New architecture rule `board-commit`: in front-end crates, `commit_local(`, `push_pending(` and `set_identity(` may appear only in `backend.rs` functions that call `outside_core_refusal`, each marked `// architecture: allowed because gated by outside_core_refusal`.
   - Tests: `store::tests::hold_skips_auto_advance` (R-14), `write::tests::scoped_write_is_refused_before_dispatch` (R-3, through `apply_as`).
   - Depends on: 2.
5. **The CLI scope commands and the gate.**
   - Files: `ScopeCmd` (issue, claim, here, list, show, brief, revoke, renew, drift); `command_access` (exhaustive) and `scope_gate`; `Backend` second-line checks; `run_capture` filter; `run_serve` refusal.
   - Integration tests: `scope_issue_records_and_prints_the_brief` (R-1), `scope_claim_binds_a_worktree` (R-2), `scoped_agent_records_task_and_test_but_cannot_move` (R-3), `agent_worktree_without_scope_is_refused` (R-4), `scoped_writes_are_attributed` (R-7, board side), `revoked_and_expired_scopes_refuse` (R-8), `main_session_unchanged_with_scopes_on_board` (R-11), `outside_core_commands_refused_in_agent_worktree` (R-13), `scoped_task_completion_holds_auto_advance` (R-14).
   - Depends on: 3, 4.
6. **Commits and pushes.**
   - Files: `agentscope::{commit_verdict, push_verdict}`; `scm.rs` (`HOOKS` gains pre-push, `push_hook_installed`); `GitCmd::CheckPush`; scope checks in `run_guard` (before its early return, plus `scoped_command_refusal`), `run_check_branch`, `run_check_msg` (appends the trailer), `run_commit` (trailer), `run_docs_guard`.
   - Tests: `commit_verdict_scoped` (unit, R-5), `scoped_commits_only_on_item_branch` (R-5), `scoped_agent_cannot_push_or_sync` (R-6), and the code-commit half of `scoped_writes_are_attributed` (R-7).
   - Depends on: 5.
7. **Drift.**
   - Files: `coderepo::commits_since`; `agentscope::{drift, drift_issues}`; `gitdrift::scan`; `scope drift --brief`; `session-start.sh`/`.ps1`; `stop-check.sh`/`.ps1`.
   - Tests: `drift_counts_commits_after_last_task_change` (unit, R-9), `scope_drift_is_reported` (R-9).
   - Depends on: 3, 6.
8. **Monitor.**
   - Files: `guards.rs` (`agents`); `web/src/types.ts` (`Scope`, `ByAgent`, `Activity.by_agent`); `api.ts` (`getScopes`); `agentScopes.ts`; FeaturePage Agents section and activity suffix; BoardPage activity suffix; WorkflowPage Agent scopes group; `check-agent-scopes.mjs` and the npm script; regenerate `openapi.json` (the core contract test writes it).
   - Test: `check:agent-scopes` (R-10).
   - Depends on: 3, 4.
9. **Skill and docs.**
   - Files: the SKILL.md subsection; hooks README; the book pages listed under Affects docs; CHANGELOG; `tools/docs/sync.sh`.
   - Tests: `skill::tests::skill_issues_a_scope_before_each_sub_agent` (R-12), plus the manual run (R-12).
   - Then `make ci`.
   - Depends on: 5–8.
