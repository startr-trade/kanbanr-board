# Method on by default in every preset

Every built-in process asks for the same discipline at the same roles, with an opt-out per project:
- **Before build:** the spec has a `Design` section (`spec_sections`), and the person gives a `design-review` sign-off.
- **Before integrate:** the docs the item declares are updated (`docs_updated`), and the person gives a `docs-folded` sign-off.
- **Everywhere:** references in specs, docs and ADRs are live links, checked by doctor.

`kanbanr config method --off` (or per gate) turns these off.

## Design

### Summary
One module in core, `method.rs`, states the method once as gate fragments addressed by **role**
([FEAT-188](/p/kanbanr/feature/FEAT-188)):
- at the **build** role: `spec_sections: [Design]` in `requires` and `design-review` in `signoffs`;
- at the **integrate** role: `docs_updated` in `requires` ([FEAT-180](/p/kanbanr/feature/FEAT-180))
  and `docs-folded` in `signoffs`;
- everywhere: doctor's broken-reference scan ([FEAT-181](/p/kanbanr/feature/FEAT-181)).

`config::preset(name)` returns the preset's YAML **with the method merged in** at the statuses that
hold those roles; `config::preset_bare(name)` returns the YAML as written. A project records its
choice in `config.method`; `kanbanr config method --off [part…]` removes the fragments from the
project's workflow and records which parts are off, and `--on` adds them back. Applying or updating
a built-in process honours the recorded choice, and drift ([FEAT-170](/p/kanbanr/feature/FEAT-170))
compares against the process *as shaped by that choice*, so opting out is never reported as an edit.

> **Amended by Q7 (19 Oct 2026).** The method is written as two role-addressed gates, `"@build"`
> and `"@integrate"` ([FEAT-188](/p/kanbanr/feature/FEAT-188)), not merged into each preset's
> status gates. `add`/`remove`/`present` act on those two keys. A role-addressed gate now *adds* to
> the built-in rule rather than replacing it: `ProjectConfig::declares_gates()` ignores `@role`
> keys. So default and scheduled keep their synthesized start rule, branch point and FEAT-156
> finishing rule with no legacy carry-over, and `synthesized_gates` / `uses_builtin_rule` are not
> needed (`unproven` already keys on `declares_gates`). The gates each stage enforces are the ones
> in the table below. A config carrying `@role` gates is schema 4.

### Components and files
- `api/crates/kanbanr-core/src/method.rs` (new): `Part`, `MethodChoice`, `add`, `remove`, `shaped`,
  `present`.
- `api/crates/kanbanr-core/src/config.rs`: `preset` / `preset_bare`; `ProjectConfig.method`;
  `synthesized_gates` (extracted from `effective_gates`); `uses_builtin_rule`; `default_for` uses
  `preset_bare("scheduled")`.
- `api/crates/kanbanr-core/src/store.rs`: `set_method`; `unproven` guard; shaping on apply/update.
- `api/crates/kanbanr-core/src/library.rs`: `drift` shapes `current` by the project's choice.
- `api/crates/kanbanr-core/src/dispatch.rs`: `GET|PUT /projects/:p/config/method`; preset apply and
  `build_project_config` shape the file before `into_config` and `source()`.
- `api/crates/kanbanr-core/src/doctor.rs`: the `links` part gates `scan_references`; Q3's nudge.
- `api/crates/kanbanr-cli/src/main.rs`: `ConfigCmd::Method`; `process update` shapes the file.
- Docs: `docs/src/using/processes.md`, `docs/src/reference/cli.md`, `CHANGELOG.md`; one paragraph in
  `skill/kanbanr/SKILL.md` (the full method text is [FEAT-194](/p/kanbanr/feature/FEAT-194)).

### Interfaces
```rust
// method.rs
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum Part { Design, DesignReview, Docs, DocsFolded, Links }
impl Part {
    pub const ALL: [Part; 5];
    pub const GATES: [Part; 4];                  // all but Links
    pub fn parse(s: &str) -> crate::Result<Part>; // unknown → error listing the five names
    pub fn as_str(self) -> &'static str;          // "design", "design-review", "docs", "docs-folded", "links"
    pub fn role(self) -> Option<Role>;            // Design|DesignReview → Build; Docs|DocsFolded → Integrate; Links → None
}
/// What a project chose (on disk under `method:`; absent = never chosen, everything on).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct MethodChoice {
    #[serde(default, skip_serializing_if = "Vec::is_empty")] pub off: Vec<Part>,  // sorted, unique
    #[serde(default, skip_serializing_if = "String::is_empty")] pub chosen_at: String, // RFC 3339
}
impl MethodChoice { pub fn is_on(&self, p: Part) -> bool; pub fn is_default(&self) -> bool; }
/// Merge the parts' fragments into the gate of the status holding each part's role. Idempotent:
/// a condition or sign-off already there is not added twice. Returns one note per part that could
/// not be placed ("no status holds the build role: design not added").
pub fn add(wf: &mut WorkflowFile, parts: &[Part]) -> Vec<String>;
/// Take the parts' fragments out: `Design` out of any `spec_sections` list at the build status
/// (dropping the condition when its list empties), the named sign-off out of `signoffs`,
/// `docs_updated` out of `requires`. A gate left equal to `Gate::default()` is dropped.
pub fn remove(wf: &mut WorkflowFile, parts: &[Part]);
/// `wf` with every part the choice has off removed.
pub fn shaped(wf: WorkflowFile, choice: &MethodChoice) -> WorkflowFile;
/// The status where `p` is in force in `wf`, or None.
pub fn present(wf: &WorkflowFile, p: Part) -> Option<String>;

// config.rs
pub fn preset_bare(name: &str) -> crate::Result<WorkflowFile>;   // today's `preset`
pub fn preset(name: &str) -> crate::Result<WorkflowFile>;        // bare + method::add(GATES)
impl ProjectConfig {
    #[serde(default, skip_serializing_if = "MethodChoice::is_default")] pub method: MethodChoice;
    pub fn synthesized_gates(&self) -> BTreeMap<String, Gate>;  // today's legacy synthesis
    /// The finishing rule of FEAT-156 applies: no gates beyond the built-in rule and the method.
    pub fn uses_builtin_rule(&self) -> bool;
}
// store.rs
pub fn set_method(&self, id: &str, on: bool, parts: &[Part]) -> Result<(ProjectConfig, Vec<String>)>;
```
Roles are read through FEAT-188's accessor (assumed `WorkflowFile::status_with_role(Role) ->
Option<&str>`); this design does not define the role syntax.

### Behaviour: gate changes per built-in preset
Roles as FEAT-188 assigns them (assumed here; Q5). Fragments are appended after the gate's
existing `requires`/`signoffs`; no `warns`, `on_enter`, `enforce` or `kinds` change.

| Preset | Build status: added | Integrate status: added | Notes |
|---|---|---|---|
| default | In Progress: `spec_sections: [Design]`; signoff `design-review` | Completed: `docs_updated`; signoff `docs-folded` | gates declared for the first time: In Progress also gets the legacy `definition, approved` and `on_enter: [branch]`, so today's rule is kept verbatim |
| scheduled | Scheduled: same as default | Completed: same | same legacy carry-over as default |
| togaf | Implementation: + `spec_sections: [Design]`; + `design-review` | Migration: + `docs_updated`; + `docs-folded` | Operations keeps `release` |
| pdca | Do: + both | Check: + both | Act keeps `review` |
| design-control | Design: + both | Validation: + both | the existing Verification `design-review` is renamed (Q2) |
| scrum | In Progress: + both | Done: + both | Released keeps `in_release` |
| agile | Develop: + both | Review: + both | |

- **Legacy rule kept.** For default and scheduled, `remove(GATES)` on the merged preset leaves gates
  equal to `synthesized_gates()`; `set_method` then clears `gates` entirely, so an all-off default
  project is byte-identical to today's (schema 2). `unproven()` (FEAT-156) changes its guard from
  `gates.is_empty()` to `uses_builtin_rule()` = `shaped(from_config, all off).gates` is empty or
  equals `synthesized_gates()`; every other workflow is unaffected.
- **A preset lacking a role** gets nothing for that role (the note is a test failure for built-ins,
  never for a user's process).
- **`kanbanr config method`** (no flag): one line per part: on/off, and where it is in force ("design
  on: Implementation requires spec_sections [Design]"), or "on, but not in this workflow — `--on`
  adds it". `--json` gives `{part, on, status}`.
- **`--off [part…]`** (default: all five): `remove`, add the parts to `method.off`, set `chosen_at`,
  run the store's validator, save. **`--on [part…]`**: `add` (notes printed), drop them from `off`.
  Commit message: "method <parts> off|on for <project>". Route: `PUT /projects/:p/config/method
  {on: bool, parts: [..]}`; `GET` returns the show data.
- **Records stay current.** If the project's workflow matched its `process.rev` before the change,
  `set_method` re-stamps `process.rev` to the new workflow's rev; an already-edited workflow stays
  edited. `library::drift` compares `shaped(current, &config.method)`.
- **Applying a process.** `config workflow --preset`, `project init --workflow` and `process update`
  shape the file by the project's choice before `into_config` and before `source()`, so a project
  that opted out stays out. Saved board or personal processes are never *added to*; they are only
  shaped.
- **links**: `doctor` runs `scan_references` only when `method.is_on(Links)`.
- **Sign-off queue.** With FEAT-182's R-4, `design-review` is offered only once the Design section
  exists, and `docs-folded` once `docs_updated` passes.

### Failure handling
`set_method` validates before writing; an unknown part, or a workflow the validator refuses, changes
nothing. `--on` for a part whose role is unassigned succeeds with the note and records nothing for
that part.

### Compatibility
- Existing projects keep their copied workflow; nothing changes until they choose.
- A project that recorded a built-in source sees FEAT-170's notice ("it has changed since — see
  `kanbanr process diff`"); `process update` brings the gates in, shaped by its choice.
- `method` is an optional key; older binaries keep it in `extra`.
- New default/scheduled projects now declare gates, so they are stamped schema 3, and a gate naming
  `docs_updated` is refused by binaries before FEAT-180. The release notes say: upgrade every machine
  sharing the board.
- The gates stay dormant for projects with no charter and for items older than its adoption.

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `config::tests::presets_include_method_gates` (every name in `presets()`: the build-role gate holds `spec_sections: [Design]` and `design-review`, the integrate-role gate holds `docs_updated` and `docs-folded`, and `problems()` is empty) | core config.rs |
| R-2 | `method_gates_opt_out` (togaf project: `config method --off` removes all four fragments, `method.off` lists five parts; an item without Design enters Implementation; `process status` is current; `--on design` restores only `spec_sections`) | cli tests/local_mode.rs |
Also: `method::tests::add_is_idempotent`, `method::tests::remove_all_restores_legacy_default`
(default preset, all off == bare, schema 2), `method::tests::missing_role_adds_nothing_and_says_so`,
`library::tests::drift_honours_method_choice`, and in core lib.rs
`builtin_rule_kept_with_method` (default project: finishing the last task with red tests is held).

### Implementation tasks
1. **method.rs.** `Part`, `MethodChoice`, `add`, `remove`, `shaped`, `present` as specified; `pub mod
   method`. Tests: the three `method::tests`. Depends on FEAT-188 (role accessor) and FEAT-180
   (`Check::DocsUpdated`).
2. **config.rs.** Rename today's `preset` to `preset_bare`; new `preset`; `ProjectConfig.method`
   (and in `into_config`, dispatch's literal config, every constructor); extract `synthesized_gates`;
   `uses_builtin_rule`; `default_for` → `preset_bare`. Test: R-1. Depends on 1.
3. **Fixtures.** Run the core and CLI suites; where a test exercises non-method behaviour through a
   preset, switch it to `preset_bare` (or `togaf_preset` → a bare variant). Never weaken an
   assertion; list each switched test in the commit. Depends on 2.
4. **Store and drift.** `unproven` guard; `set_method` with re-stamp and legacy clearing; shaping in
   dispatch's preset apply and `build_project_config`; `library::drift` shaping. Tests:
   `builtin_rule_kept_with_method`, `drift_honours_method_choice`. Depends on 2.
5. **Doctor.** `links` gates `scan_references`; Q3 nudge if agreed. Depends on 4, FEAT-181 task 2.
6. **Route and CLI.** `GET|PUT …/config/method`, its commit message; `ConfigCmd::Method { on, off,
   parts }` (clap: `--on` conflicts with `--off`); `process update` shapes. Test: R-2. Depends on 4.
7. **Docs.** processes.md: the Choosing table's Gates column, the built-in rule paragraph, a new
   section "The method, on by default" (what, where, opting out), the design-stage example; cli.md;
   SKILL.md design-stage paragraph ("built-in processes ask for this by default; `kanbanr config
   method`"); CHANGELOG with the docs sync. Depends on 6.

### Decisions (19 Oct 2026: every recommended answer accepted)
- **Q1.** Merge the method into presets in code, or write it into each YAML file? Decided:
  **in code** (`preset` = bare + `method::add`): one statement of the rule, the same code serves
  `--on`, and `preset_bare` keeps tests on today's semantics.
- **Q2.** design-control already has `design-review` at Verification (ISO 8.3.4, review of the
  outputs), which one recorded sign-off would now satisfy before Design. Decided: rename that
  one to `verification-review`, so `design-review` means the pre-build review in every preset.
- **Q3.** Projects created without `--workflow` record no process source, so FEAT-170 never tells
  them. Decided: `for_new_project` records `default` (built-in) from now on, and doctor warns
  once per project with no `method.chosen_at` whose workflow lacks the fragments ("predates the
  method: `kanbanr config method --on`, or `--off` to keep it off"), silenced by either choice.
- **Q4.** Require `docs-folded` even when the item declares no `affects_docs`? Decided: yes,
  uniform and one question; a project that finds it noisy turns off `docs-folded` alone.
- **Q5.** Confirm the roles assumed above, especially design-control build = Design, pdca integrate
  = Check, agile integrate = Review. Decided: as tabled; FEAT-188 owns the final assignment and
  this table follows it.
- **Q6.** Apply the method gates to every kind (defects, chores)? Decided: yes, no `kinds:`; a
  defect's Design can be a paragraph.

- **Q7.** Build the method as `@build`/`@integrate` gates, with role-addressed gates made additive
  to the built-in rule (a FEAT-188 fix: until now an `@role` gate on a label-only process silently
  dropped the start rule), or as designed above? Decided: **`@role` gates plus the fix**.

### Affects docs
- docs/src/using/processes.md, docs/src/reference/cli.md, skill/kanbanr/SKILL.md, CHANGELOG.md
- [design/process-as-configuration.md](/p/kanbanr/docs/file/design/process-as-configuration.md)
  (presets become data; legacy synthesis)
- [design/process-library.md](/p/kanbanr/docs/file/design/process-library.md) (drift shaped by choice)
- [ADR-0010](/p/kanbanr/docs/file/decisions/0010-process-is-configuration-kanbanr-owns-th.md)
  (process is configuration: a default the user can switch off)
