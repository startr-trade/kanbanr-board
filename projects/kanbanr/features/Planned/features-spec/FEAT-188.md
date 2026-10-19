# Workflow stage roles

Gates and actions name statuses, so anything automatic is tied to one process's vocabulary. A design gate written for `System Design` means nothing to PDCA, and a merge on entering `Migration` means nothing to kanban.

Scope:
- A workflow maps statuses to **roles**: `design` (how and where are decided), `build` (code is written on the item's branch), `integrate` (the item is finished and joins the integration line), and `release` (the terminal, in use). A status may have no role, and each role belongs to at most one status.
- Every built-in preset declares its roles. For example, TOGAF: System Design → design, Implementation → build, Migration → integrate, Operations → release. Default kanban: Planned → design, In Progress → build, Completed → integrate and release.
- Gates and actions may name a role instead of a status, so presets and the skill can state rules once.
- `kanbanr process checks` and the working agreement show the roles.

## Design

### Summary
A gate gains `roles`, the stage roles its status holds: `design`, `build`, `integrate` and `release`.
A gate may also be keyed by a role instead of a status (`"@build"`). Core resolves it onto the
status that holds the role, so every place that reads `effective_gates()` (moves, `check`, `next_gates`,
doctor, the review queue) honours it with no change. The build role is where `start` makes the
branch; `on_enter: [branch]` is kept and still accepted. A workflow with no roles gets them
**synthesised** from what it already does: build where the branch is made, release at the first end
status. So no existing board changes behaviour. Every preset declares all four roles. `process
checks` lists the roles, and the working agreement names each stage's role. FEAT-189, FEAT-190 and
FEAT-193 address stages only through `ProjectConfig::role_status`.

### Components and files
- `api/crates/kanbanr-core/src/config.rs`:
  - adds `Role`, `StageRoles`, `ROLE_KEY_PREFIX` and `Gate.roles`;
  - adds `ProjectConfig::{roles, role_status, branch_status, declares_gates}`;
  - adds `role_problems`, called from `gate_problems`;
  - `effective_gates` merges role-keyed gates and the role labels;
  - `counts_as_done` reads the effective gates;
  - `required_schema_version` adds 4;
  - `working_agreement` prints roles.
- `api/crates/kanbanr-core/presets/*.yaml`: `roles:` on the gates of all seven presets. `default` and
  `scheduled` get gates that only label roles (see Behaviour), and their header comments are updated.
- `gates.is_empty()` used as "declares its own gates" is replaced by `!config.declares_gates()` in:
  - `api/crates/kanbanr-core/src/doctor.rs` (211);
  - `store.rs` (1770);
  - `claude.rs` (108; it also iterates `effective_gates()` rather than `gates` at 115);
  - `releases.rs` (203);
  - `kanbanr-cli/src/main.rs` run_finish (3867).
- `api/crates/kanbanr-cli/src/main.rs`:
  - `branch_status` delegates to `ProjectConfig::branch_status`, which FEAT-176 also moves into core;
  - `run_process_checks` prints the roles (text and `--json`).
- `api/crates/kanbanr-core/src/library.rs`: no code change. Roles travel inside `WorkflowFile.gates`,
  so saved processes carry them, and `diff` reports a `roles` change as a gate field change.
- `web/src/types.ts`: `Gate.roles?: string[]`. `web/src/pages/WorkflowPage.tsx`: a `role: build` chip
  beside "branch here".
- Docs: `docs/src/using/processes.md` (a new "Stage roles" section), `skill/kanbanr/SKILL.md`, and
  `CHANGELOG.md`.

### Data model / Interfaces
```rust
// config.rs
/// What a stage is for, in any process (FEAT-188). Each role belongs to at most one status.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Role { Design, Build, Integrate, Release }
impl Role {
    pub const ALL: [Role; 4];                       // in this order
    pub fn name(self) -> &'static str;              // "design" | "build" | "integrate" | "release"
    pub fn parse(s: &str) -> Option<Role>;          // trimmed, ASCII case-insensitive
    pub fn means(self) -> &'static str;             // one sentence, used by checks and agreement
}
/// A gate key that addresses a role rather than a status: `"@build"`.
pub const ROLE_KEY_PREFIX: &str = "@";
pub fn role_key(key: &str) -> Option<Role>;         // Some only for "@<valid role>"

// Gate: new field (kept as strings, so an unknown future role is a reported problem, not a
// parse failure of the whole config)
#[serde(default, skip_serializing_if = "Vec::is_empty")]
pub roles: Vec<String>,

/// The resolved role→status map, and whether it was declared or synthesised.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize)]
pub struct StageRoles { pub by_role: BTreeMap<Role, String>, pub declared: bool }
impl StageRoles { pub fn status(&self, r: Role) -> Option<&str>; pub fn of(&self, status: &str) -> Vec<Role>; }

impl Gate { pub fn is_role_label(&self) -> bool; } // only `roles` (and extra) set
impl ProjectConfig {
    pub fn roles(&self) -> StageRoles;
    pub fn role_status(&self, role: Role) -> Option<String>;
    pub fn branch_status(&self) -> Option<String>;  // == role_status(Build)
    pub fn declares_gates(&self) -> bool;           // some gate (status- or role-keyed) is not a role label
}
/// Role problems in a set of gates; `gate_problems` appends them.
pub fn role_problems(statuses: &[String], no_ops: &[String], terminals: &[String],
                     gates: &BTreeMap<String, Gate>) -> Vec<CoreError>;
```
On disk, the TOGAF preset becomes:
```yaml
Implementation: { purpose: …, requires: [tests_named, approved], on_enter: [branch], roles: [build] }
```
The default preset becomes:
```yaml
gates: { Planned: {roles: [design]}, In Progress: {roles: [build]}, Completed: {roles: [integrate, release]} }
```

### Behaviour
- **`roles()`**: when declared (any status-keyed gate has a non-empty `roles`):
  - each valid role name maps to its gate's status;
  - `declared = true`;
  - role-keyed gates never hold roles.

  When nothing declares roles, they are **synthesised**:
  - build is the first status, in `statuses` order, whose `effective_gates()` gate has
    `on_enter: Branch`. This is exactly today's `branch_status`;
  - release is the first status in `statuses` that `graph::is_terminal_status` calls terminal and that
    is not a no-op;
  - design and integrate stay unassigned (Q2);
  - `declared = false`.
- **`effective_gates()`**, in order:
  1. Base. If `declares_gates()` is true, use the status-keyed declared gates. Otherwise use today's
     synthesis, with one change: when roles are declared, `Branch` goes on the build-role status
     instead of the first active one. (In every preset these are the same status.)
  2. Copy role labels onto the base gates. A status that only holds a role gets a gate that holds
     the role and asks nothing.
  3. Ensure the declared build status's gate has `on_enter: [Branch]`.
  4. For each `"@role"` key, merge that gate into the gate of the status that holds the role
     (an empty gate is created if needed):
     - `requires`, `warns`, `signoffs` and `on_enter`: union, status entries first, no duplicates;
     - `purpose`: the status's own, unless it is empty;
     - `done`: either;
     - `enforce` and `kinds` must match; a mismatch is a check problem (Q3).

     A role nobody holds makes the key a check problem, so it never reaches here; at runtime it is
     skipped.
  5. Drop the `@` keys. The result is keyed only by status, as today.
- **`declares_gates()`**: true when any gate, status- or role-keyed, has a field other than `roles`
  set. Role labels alone keep the built-in rule, so a new `default` or `scheduled` board behaves
  exactly as today, in this binary and in older ones (see Compatibility).
- **`role_problems`** reports each of these as `CoreError::Unsupported`, in this order:
  - an unknown role in `roles` or in an `@` key: "'x' is not a stage role (design, build, integrate,
    release)";
  - a role held by two statuses (R-4): "the role 'build' is held by both 'Do' and 'Check'; give it to
    one", naming the statuses in `statuses` order;
  - a role on a no-op status;
  - `release` on a status that is not terminal;
  - an `@role` key whose role no status holds, when roles are declared: "the gate '@design' names a
    role no status holds";
  - `on_enter: [branch]` on a status other than the declared build status;
  - an `enforce` or `kinds` conflict from step 4.

  `gate_problems` skips its `UnknownStatus` check for valid `@role` keys. Because this runs inside
  `check_workflow`, every save path refuses the problem: `config workflow`, `--from-file`, `process
  save`, `process apply` and `process check`.
- **Start.** `start` targets `branch_status()` (unchanged in effect) and makes the branch there.
  Finish is unchanged: picking the integrate role is FEAT-190's (Q4).
- **`process checks`** prints a "Stage roles" block of `name — means`. JSON gains `roles: [{role,
  means}]`.
- **The working agreement** prints `_Role: build — code is written on the item's branch._` under a
  stage's heading for each role it holds (from `roles()`; synthesised roles are marked
  "(inferred)").

### Compatibility
- **Older binaries, gates with rules plus `roles`:**
  - `roles` is an unknown gate key, kept in `Gate.extra` and written back;
  - the gates are enforced as before;
  - presets keep `on_enter: [branch]`, so the branch is still made;
  - schema stays 3.
- **Gates that only label roles** (`default`, `scheduled`), **or any `@role` key:** an older binary
  that knows gates would treat the labels as declared gates and lose the synthesised rule. It would
  also never match `@build`. Either way a guardrail is silently lost. `required_schema_version`
  returns **4** for these, so an older binary refuses the board, as FEAT-113 set the precedent (Q1).
  Otherwise it is 3 with gates and 2 without.
- **Existing boards with no roles:** `roles()` synthesises build and release from today's branch
  and terminal rules, and `effective_gates()` is byte-for-byte the same. The existing test
  `effective_gates_reproduce_the_legacy_gate` must stay green, unchanged.
- **Boards applied from a built-in preset** will show drift once the preset gains `roles` (its
  `content_rev` changes). `process apply` takes the update, as for any preset change, and the
  CHANGELOG says so.

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `roles_assigned_once` (each role resolves to one status; a status may hold several, e.g. default's Completed holds integrate and release; `StageRoles::of`) | core config.rs tests |
| R-2 | `presets_declare_roles` (every preset: all four roles declared; build == the status with `on_enter: [branch]`; release is terminal; `problems()` is empty) | core config.rs tests |
| R-3 | `role_addressed_gates_apply` (an `@build` gate's `requires` and `signoffs` merge into TOGAF's Implementation and PDCA's Do; `readiness` refuses a move into Implementation that lacks them) | core config.rs tests |
| R-4 | `duplicate_role_refused` (`build` on Do and Check: `check_workflow` returns the problem naming both) | core config.rs tests |

Also:
- `legacy_roles_follow_the_branch`: no roles declared gives build = the branch status, release = the
  first end status, and the effective gates are unchanged (lib.rs).
- `role_labels_keep_the_builtin_rule`: the default preset still synthesises definition and approval
  on In Progress, and `declares_gates()` is false.
- `role_problems_reported`: unknown role, no-op holder, non-terminal release, orphan `@role`, a stray
  branch action, an enforce conflict.
- `schema_four_for_role_labels`.
- `working_agreement_names_roles`.
- CLI `process_checks_lists_roles` (local_mode.rs).

### Implementation tasks
1. **Model.** In config.rs:
   - add `Role` (with `ALL`, `name`, `parse`, `means`), `ROLE_KEY_PREFIX`, `role_key`, the
     `Gate.roles` field, `Gate::is_role_label`, `StageRoles` and its two methods;
   - update `WorkflowFile::into_config` and `from_config`, which need nothing new because the roles
     ride in `gates`.

   Tests: none of their own. Depends on: none.
2. **Resolution.** In config.rs:
   - `ProjectConfig::{roles, role_status, branch_status, declares_gates}`;
   - rewrite `effective_gates` as steps 1–5;
   - `counts_as_done` reads `effective_gates()`;
   - `required_schema_version` returns 4 per Compatibility.

   Tests: R-1 `roles_assigned_once`, R-3 `role_addressed_gates_apply`, `legacy_roles_follow_the_branch`,
   `role_labels_keep_the_builtin_rule`, `schema_four_for_role_labels`. Bump `CURRENT_SCHEMA_VERSION`
   to 4 and update its history comment. Depends on 1.
3. **Validation.** `role_problems`, wired into `gate_problems`, which receives no-ops and terminals:
   change its signature to `gate_problems(statuses, no_ops, terminals, gates)` and update the call in
   `check_workflow`. Tests: R-4 `duplicate_role_refused`, `role_problems_reported`. Depends on 2.
4. **Presets.** Add `roles:` per the table below, keep every `on_enter: [branch]`, and update the
   default and scheduled header comments ("roles are labelled; the built-in rule still applies").

   | Preset | design | build | integrate | release |
   |---|---|---|---|---|
   | default | Planned | In Progress | Completed | Completed |
   | scheduled | Planned | Scheduled | Completed | Completed |
   | togaf | System Design | Implementation | Migration | Operations |
   | pdca | Plan | Do | Check | Act |
   | design-control | Inputs | Design | Validation | Released |
   | scrum | Ready | In Progress | Done | Released |
   | agile | Design | Develop | Review | Released |

   Tests: R-2 `presets_declare_roles`, plus the existing preset and legacy tests stay green.
   Depends on 3.
5. **Gate-mode call sites.** Replace `gates.is_empty()` with `!declares_gates()` at the five sites
   listed. claude.rs iterates `effective_gates()`. Tests: the existing doctor, finish and claude
   tests stay green on the default preset. Depends on 2. **FEAT-176:** if its theme-3 task has
   landed, edit `flow::plan_finish` instead of run_finish.
6. **CLI.** `branch_status` → `config.branch_status()`. **FEAT-176:** if it has landed, its
   `ProjectConfig::branch_status` takes this body, and `flow::plan_start` needs no change. Whichever
   lands second keeps the role-based body. `run_process_checks` gets the roles block and JSON.
   Test: `process_checks_lists_roles`. Depends on 2.
7. **Agreement.** `working_agreement` prints the role lines. Test: `working_agreement_names_roles`.
   Depends on 2.
8. **Monitor.** `types.ts` gets `Gate.roles`, and WorkflowPage shows the role chip. Run `npm run build`
   and the existing web tests. Depends on 4.
9. **Docs.**
   - processes.md: a "Stage roles" section covering the table, `@role` keys, synthesis and the
     schema-4 note;
   - SKILL.md: state method rules at roles;
   - CHANGELOG.

   Depends on 4 and 6.

### Decisions (19 Oct 2026: every recommended answer accepted)
- **Q1.** Is schema 4, which makes older binaries refuse, right for role-label-only gates and `@role`
  keys?
  - Decided: yes. A silently lost guardrail is the failure FEAT-113's schema rule exists to
    prevent. Boards that only add `roles` beside real gates stay at 3.
- **Q2.** Should the synthesis also infer design (the status before build) and integrate (the
  release status) for boards with no roles?
  - Decided: no. Infer only build and release, which today's behaviour defines. `doctor` hints
    "declare stage roles", so FEAT-190 never starts merging on a board that didn't opt in.
- **Q3.** When an `@role` gate and its status's own gate disagree on `enforce` or `kinds`, should
  the save be refused or the gates merged?
  - Decided: refuse with a check problem. A merged result would silently change which items a
    rule binds.
- **Q4.** Should `finish` target the integrate role instead of the first reachable end status?
  - Decided: not in FEAT-188. FEAT-190 owns entering integrate and its merge.
- **Q5.** Should the order design → build → integrate → release be enforced in workflow order?
  - Decided: no. Roles may share a status, and loops make "order" ambiguous. Only the no-op and
    terminal rules apply.
- **Q6.** Design-control's `Design` status holds the build role, because the branch is made there.
  Is that acceptable naming?
  - Decided: yes. Moving the branch would change behaviour; the agreement line makes the role
    explicit.

### Affects docs
- [processes.md](/p/kanbanr/docs/file/docs/src/using/processes.md) (Gates; new Stage roles; Writing your own process)
- [cli.md](/p/kanbanr/docs/file/docs/src/reference/cli.md) (`process checks`)
- [architecture overview](/p/kanbanr/docs/file/docs/src/architecture/overview.md) (workflow config)
- Dependent items: [FEAT-189](/p/kanbanr/feature/FEAT-189), [FEAT-190](/p/kanbanr/feature/FEAT-190), [FEAT-193](/p/kanbanr/feature/FEAT-193); interacts with [FEAT-176](/p/kanbanr/feature/FEAT-176)
