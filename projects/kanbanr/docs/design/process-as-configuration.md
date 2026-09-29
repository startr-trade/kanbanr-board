# Process is configuration: declarable guardrails on workflow transitions

## Context

katalog uses the TOGAF preset, and walking an item through it on a scratch board showed that the
phases are only column names. The guardrails are hard-coded around a single "start then finish"
shape:

- **Approval is required on every move.** The start gate asks for approval on *any* move into a
  displayed, non-default, non-terminal status. Growing the definition in a phase lapses the
  approval, so each later move asks again. There is no way to say "Vision needs only a
  statement, System Design needs NFRs and a decision".
- **The branch is created too early.** `kanbanr start` creates the code branch at the first
  active status, which is Business Arch here, long before any code exists.
- **`finish` can't reach the end from Implementation.** It jumps to the first terminal status,
  so from Implementation it is refused (only Migration → Operations is an allowed transition).
- **Auto-advance and `finish` disagree.** Auto-advance targets a status literally named
  "Completed", while `finish` uses `terminal_states`. Auto-advance also skips every check.
- **"What is missing" is written five times.** `check_report` (CLI), `doctor`, `check --file`,
  `query::has_gap` and the monitor's client-side chips each have their own copy, and they have
  already drifted apart.

The user's real ask is not a TOGAF fix. It is that **a process (TOGAF, PDCA, an ISO-9001-style
design-control flow, an organisation's own QMS) should be declarable as data**, guardrails
included, while kanbanr stays generic.

**Principle (becomes ADR-0010):** *kanbanr owns the checks; the project owns the process.*
kanbanr provides a closed, versioned vocabulary of checks it can evaluate from board data, plus
named sign-offs for anything it can't. A workflow says which checks apply at which status. No
process semantics are hard-coded, and no user code runs.

Decisions taken with the user:
- **Named sign-offs** cover conditions kanbanr can't see (for example "design review held"). No
  script checks.
- **Enforcement is chosen per gate**: `block` (the default) or `warn`. A blocked move can go
  through with `--override "<reason>"`, and the reason is recorded.
- TOGAF is kept for katalog, with real phase support.

## Design

### 1. Gates in the workflow config (`config.rs`)

Add an optional `gates` map to `ProjectConfig`, keyed by status. Each entry is the **entry
criteria** for moving into that status, plus what happens on entry:

```yaml
gates:
  System Design:
    purpose: Decide how. Name quality needs and the decisions behind them.   # shown to Claude and in the monitor
    requires: [statement, goals, zachman: [what, who, why], requirements, ears, approved]
    warns:    [nfr_measured, adr]
    signoffs: [business-review]       # named sign-offs that must be recorded
    enforce: block                    # block | warn   (default: block)
    kinds: [feature]                  # optional: this gate applies only to these item kinds
  Implementation:
    requires: [zachman, tests_named, approved]
    on_enter: [branch]                # kanbanr start creates the code branch here
  Operations:
    requires: [tests_green, tasks_done, approved]
    signoffs: [release-approval]
```

- **One check vocabulary, evaluated in core (new `readiness.rs`)**, with parameters:
  - `definition`, `statement`, `goals`, `zachman` (optionally `[cols]`)
  - `requirements`, `ears`, `tests_named`, `tests_green`, `nfr_measured`
  - `approved` (current or ratified), `tasks_done`, `design_doc`
  - `adr` (an accepted ADR lists the item in `affects`), `defect_recorded` (defects only)
  - `signoff:<id>`

  Unknown check names and unknown statuses are rejected by `set_workflow`, as unknown statuses
  in transitions are today.
- **Sign-offs:** a new `signoffs: [{id, by, at, note, doc, rev}]` on the feature.
  - Recorded with `kanbanr signoff <CODE> <id> [--note …] [--doc path]`, or a button on the
    Review page. The commit identity is required, as for approve.
  - A sign-off pins the definition's `content_rev`, as an approval does, so a later change
    lapses it.
  - It is audit-grade: the event is appended and never overwritten.
- **Approvals remember their phase.** An `ApprovalEvent` gains a `status` field recording the
  phase it was given in. Progressive elaboration then leaves a readable trail: approved at
  Vision, re-approved at System Design after NFRs were added.
- **Override:** `--override "<reason>"` (`--unapproved` stays as an alias) lets a blocked move
  through. The reason goes into the move's `Transition` history entry, and into
  `started_unapproved` when the missing check was `approved`, so ratify keeps working.

### 2. Legacy synthesis: no board changes behaviour

`effective_gates(config)` returns the declared `gates`. When there are none, it synthesises
today's rules exactly:
- `approved` on every displayed, non-default, non-terminal, non-no-op status;
- the current `check_report` list on terminal statuses;
- `on_enter: [branch]` on the first active status.

All enforcement reads `effective_gates`, so existing boards, including this one, behave
identically. A **golden test** asserts that synthesised gates reproduce the old gate decisions
on the existing fixtures.

The charter adoption cutoff (`adopted_at`) still exempts pre-method items from gates.

**Terminal status without the name hack:** today a status literally named "Completed" counts as
terminal even when `terminal_states` is empty, which is how this board works (its
`terminal_states` is `[]`). The engine stops hard-coding the name. Legacy synthesis keeps the
fallback, so a board with an empty `terminal_states` and a "Completed" status behaves exactly as
before, and `doctor` suggests making it explicit. `portfolio.rs`'s separate `is_terminal` joins
the shared definition.

**Schema:** stamp `schema_version: 3` only when `gates` is non-empty. That way an older binary
refuses such a board (`SchemaTooNew`) instead of silently ignoring its guardrails, which
ADR-0004 forbids. Boards without gates stay at 2 and remain readable by older binaries.

### 3. One engine everywhere

`readiness::evaluate(project, charter, feature, checks) -> Vec<Gap{check, message, level}>` and
`readiness::gate_for(project, feature, to) -> GateOutcome` replace the five copies:
- **The store's move path** (`move_feature_on` / `move_feature_approved` / batch `feature.move`)
  evaluates the target's gate: a block refuses the move (overridable), a warn is returned with
  the success.
- **The CLI:**
  - `check` prints the gaps against the **next** status or statuses, as in "to move to System
    Design you still need: …". This is the progressive-elaboration guidance.
  - `finish` targets a terminal status **reachable by an allowed transition** from the current
    one, and evaluates its gate.
  - `start` targets the status whose gate has `on_enter: [branch]`, and creates the branch
    there.
  - `check --file` evaluates the terminal gate of the effective workflow.
- **Auto-advance** targets a terminal status allowed from the current one, never a literal
  "Completed", and only fires when that status's gate passes. Otherwise it stays put and the
  task write reports why.
- **doctor** becomes phase-aware: it warns about the gaps for the item's **next** gate, not
  every possible gap. The `warns:` lists feed it too.
- **Review queue:** it lists items blocked at their next gate for want of `approved` or a
  sign-off, with a button for each: Approve, Ratify or Sign off.
- **`query --gap`** uses the engine.
- **The monitor** reads a new `GET …/features/{code}/readiness` (per-next-status gaps) instead
  of computing chips client-side.
- **Git-dependent evidence** (commits referencing the item) stays a CLI-only `finish` check.
  The store has no code repo.

### 4. Presets become data

Presets move to embedded YAML files, `api/crates/kanbanr-core/presets/*.yaml` loaded with
`include_str!`, replacing `default_for` and `togaf_preset` in code:
- **`default`**: **this board's shape**, chosen by the user. Statuses: Deferred, Planned,
  In Progress, Completed, Ongoing, plus No Action, Not Applicable and Out-of-Scope. Default status
  Planned; terminal status Completed. Ongoing is a displayed, non-terminal home for recurring work
  that never completes. Gates are the legacy-equivalent set: `approved` to enter In Progress and
  the current readiness list to enter Completed; branch on In Progress.
  - This replaces the old built-in default (Deferred, Planned, Scheduled, Completed), which stays
    available as a preset named **`scheduled`**, so nothing that relied on it is lost.
  - It affects **new** projects only. A preset is copied into a project at setup, and from then
    on the project's own `config.yaml` is the source of truth. Existing boards, this one included,
    keep their workflow unchanged.
- **`togaf`**: progressive gates.

  | Phase | Gate requires | Warns about | Other |
  |---|---|---|---|
  | Vision | statement, goals (entry state, no gate) | — | — |
  | Business Arch | who, what, why, functional requirements (EARS), `approved` | — | — |
  | System Design | how, where, `approved` | NFRs measured, an ADR | — |
  | Implementation | `tests_named`, `approved` | — | `on_enter: branch` |
  | Migration | `tests_green`, `tasks_done` | — | — |
  | Operations | — | — | `signoff: release`, terminal |

  It also allows **Implementation → Operations** for items with no migration step.
- **`pdca`**: Plan → Do → Check → Act.
  - Do: `approved`, branch.
  - Check: `tests_green`.
  - Act: `signoff: review`; its gate warns on a missing lesson link.
- **`design-control`**: an ISO-9001-§8.3-style flow of Planning → Inputs → Design → Review →
  Verification → Validation → Released, with sign-offs at Review and Validation. It is described
  as "modelled on", **never "compliant with"**.

CLI:
- `kanbanr config workflow --preset <name>` (keeps `--togaf` and `--defaults` as aliases).
- `kanbanr config workflow --from-file process.yaml` for an organisation's own QMS.
- `kanbanr config workflow --export` prints the full YAML, gates included.
- `project init --workflow <preset>` accepts any preset name and errors on an unknown one. Today
  an unknown name silently falls back.

Mermaid export adds each gate as a `note` (read-only; import ignores notes, as now).

### 5. Surfacing, skill and docs

- **Monitor Workflow page:** each status shows its purpose, required checks, sign-offs and
  enforcement. On the board, each card gets a "next: System Design needs 2" chip from the
  readiness endpoint.
- **CLAUDE.md block** (`kanbanr claude sync`) includes each status's `purpose`, so Claude
  elaborates phase by phase instead of filling everything up front.
- **Skill:**
  - The setup interview offers the presets and `--from-file` for an organisation's own process.
  - The method section explains that the definition grows as the item moves, that `kanbanr
    check` names what the next phase needs, and that a sign-off is the user's, never Claude's.
- **Docs:** a new chapter, `docs/src/using/processes.md` (presets, gate vocabulary, sign-offs,
  writing your own QMS file, a worked PDCA example). The Zachman/TOGAF section of
  `the-method.md` is updated. ADR-0010 goes into the board's `decisions/`.

## Board items (one batch, milestone MS-007 "Process as configuration", after this is approved)

| Item | Scope | Depends on |
|---|---|---|
| A | `readiness.rs` single engine. Replace `check_report`, the doctor gap checks, `query::has_gap`, the `check --file` checks and the web chips (via the endpoint). Behaviour-preserving, plus a golden test. | — |
| B | `gates` config + validation + `effective_gates` legacy synthesis + store move enforcement + `--override` + schema 3 stamping. Status is read from the record, never inferred from the path; identity is recorded as given; item codes are treated as opaque keys | A |
| C | Sign-offs: model, `kanbanr signoff`, route, content-pinned lapse, approval `status` field | B |
| D | Transition targets: `start` via `on_enter: branch`, `finish` via a reachable terminal, auto-advance through gates, `first_active_status` no-op fix | B |
| E | Presets as data (default, togaf, pdca, design-control), `--preset` / `--from-file` / `--export`, mermaid gate notes, unknown-preset error | B, C |
| F | Surfacing: `check` next-gate output, phase-aware doctor, review queue sign-offs, monitor readiness endpoint + Workflow page + card chip, CLAUDE.md purposes | A, B, C |
| G | Skill, docs chapter, ADR-0010, changelog; apply the new togaf preset to katalog | E, F |
| H (defect, separate, first) | `kanbanr claude guard` denies writes to files **outside the project repo** (it refused `~/.claude/plans/*.md`, the harness's plan file) and suggests a malformed `notes//home/…` path. It must decide only for paths inside the tracked repo. | — |

Each item gets the house definition (statement, goals, Zachman, EARS requirements with named
tests), is approved before it starts, and goes on its own branch. Order: H, then A → B → (C, D) →
E → F → G.

## Part 2: cadence. Agile and Scrum with sprints and releases

The user asked for ready-made agile and Scrum setups that work on a timeline: sprints, and
releases that take finished items, following the common industry stages (plan, design, develop,
test, review, deploy/release, feedback, repeat). This builds on Part 1: stages are workflow
statuses with gates, and the new parts are **timeboxes** and **releases**.

Decided with the user:
- **Sprints are their own entity.** Milestones stay themes with dependencies.
- **Releases are planned up front.**
- **Estimates use story points**, with the unit chosen per project.

**Charter fit.** Sprints and releases here are timeboxing and shipping for one developer plus
Claude, which serves G-1 and G-5. Team ceremonies, per-person velocity and capacity by assignee
stay out; they belong to the opt-in team track (MS-005).

### Presets: common industry stages

Each preset below also carries the three no-op statuses. Transitions go one step forward or one
step back (rework is normal), or to a no-op. Feedback is not a status: it arrives as **new
backlog items linked to the release** they came from (`found_in: v1.2.0`, reusing the defect
record's field).

**`scrum`**: Backlog → Ready → In Progress → Review → Testing → Done → Released.

| Status | Gate | Notes |
|---|---|---|
| Backlog | — | default, no gate |
| Ready | **Definition of Ready**: statement, goals, requirements (EARS), `estimated` | — |
| In Progress | `approved`, `in_sprint` (assigned to the active sprint) | `on_enter: branch` |
| Review | `tests_named` | — |
| Testing | — | — |
| Done | **Definition of Done**: `tests_green`, `tasks_done` | — |
| Released | `in_release` | terminal, reached only by `release cut` |

The Scrum events map onto commands: sprint planning is `sprint plan`, the sprint review and
retrospective are `retro --sprint`, and the increment is `release cut`.

**`agile`**: the user's own stage list, for flow with or without sprints: Plan → Design →
Develop → Test → Review → Released.

| Status | Gate | Notes |
|---|---|---|
| Plan | — | default |
| Design | statement, goals, requirements, `approved` | — |
| Develop | how and where (Zachman), `tests_named` | `on_enter: branch` |
| Test | — | — |
| Review | `tests_green` | — |
| Released | `tasks_done`, `in_release` | terminal; warns on a missing sign-off |

**Not only code.** A project need not be software, so no stage name assumes code (hence
"Review", not "Code Review"), and the checks stay neutral. A "test" is any named verification,
and the `manual` kind already exists, so a document review or a sign-off counts. The
`on_enter: branch` action runs only where the project folder is a git repository; elsewhere
`start` moves the item without a branch and says so. A project can also drop the action from its
gates.

**Gate vocabulary additions** (in `readiness.rs`): `estimated` (points or days, per the project's
unit), `in_sprint`, `in_release`, `released`.

### Sprints (new `projects/<id>/sprints.yaml`, the charter side-file pattern)

A sprint is `{code: SP-001, name, goal, start, end, capacity, state: planned|active|closed,
closed_at, carried: [..]}`. An item gains `sprint: Option<String>`.

Commands:
- `kanbanr sprint add --start <date> --length 2w --goal "…" [--capacity 20]`: the length
  defaults from the project's cadence.
- `kanbanr sprint plan SP-003 FEAT-… …` assigns items and warns when committed points exceed
  capacity.
- `kanbanr sprint start SP-003` makes it the active sprint. Only one is active at a time.
- `kanbanr sprint close SP-003 [--carry-to SP-004|backlog]` moves unfinished items on, records
  the carry-over on the sprint and each item, and offers `retro --sprint SP-003`.
- `kanbanr sprint show SP-003` shows goal, dates, days left, committed vs done points, and a
  text burndown.

Burndown and velocity are **derived** from the move history the board already keeps (raw data
kept, reports derived). `retro` gains `--sprint`.

### Releases (new `projects/<id>/releases.yaml`)

A release is `{version, name, target, state: planned|shipped, shipped_at, tag, notes_doc,
carried: [..]}`. An item gains `release: Option<String>`. Releases are planned up front, as the
user chose.

Commands:
- `kanbanr release add v1.2.0 --target <date>` creates a planned release.
- `kanbanr release plan v1.2.0 FEAT-… …` assigns items to it.
- `kanbanr release cut v1.2.0 [--tag]` ships the planned items that are Done:
  - moves them to the terminal status through its gate;
  - writes release notes from their statements and requirements to the board doc
    `releases/v1.2.0.md`;
  - optionally tags the code repo;
  - carries unfinished planned items to the next planned release, or back to unplanned, and
    records the carry-over.
- `kanbanr feature add --found-in v1.2.0` records feedback against a shipped release.

### Estimates

An item gains `points: Option<f64>` beside `estimate_days`. The config gains `estimate_unit:
points|days` and `cadence: {sprint_length_days, release: per_sprint|every_n|on_demand}`. The
cadence is used only as defaults for setup and `sprint add`.

### Kick-starting a project (the setup interview, FEAT-100 skill)

The process step of the interview offers these presets: default, scrum, agile, togaf, pdca,
design-control, or the team's own file. When a preset uses sprints, it also asks:
- sprint length (1, 2, 3 or 4 weeks; 2 is the default);
- the first sprint's start (default: next Monday);
- capacity in points;
- release cadence (every sprint, every N sprints, or on demand);
- the first release's version (default v0.1.0).

The setup plan then also runs `config workflow --preset scrum`, `sprint add` for Sprint 1,
`release add v0.1.0`, and writes a **working agreement** doc, `process/working-agreement.md`. That
doc renders the Definition of Ready and Definition of Done straight from the gates, so it can
never disagree with what is enforced.

### Timeline and monitor

- **Gantt/Schedule:** sprints show as sections, releases as `milestone` markers.
- **Board:** a sprint selector (the active sprint by default when the preset uses sprints), and
  a header with goal, dates, days left, committed vs done points, and a small burndown.
- **New Releases page:** each release's planned scope, % done, target date and a notes link.

### Part 2 items (milestone MS-008 "Cadence: sprints and releases", after Part 1's B and E)

| Item | Scope | Depends on |
|---|---|---|
| I | Sprints: side file, item field, CLI, routes, `in_sprint` gate, derived burndown/velocity, `retro --sprint` | B |
| J | Releases: side file, item field, plan/cut, notes doc, optional tag, carry-over, `in_release` gate, `--found-in` feedback | B |
| K | Points + `estimate_unit` + cadence config; capacity warnings; `estimated` check | B |
| L | Presets `scrum` and `agile`; the setup-interview kick-start (skill) and the working-agreement doc rendered from gates | E, I, J, K |
| M | Monitor: sprint selector and header, Releases page, Gantt/Schedule sprints and releases | I, J |

### Part 2 verification

- **Scrum end to end in a scratch repo, run as a probe:**
  - Set up with the scrum preset: Sprint 1 and v0.1.0 exist, and the working agreement lists
    the DoR/DoD from the gates.
  - An item without an estimate is refused Ready; one outside the active sprint is refused In
    Progress.
  - Plan, work and finish two items; close the sprint with one carried over; check burndown and
    velocity against the history.
  - Cut v0.1.0: only the Done items move to Released, notes are written, and the unfinished item
    is carried to v0.2.0.
  - `feature add --found-in v0.1.0` links the feedback.
- **Agile:** the preset's gates run end to end the same way, without sprints.
- **Monitor:** headless screenshots of the sprint header and burndown, the Releases page, and a
  Gantt with sprints and releases.

## Delivery order

Each item is merged, tested and usable on its own:

1. **H**: the docs-guard defect that blocked this plan file.
2. **Part 1, A → B → (C, D) → E → F → G**: one readiness engine, declarable gates, sign-offs,
   transition targets, presets as data, surfacing, then skill, docs and ADR-0010. katalog moves
   to the progressive TOGAF preset after E.
3. **Part 2, I, J, K → L → M**: sprints, releases, points, the Scrum/agile kick-start, cadence
   views.

Every item is recorded on the board before it starts, with the house definition, approved by the
user, and on its own branch. Approving this plan approves recording them, not skipping their
individual approvals.

## First step after approval: record it on the board (one batch, previewed with `--dry-run`)

- **Milestones:**
  - MS-007 "Process as configuration" (depends on MS-006).
  - MS-008 "Cadence: sprints and releases" (depends on MS-007).
- **Items:** H in MS-006 as a defect, A–G in MS-007, and I–M in MS-008, with `depends_on` taken
  from the tables above. Each gets the house spec (`## Problem` / `## Behavior` / `## Out of
  scope`) and a full definition: statement, goals, Zachman, and EARS requirements with named
  tests.
- **This plan** is saved as the board doc `design/process-as-configuration.md`. ADR-0010 is
  drafted as `proposed` and accepted when G lands.
- **Approvals:** nothing starts until the user approves it, on the Review page or with
  `kanbanr approve`. The first asks are **H** and **A**.

## Critical files

- `api/crates/kanbanr-core/src/config.rs`: `ProjectConfig` (+`gates`); presets move out
- `api/crates/kanbanr-core/src/readiness.rs` (new); `graph.rs` (`is_terminal_status`,
  `is_live_work`)
- `api/crates/kanbanr-core/src/store.rs`: `check_start_gate` → gate evaluation in
  `move_feature_on`, `set_workflow` validation, auto-advance (`set_task_state_on`), sign-off
  writes
- `api/crates/kanbanr-core/src/models.rs`: `Signoff`, `ApprovalEvent.status`,
  `Transition.override`
- `api/crates/kanbanr-core/src/doctor.rs`, `dispatch.rs` (routes, `build_project_config`,
  `apply_workflow`, the review queue), `query.rs`, `mermaid.rs`
- `api/crates/kanbanr-cli/src/main.rs`: `run_start`, `run_finish`, `check_report` (removed),
  `check_definition_file`, `ConfigCmd::Workflow`, the new `Signoff` command, and the claude
  guard (item H)
- `web/src/pages/{WorkflowPage,ReviewPage,BoardPage,FeaturePage}.tsx`, `web/src/types.ts`,
  `web/src/api.ts`
- `skill/kanbanr/SKILL.md`, `docs/src/using/processes.md` (new), `docs/src/using/the-method.md`,
  `CHANGELOG.md`

## Verification

- **Golden:** with no `gates`, every existing core and CLI test passes unchanged, and a table test
  asserts `effective_gates` gives the same allow/refuse decisions as the current
  `check_start_gate` over all status pairs of both presets.
- **One engine:** for a fixture set of items, `check`, `doctor` (next-gate), `query --gap`,
  `check --file` and the readiness endpoint report the same gaps. This is the regression test
  for the drift found today.
- **Gates:**
  - A block refuses the move and lists the gaps; `--override` passes and records the reason in
    history; a warn moves and reports.
  - Unknown check or status names are rejected on `set_workflow`.
  - `kinds:` limits a gate to those kinds.
  - Schema 3 is stamped only with gates, and an older schema-2 reader refuses a schema-3 board.
- **Sign-offs:** recording one needs an identity; it lapses when the definition changes; the gate
  passes only while it is current; the monitor button records it as the commit identity.
- **Transitions:**
  - TOGAF: `start` branches at Implementation, not Business Arch.
  - `finish` from Implementation reaches Operations through the allowed edge.
  - Auto-advance doesn't fire past an unmet gate.
  - PDCA end to end in a scratch repo.
- **End to end on a scratch board, walked by the scratch-probe method used today:**
  - Apply the togaf preset, add an item in Vision.
  - `check` names the Business Arch needs; fill them, approve, move.
  - Repeat through each phase, re-approving where the definition grew.
  - Record the release sign-off from the Review page (headless Chromium click), then `finish`.
  - The approval trail shows the phase of each approval.
- **Monitor:** a headless screenshot of the Workflow page with gates, plus the card chip.
- **Gates on every item:** fmt, clippy `-D warnings`, the full test suite, `npm run build` and
  `check:ui`/`check:docs`, and the legacy-load invariant (`kanbanr board` + `feature show` on this
  board with zero YAML diff).

## Out of scope


- Team ceremonies, per-person velocity and assignee capacity (the MS-005 team track).

- Script or command checks (the user chose sign-offs).
- Multi-approver quorum or roles (enterprise RBAC is a charter non-goal).
- Workflow editing in the monitor (the monitor stays a viewer, except for the verdict buttons).
- Any claim of ISO compliance.
