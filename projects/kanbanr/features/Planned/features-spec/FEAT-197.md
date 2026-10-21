## Problem
Living architecture docs drift even when every item's design is folded in. The fold-in check (`docs_updated`) only covers the docs an item names in `affects_docs`. The cross-cutting views are rarely named, so nothing notices when they fall behind:
- a Zachman or coverage matrix;
- an ADR index;
- the component catalog in an application view.

**An observed case.** A board ran a sprint in which more than twenty items moved past the vision stage and five ADRs were accepted. Every item's own component docs were updated. Even so:
- the Zachman matrix lacked 24 of those items;
- 8 ADRs were referenced from no architecture view;
- the component catalog lacked 7 shipped items and 6 designed components.

No gate fired, and `doctor` reported only broken links.

## What this adds
1. **Project-configured coverage rules** in the project config, generic over any process. Examples:
   - "every item at stage S or later is referenced from doc D";
   - "every accepted ADR is referenced from some doc under folder F";
   - "every doc under folder C is referenced from doc K" (a catalog lists every component doc);
   - "every item in stage S lists doc D in `affects_docs`".

   References use the existing reference finder: live links and board-shaped tokens.
2. **Lifecycle triggers.** The rules are evaluated:
   - when an item is added, moved or its definition edited;
   - when an ADR is accepted;
   - when a doc is written;
   - at sprint close and release cut.

   A move reports the uncovered rule as a warning, or refuses it when the rule is a gate condition (`docs_cover`) on that stage's gate. The other events report it as a warning in the command's output and in the board-update hook. `doctor` lists every uncovered rule.
3. **Default `affects_docs` per stage.** A process can name docs that every item entering a stage must list, so the views are always part of the fold-in and `docs_updated` covers them.
4. **Skill guidance.** The skill tells Claude:
   - to add the project's view docs to `affects_docs` when it writes a design;
   - to add every new ADR to the architecture index when the ADR is accepted;
   - to fix coverage warnings before moving an item;
   - to run `doctor` before a sprint merge or a release cut.
5. **`process checks`** lists `docs_cover` with its narrowing (rule ids).

## Out of scope
Checking that the content of a doc is semantically accurate.

## Design

### Summary
A new core module, `coverage`, evaluates **coverage rules** that a project configures under `coverage:` in its config. Each rule says that every subject of one kind is covered:
- the subject kinds are items in a stage range, accepted ADRs, or docs under a folder;
- a subject is covered when one source doc, or any doc under a source folder, references it, or (for items) when it lists a named doc in `affects_docs`.

References come from `refs::find`, the FEAT-181 finder, so the same live links and board-shaped tokens count.

The rules are checked in three places:
- **On writes.** After the trigger writes, the dispatcher adds a `coverage_warnings` field to the response. The CLI prints it and eventing records a `coverage_gap` event (events log and webhook).
- **On moves.** A gate can ask for the new check `docs_cover`, optionally narrowed to rule ids (`{docs_cover: [zachman]}`). It is judged as if the item were already in the target stage.
- **In `doctor`.** It reports one issue per uncovered rule.

A gate can also carry `affects_docs:`, the docs every item entering that stage must list. The move adds them to the item's definition, and `docs_updated` (FEAT-180) then checks them.

With no rules configured, nothing changes: no docs are read, no fields are added and no gaps appear.

### Crates, modules and files
All logic goes in `kanbanr-core`. The CLI changes only argument parsing and printing, to stay out of the way of FEAT-176.

| File | Change |
|---|---|
| `api/crates/kanbanr-core/src/coverage.rs` (new) | rules, validation, snapshot, evaluation, triggers, response annotation |
| `api/crates/kanbanr-core/src/lib.rs` | `pub mod coverage;`; store tests |
| `api/crates/kanbanr-core/src/config.rs` | `ProjectConfig.coverage`, `Gate.affects_docs`, `merge_gate`, `is_role_label`, `gate_problems`, stage helpers, working agreement line |
| `api/crates/kanbanr-core/src/readiness.rs` | `Check::DocsCover`, `Condition::DocsCover`, `Context.coverage`, `evaluate_entering` |
| `api/crates/kanbanr-core/src/store.rs` | `check_gate` and `next_gates` judge at the target stage; default docs added on entry; `set_coverage`; `rename_status` updates rules |
| `api/crates/kanbanr-core/src/dispatch.rs` | wrapper adding `coverage_warnings`; routes `GET/PUT /projects/{p}/coverage` |
| `api/crates/kanbanr-core/src/doctor.rs` | `scan_coverage` |
| `api/crates/kanbanr-core/src/eventing.rs` | `EventKind::CoverageGap` |
| `api/crates/kanbanr-cli/src/main.rs` | `config coverage` subcommand; `print_coverage_warnings`; `process checks` unchanged in code (it reads `Check::GATEABLE` and `parameters()`) |
| `web/src/types.ts` | `Condition` gains `{ docs_cover: string[] }`; `conditionText`; `Gate.affects_docs?` (display only) |
| `docs/src/reference/openapi.json` | regenerated (`Gate` and `Condition` schemas change) |

### Config format (`projects/<id>/config.yaml`)
```yaml
coverage:
  - id: zachman                      # required, ^[a-z0-9][a-z0-9-]*$, unique in the project
    description: the Zachman matrix lists every designed item   # optional
    every: item                      # item | adr | doc
    from: "@design"                  # item only: this stage or later; a status name or "@<role>"
    # in: [Implementation, Review]   # item only: exactly these stages (excludes `from`)
    # kinds: [feature]               # item only: only these kinds (no kind = feature)
    referenced_from: architecture/zachman.md   # a doc, or a folder ending "/" = any doc under it
  - id: adr-index
    every: adr                       # accepted ADRs (status "accepted"; superseded ones excluded)
    referenced_from: architecture/
  - id: catalog
    every: doc
    under: architecture/components/  # doc only, required
    referenced_from: architecture/catalog.md
  - id: views-listed
    every: item
    in: [Implementation]
    lists: architecture/zachman.md   # item only; instead of referenced_from
    except: [FEAT-001]               # optional: subjects grandfathered out
```

The default docs per stage live on the gate, inside the process (`WorkflowFile.gates`):
```yaml
gates:
  "@design":   { affects_docs: [architecture/zachman.md] }
  Completed:   { requires: [tests_green, {docs_cover: [zachman, catalog]}] }
```

**Stage order: what "S or later" means.**
- `from: S` takes in every status whose position in `ProjectConfig.statuses` is at or after S's, except no-op statuses (`is_no_op`). This is the position order that `next_gates` already uses.
- `"@role"` resolves through `ProjectConfig::role_status(Role)` (FEAT-188), so one rule works in every process.
- `in:` lists exact statuses, and no-op statuses are allowed there.
- With neither `from` nor `in`, every non-no-op status counts.

**Subjects.**
- Items with a definition marked `exempt` are never subjects. Neither is anything listed in `except`.
- For `every: doc`, the source doc itself is excluded. For `every: adr`, the ADR's own file is excluded as a source.

**Format notes.**
- Paths are normalised with `refs::doc_key`. A folder keeps its trailing `/`.
- Unknown keys go to `extra` (FEAT-151), so no schema bump is needed. An older binary keeps the rules and ignores them.
- An older binary refuses a `docs_cover` condition at parse time. That is the right failure: a gate must not silently disappear.

### Public signatures (`coverage.rs`)
```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)] #[serde(rename_all="snake_case")]
pub enum Every { Item, Adr, Doc }

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Default)]
pub struct CoverageRule {
    pub id: String,
    #[serde(default, skip_serializing_if="String::is_empty")] pub description: String,
    pub every: Every,
    #[serde(default, skip_serializing_if="Option::is_none")] pub from: Option<String>,
    #[serde(default, rename="in", skip_serializing_if="Vec::is_empty")] pub in_stages: Vec<String>,
    #[serde(default, skip_serializing_if="Vec::is_empty")] pub kinds: Vec<String>,
    #[serde(default, skip_serializing_if="Option::is_none")] pub under: Option<String>,
    #[serde(default, skip_serializing_if="Option::is_none")] pub referenced_from: Option<String>,
    #[serde(default, skip_serializing_if="Option::is_none")] pub lists: Option<String>,
    #[serde(default, skip_serializing_if="Vec::is_empty")] pub except: Vec<String>,
    #[serde(flatten, default, skip_serializing_if="crate::models::Extra::is_empty")] pub extra: crate::models::Extra,
}
```
`Default` for `Every` is `Item`. The struct takes the `schema` cfg_attr, as the other config types do.

- **`pub fn parse_rules(text: &str) -> Result<Vec<CoverageRule>>`**
  - Reads YAML: either a bare list or a mapping with a `coverage:` key.
  - YAML is parsed in core, because the `yaml` architecture rule forbids `serde_yaml` in the CLI.
- **`pub fn rule_problems(rules: &[CoverageRule], config: &ProjectConfig) -> Vec<String>`** reports:
  - an empty or malformed id, or a duplicate id;
  - `from` together with `in`;
  - `from`, `in`, `kinds` or `lists` on a non-item rule;
  - `under` missing on a doc rule, or present on another kind;
  - not exactly one of `referenced_from` and `lists`;
  - a status that does not exist, or a role that resolves to no status;
  - a path that is absolute or contains `..`.

  Messages name the rule id.
- **`impl ProjectConfig`** (in `config.rs`):
  - `pub fn stage_set(&self, from: Option<&str>, in_stages: &[String]) -> Option<BTreeSet<String>>` returns `None` when it cannot resolve.
  - `pub fn default_affects_docs(&self, status: &str) -> Vec<String>` collects the raw `gates[status].affects_docs`, plus `gates["@r"].affects_docs` for each role in `self.roles().of(status)`. Paths are normalised with `doc_key` and deduplicated.
- **`pub struct Snapshot`**:
  - `rules: Vec<CoverageRule>` and `stages: BTreeMap<String, BTreeSet<String>>` (rule id to stage set);
  - `sources: BTreeMap<String, BTreeSet<Key>>` (source doc path to the subjects it references);
  - `docs: BTreeSet<String>`, `adrs: Vec<(String /*id*/, String /*path*/, bool /*accepted*/)>`;
  - `problems: BTreeMap<String, String>` (rule id to the problem that stopped it);
  - `pub docs_read: usize`.

  `Key` is `enum Key { Item(String), Adr(String), Doc(String) }` and derives `Ord`.
- **`pub fn Snapshot::load(store: &Store, project: &Project) -> Result<Snapshot>`**:
  1. Calls `refs::BoardIndex::of(store, project)` once.
  2. Collects the source docs: each `referenced_from` doc, or every doc in `index.docs` under a `referenced_from` folder. Each distinct source is read once with `store.read_doc`.
  3. Runs `refs::find(text, &index)` on each source and maps every `Found`:
     - `Item{code,..}` becomes `Key::Item(code)`; a requirement reference also covers its item.
     - `Adr{id}` becomes `Key::Adr(id)`.
     - `Doc{path}` becomes `Key::Doc(path)`. If `path` is not in `index.docs`, the evaluator tries `normalize(parent(source)/path)`, so relative links resolve. If the path is an ADR's path in `index.adrs`, a `Key::Adr(id)` is also inserted.
  4. A missing source doc goes into `problems`. A failed read also goes into `problems`; nothing panics.

  This is the only I/O. Snapshot does not change `refs::find`, so the TypeScript port stays at parity.
- **`impl Snapshot`**:
  - `pub fn covered(&self, rule: &CoverageRule, subject: &Key, item: Option<&FeatureItem>, entering: Option<&str>, config: &ProjectConfig) -> bool`
    - For a `referenced_from` rule: true when any source of the rule, other than the subject's own file, holds the key.
    - For a `lists` rule: true when `doc_key(lists)` is in `def.affects_docs`, or in `config.default_affects_docs(s)` for `s = entering` (the docs a move is about to add).
  - `pub fn item_findings(&self, config: &ProjectConfig, f: &FeatureItem, at_status: &str, only: Option<&[String]>) -> Vec<Finding>` checks the item rules for which `f` at `at_status` is a subject. This is O(rules) set lookups.
  - `pub fn report(&self, project: &Project) -> CoverageReport` gives every rule and every uncovered subject. It is O(subjects × log n).
- **Output types** (`Serialize`):
  - `pub struct Finding { pub rule: String, pub subject: Subject, pub level: Level /*readiness::Level*/, pub message: String }`
  - `pub struct Subject { pub kind: Every, pub id: String }`
  - `pub struct RuleReport { pub id, pub description, pub every: Every, pub source: String, pub subjects: usize, pub uncovered: Vec<Subject>, #[serde(skip_serializing_if = "Option::is_none")] pub problem: Option<String> }`
  - `pub struct CoverageReport { pub rules: Vec<RuleReport> }`
- **Messages** (fixed wording):
  - referenced: `"[{rule}] {id} is not referenced from {source} — add a link to it there"`
  - listed: `"[{rule}] {id} does not list {doc} in affects_docs"`
  - problem: `"[{rule}] {source} is not on the board"`, at level `Error`
- **`pub enum Trigger`**: `Item(String)`, `Items(Vec<String>)`, `Adr(String)`, `Doc(String)`, `All`.
- **`pub fn trigger_of(method: &str, segs: &[&str], body: &Value, out: &Value) -> Option<(String /*project*/, Trigger)>`** is a pure route map:

  | Route | Trigger |
  |---|---|
  | `POST features` | `Item(out.code)` |
  | `PATCH features/{c}` | `Item(out.code)` (follows a rename) |
  | `PUT features/{c}/definition` | `Item(c)` |
  | `POST features/{c}/move` | `Item(c)` |
  | `POST adrs/{id}/accept` | `Adr(id)` |
  | `PUT` or `DELETE docs/content` | `Doc(path)` (the response's or the query's) |
  | `POST sprints/{c}/close`, `releases/{v}/cut`, `releases/{v}/promote` | `All` |
  | `POST batch` that is not a dry run | `Items`, from every `results[*].code` string |
  | anything else | `None` |

- **`pub fn warnings_for(store, project: &Project, t: &Trigger) -> Vec<Finding>`**:
  - `Item`: `item_findings(f, &f.status, None)`.
  - `Adr`: the ADR rules' findings where the subject is the ADR.
  - `Doc(p)`: the findings of rules whose sources include `p`, plus doc rules where `p` is the subject.
  - `All`: every finding from `report`.

  The list is capped at 100, and the number dropped is returned beside it.
- **`pub fn annotate(store: &Store, method: &str, path: &str, body: &Value, out: String) -> String`**:
  - Does nothing, cheaply, when the route has no trigger or the project has no rules (one `load_meta`, only for trigger routes).
  - Otherwise it parses `out` as a JSON object and inserts `"coverage_warnings": [Finding…]`. When the cap dropped findings, it also inserts `"coverage_more": n`.
  - On a move, it drops any finding whose message already appears in `gate_warnings`.
  - **It never returns an error.** Any failure returns `out` unchanged, because the write is already done.

### Readiness and gates (`readiness.rs`)
- **`Check::DocsCover`.** Add it to `GATEABLE` (the array grows to 19), with:
  - `passes_when`: `"the item is covered by every project coverage rule it falls under; \`{docs_cover: [id]}\` asks for only those rules"`
  - `parameters`: `Some("docs_cover: [rule-id, …] (the project's coverage rules, \`kanbanr config coverage\`)")`

  Add it to the no-op arms in `item_level` and to the `reads_definition` exclusion list in `evaluate_definition`.
- **`Condition::DocsCover { docs_cover: Vec<String> }`.** Add it to `Raw` in the hand-written `Deserialize`.
- **`Context` gains `pub coverage: Option<std::sync::Arc<crate::coverage::Snapshot>>`.**
  - `Context::load` builds it only when `!config.coverage.is_empty()` and some effective gate's `requires` or `warns` names `docs_cover`. It then calls `Snapshot::load(store, &store.load_meta(id)?)`.
  - If that fails, it stores a `Snapshot` whose `problems` holds the error under the key `"*"`.
- **`pub fn evaluate_entering(feature, goal_ids, conditions, ctx, entering: &str) -> Vec<Gap>`.** This is today's `evaluate_conditions` body, plus the docs_cover handling:
  - Plain `docs_cover` means all rules; a narrowed one means the union of the named ids.
  - Exempt items are skipped.
  - With `ctx.coverage` `None` and no narrowing, there are no gaps.
  - A narrowed id that the project does not configure is an Error gap: `"docs_cover names rule '{id}', which this project does not configure"`.
  - Otherwise each `item_findings(.., entering, only)` finding becomes `Gap { check: DocsCover, level, label: "[{rule}] not covered", message }`.

  `evaluate_conditions` becomes `evaluate_entering(.., &feature.status)`. `next_gates` (readiness.rs:523, 545) and `Store::check_gate` (store.rs:1513, 1516) call `evaluate_entering(.., to)`.

### Lifecycle hooks
| Event | Where | Effect |
|---|---|---|
| Move: gate | `Store::check_gate` → `evaluate_entering(.., to)` | under `requires` with `enforce: block`, the move is refused (`--override` records a bypass); under `warns`, or with `enforce: warn`, it goes to `gate_warnings` |
| Move: default docs | `Store::gated_move_on`, after `move_feature_on`: new `fn add_default_docs(project, code, to) -> Option<Gap>` | `config.default_affects_docs(to)` is unioned into `def.affects_docs`; `content_rev` excludes them, so approval does not lapse; an item with no definition gets a Warning gap `"{code} has no definition: the stage's default docs ({list}) are not recorded"`, returned in the warnings |
| Move, add, edit, define, ADR accept, doc write or delete, sprint close, release cut or promote, batch | `dispatch::dispatch_in`: the current body moves into `fn dispatch_routes(..)`; `dispatch_in` returns `coverage::annotate(store, &m, path, b, dispatch_routes(..)?)` | `coverage_warnings` is added to the response |
| Hook | `eventing::compute_events` | if the result has a non-empty `coverage_warnings`, it pushes `Event::new(project, EventKind::CoverageGap, item_of(path), "{n} coverage gap(s)", json!({"findings": …}))`; the write recipe (`write::apply`) logs and delivers it with the other events |
| doctor | `doctor::run` and `doctor::run_project` → new `fn scan_coverage(store, project, report)` | one issue per uncovered rule (below) |

"Board-update hook" here means the events written after every board write (FEAT-036: events log plus opt-in webhook). There is no other hook by that name; see Open questions.

### Output shapes
- **CLI text** (stderr, as `print_gate_warnings` does). `fn print_coverage_warnings(cli, resp)` is called from `print_write` and from every trigger command that does not use `print_write`. It prints up to 10 lines of `  coverage: [zachman] FEAT-012 is not referenced from architecture/zachman.md — add a link to it there`, then `  … and N more — kanbanr doctor`. With `--json` it prints nothing extra; the field is already in the JSON.
- **`--json`**: the write's own JSON plus `"coverage_warnings": [{"rule","subject":{"kind","id"},"level","message"}]` and, optionally, `"coverage_more": n`.
- **A refused move**: the existing `CoreError::Unsupported("cannot move FEAT-012 to 'Completed': [zachman] FEAT-012 is not referenced from … . To proceed anyway, …")`.
- **doctor**: `Issue { severity: Warning, project, code: None, message: "coverage rule 'zachman' (every item at Design or later is referenced from architecture/zachman.md): 24 of 60 uncovered — FEAT-012, FEAT-013, … (first 10)" }`. A rule with a problem, a rule that fails `rule_problems`, or a gate naming an unknown rule id is `Severity::Error`. An unknown doc in a gate's `affects_docs` is also an Error, as in `scan_references`.
- **`kanbanr config coverage`**:
  - With no flag it calls `GET /projects/{p}/coverage` and prints each rule with its uncovered count. `--json` prints the `CoverageReport`.
  - `--from-file F` reads F and calls `PUT /projects/{p}/coverage` with `{"text": "<file contents>"}`.
  - `--clear` sends `{"rules": []}`.
  - These routes are internal, not in the OpenAPI public set.
- **`process checks`** lists `docs_cover` with `narrowed by docs_cover: [rule-id, …] …`, with no code change.

### Failure handling
- **Invalid rules are refused** at `Store::set_coverage(id, rules) -> Result<ProjectConfig>`, which reports the first of `rule_problems`.
- **A hand-edited invalid file never blocks a write.** `doctor` reports it, and evaluation skips the invalid rule. A gate that names it gets an Error gap, which blocks; that matches the existing unknown-doc behaviour of `docs_updated`.
- **`rename_status`** renames `from` and `in` entries in `config.coverage`.
- **After a write, coverage failures are swallowed** (R-13).

### Defaults and performance
- **No rules means nothing happens.** `Context::load` builds no snapshot. `annotate` returns early after `load_meta`. `doctor` skips `scan_coverage`. A gate with plain `docs_cover` passes.
- **Budget:**
  - Snapshot build is linear in the bytes of the source docs: each read once, one `refs::find` pass each.
  - The per-item gate check is O(rules) set lookups.
  - `report` is O(subjects × rules × log n).
  - Target: with 2,000 items, 300 docs and 3 MB of source markdown, a snapshot in under 50 ms (release build) and a move overhead under 60 ms.
  - Only source docs are read, never every doc. Asserted through `docs_read`.
- **Known limit: batches.** A batch's gate uses the snapshot taken at the start of the batch, and batch doc ops are deferred. The doc fix must therefore be written before the move, in an earlier call. The docs say so.

### Dependencies and security
- No new dependencies: `serde_yaml` is already in core, plus `refs`, `adr` and `store`.
- **Paths:** rule and gate paths are normalised with `doc_key`, and absolute or `..` paths are refused. Reads go through `Store::read_doc`, which is confined to the project's `docs/`.
- No network. The webhook payload carries only finding messages, and only when the user has opted in.
- YAML comes from the user's own file and is parsed by core.

### Requirements (EARS)
- **R-1** (ubiquitous): THE SYSTEM SHALL let a project configure coverage rules (id, subject kind, stage range, kinds, folder, source doc or folder, or listed doc, exceptions), and SHALL refuse a rule set that is invalid, naming the rule and the problem.
- **R-2** (ubiquitous): THE SYSTEM SHALL count a subject as referenced only when a source doc names it as `refs::find` finds references: live links, including relative ones, and board-shaped tokens; a requirement reference covers its item.
- **R-3** (ubiquitous): THE SYSTEM SHALL take "stage S or later" as every status at or after S in the workflow's status order, no-op statuses excluded, with S given as a status or as `@role`.
- **R-4** (state-driven): WHILE a project configures no coverage rules, THE SYSTEM SHALL read no docs for coverage, and SHALL add no fields, gaps or doctor issues.
- **R-5** (event-driven): WHEN an item is added, moved, edited or its definition set, THE SYSTEM SHALL report the coverage rules that item fails as warnings in the command's output.
- **R-6** (event-driven): WHEN an ADR is accepted or a doc is written or deleted, THE SYSTEM SHALL report the rules that ADR or doc fails, or that the doc's subjects fail, as warnings.
- **R-7** (event-driven): WHEN a sprint closes or a release is cut or promoted, THE SYSTEM SHALL report every uncovered rule as a warning.
- **R-8** (optional): WHERE a stage's gate requires `docs_cover`, optionally narrowed to rule ids, THE SYSTEM SHALL refuse a move into that stage, unless overridden, while the item fails one of those rules as judged at the target stage.
- **R-9** (event-driven): WHEN a write reports coverage warnings, THE SYSTEM SHALL record a `coverage_gap` event in the events log and deliver it to configured webhooks.
- **R-10** (ubiquitous): THE SYSTEM SHALL list every uncovered rule in `doctor`, and report invalid rules and unknown rule ids in gates as errors.
- **R-11** (optional): WHERE a stage, or the role it holds, names default `affects_docs`, THE SYSTEM SHALL add them to the item's `affects_docs` when it enters the stage, without lapsing approval.
- **R-12** (ubiquitous): THE SYSTEM SHALL list `docs_cover` and its narrowing in `process checks` and in the guide's check table.
- **R-13** (unwanted): IF coverage cannot be evaluated after a write, THEN THE SYSTEM SHALL keep the write and its normal output.
- **R-14** (unwanted): IF a gate narrows `docs_cover` to a rule the project does not configure, THEN THE SYSTEM SHALL report an error gap naming it.
- **R-15** (quality, performance efficiency, time behaviour): WHEN a move is judged, THE SYSTEM SHALL read only the rules' source docs, once each. Scenario: 2,000 items, 200 source docs; the snapshot is built in under 2 s in a debug test, and `docs_read` equals the number of distinct source docs.
- **R-16** (ubiquitous): THE SYSTEM SHALL state in the skill when to list view docs, index new ADRs, fix coverage warnings before a move, and run `doctor` before a sprint merge or release cut.
- **R-17** (event-driven): WHEN a status is renamed, THE SYSTEM SHALL rename it in coverage rules.

### Test plan
| Req | Test |
|---|---|
| R-1 | `coverage::tests::rules_parse_and_validate`, `tests::set_coverage_refuses_invalid_rules` (lib.rs) |
| R-2 | `coverage::tests::references_count_links_tokens_and_relative_links` |
| R-3 | `coverage::tests::stage_order_skips_no_ops_and_resolves_roles` |
| R-4 | `coverage::tests::no_rules_no_effect`, `local_mode::coverage_silent_without_rules` |
| R-5 | `local_mode::coverage_warns_on_item_events` |
| R-6 | `local_mode::coverage_warns_on_adr_accept_and_doc_write` |
| R-7 | `tests::coverage_reports_all_at_sprint_close_and_cut` (lib.rs, via `dispatch`) |
| R-8 | `readiness::tests::docs_cover_gate`, `tests::docs_cover_blocks_move_until_covered` (lib.rs) |
| R-9 | `eventing::tests::coverage_gap_event` |
| R-10 | `doctor::tests::doctor_lists_uncovered_rules` |
| R-11 | `tests::default_affects_docs_on_entry` (lib.rs), `config::tests::default_affects_docs_by_role` |
| R-12 | `readiness::tests::every_check_is_listed_with_a_description`, `readiness::tests::the_guides_check_table_matches_process_checks`, `readiness::tests::docs_cover_reads_and_narrows` |
| R-13 | `coverage::tests::annotate_never_fails_a_write` |
| R-14 | `readiness::tests::docs_cover_unknown_rule_is_error` |
| R-15 | `coverage::tests::snapshot_reads_only_source_docs_linearly` |
| R-16 | `manual: skill coverage guidance present and matches docs/src/using/living-docs.md` |
| R-17 | `tests::rename_status_updates_coverage_rules` (lib.rs) |

### Affects docs
- **`docs/src/using/living-docs.md`**: a new section, "Coverage rules: keeping the views whole". It covers the YAML, stage order and roles, triggers, `docs_cover`, default `affects_docs`, and the batch limitation.
- **`docs/src/using/processes.md`**: in "The checks", a table row for `docs_cover` with the exact `passes_when` text (CI compares it). In "When a gate isn't met", a note on `docs_cover`. The gate field `affects_docs`.
- **`docs/src/using/housekeeping.md`**: doctor lists uncovered coverage rules.
- **`docs/src/reference/cli.md`**: `kanbanr config coverage`.
- **`docs/src/reference/openapi.json`**: regenerated.
- **`docs/src/project/changelog.md`**: an entry.
- **`skill/kanbanr/SKILL.md`**:
  - the gate-question table (around line 336): a `docs_cover` row, "never a question — fix the coverage";
  - "### The design stage: the spec carries the build-ready design" (around line 349): add the project's view docs to `affects_docs`;
  - "### Moving work" (around line 507): fix coverage warnings before moving;
  - "## Where documentation goes" (around line 704): add every accepted ADR to the architecture index;
  - "## Keep the tool updated" (around line 733): run `kanbanr doctor` before a sprint merge or release cut;
  - the Command reference: `config coverage`.

### Open questions
1. **What is "the board-update hook"?** No hook has that name. The closest is the post-write eventing step (events log and webhook), so the warnings go there. The Stop hook (`skill/kanbanr/hooks/stop-check.sh`) is left alone. **Recommendation:** eventing; revisit only if a Claude Code hook is wanted.
2. **Should coverage rules live in the process file, or only in the project config?** **Recommendation:** project config only. Rules name concrete doc paths, so they are not portable. Default `affects_docs` lives on gates and so travels with the process.

### Decisions (21 Oct 2026, by the user: the drafted design with its recommended answers)
- Coverage warnings go to the post-write eventing step (events log and webhook); the Stop hook is unchanged.
- Coverage rules live in the project config only; default `affects_docs` lives on gates and travels with the process.
- Built after [FEAT-176](/p/kanbanr/feature/FEAT-176) is merged.

### Implementation tasks
1. **Config fields.** File: `config.rs`.
   - Add `ProjectConfig.coverage: Vec<crate::coverage::CoverageRule>`, with `#[serde(default, skip_serializing_if = "Vec::is_empty")]`, placed before `extra`.
   - Add `Gate.affects_docs: Vec<String>`, likewise.
   - `merge_gate` unions `affects_docs`.
   - `is_role_label` returns true when the gate names roles and/or `affects_docs` and nothing else. Its first clause becomes `(!roles.is_empty() || !affects_docs.is_empty())`.
   - `gate_problems` refuses an empty, absolute or `..` path in `affects_docs`.
   - Add `ProjectConfig::stage_set` and `ProjectConfig::default_affects_docs` as specified above.
   - `working_agreement` prints `entering: list {docs} in affects_docs` for a stage that has defaults.
   - Fix the struct literals (`into_config` and 23 `Gate {` sites) with `..Default::default()` where needed.
   - Tests: `config::tests::default_affects_docs_by_role` (R-11), and a role-label regression `config::tests::affects_docs_only_gate_keeps_builtin_rule`.
   - Depends on: task 2 (the type).
2. **The coverage module.** File: `coverage.rs` (new), with `pub mod coverage;` in `lib.rs`.
   - Write `Every`, `CoverageRule`, `parse_rules`, `rule_problems`, `Key`, `Snapshot::load`, `Snapshot::covered`, `Snapshot::item_findings`, `Snapshot::report`, `Finding`, `Subject`, `RuleReport` and `CoverageReport`, exactly as specified above.
   - Tests:
     - `rules_parse_and_validate` (R-1)
     - `references_count_links_tokens_and_relative_links` (R-2)
     - `stage_order_skips_no_ops_and_resolves_roles` (R-3)
     - `no_rules_no_effect` (R-4)
     - `snapshot_reads_only_source_docs_linearly` (R-15)
   - Depends on: none (uses `refs`, `adr`, `store`).
3. **Readiness.** File: `readiness.rs`.
   - Add `Check::DocsCover` (to `GATEABLE`, `passes_when`, `parameters`, the `item_level` no-op arm, and the `evaluate_definition` exclusion list).
   - Add `Condition::DocsCover`, with the `Raw` arm. `invalid_column` and `reads_spec` arms return `None` and `false`. Add `pub fn is_docs_cover(&self) -> bool`.
   - Add `Context.coverage` and build it in `Context::load`.
   - Add `evaluate_entering`. `evaluate_conditions` wraps it. `next_gates` passes `to`.
   - Tests: `docs_cover_gate` (R-8), `docs_cover_unknown_rule_is_error` (R-14), `docs_cover_reads_and_narrows` (R-12). The existing two table tests must pass after task 9.
   - Depends on: task 2.
4. **Store.** Files: `store.rs` and tests in `lib.rs`.
   - `check_gate` calls `evaluate_entering(.., to)`.
   - Add `add_default_docs` and call it in `gated_move_on`; its warning joins the returned warnings.
   - Add `pub fn set_coverage(&self, id: &str, rules: Vec<CoverageRule>) -> Result<ProjectConfig>`. It validates with `rule_problems` and saves with `save_config`.
   - `rename_status` updates coverage `from` and `in`.
   - Tests in `lib.rs`:
     - `tests::default_affects_docs_on_entry` (R-11)
     - `tests::docs_cover_blocks_move_until_covered` (R-8)
     - `tests::set_coverage_refuses_invalid_rules` (R-1)
     - `tests::rename_status_updates_coverage_rules` (R-17)
   - Depends on: tasks 1 and 3.
5. **Dispatch.** Files: `coverage.rs` and `dispatch.rs`.
   - Write `Trigger`, `trigger_of`, `warnings_for` and `annotate`.
   - Split `dispatch_in` into `dispatch_routes` plus a wrapper that calls `annotate`. Skip the wrapper when `is_dry_run(body)` holds.
   - Add `GET /projects/{p}/coverage`, which serialises `Snapshot::load(..).report(..)`, or `{"rules": []}` when none are configured.
   - Add `PUT /projects/{p}/coverage` with `{text}` (`parse_rules`) or `{rules}`, which calls `store.set_coverage`.
   - Add `commit_message` text: `config: coverage rules`.
   - Tests: `coverage::tests::annotate_never_fails_a_write` (R-13), `tests::coverage_reports_all_at_sprint_close_and_cut` (R-7).
   - Depends on: tasks 2 and 4.
6. **Eventing.** File: `eventing.rs`.
   - Add `EventKind::CoverageGap`. `compute_events` emits it from `coverage_warnings`.
   - Test: `eventing::tests::coverage_gap_event` (R-9).
   - Depends on: task 5.
7. **Doctor.** File: `doctor.rs`.
   - Add `scan_coverage(store, project, report)`, called in `run` and `run_project` after `scan_declared_docs`, only when `!project.config.coverage.is_empty()` or a gate names `docs_cover`.
   - It reports rule problems as Error, unknown rule ids in gates as Error, unknown docs in gate `affects_docs` as Error, and one Warning per uncovered rule (first 10 ids).
   - Test: `doctor::tests::doctor_lists_uncovered_rules` (R-10).
   - Depends on: tasks 2 and 3.
8. **CLI (parsing and printing only).** File: `kanbanr-cli/src/main.rs`.
   - Add the `ConfigCmd::Coverage { from_file: Option<PathBuf>, clear: bool }` subcommand. It reads the file as a string (no `serde_yaml`) and calls the routes in task 5.
   - Text output: one line per rule, `{id:<16} {uncovered}/{subjects} uncovered  {source}`.
   - Add `print_coverage_warnings`, called from `print_write` and from each trigger command that does not use `print_write` (check: `adr accept`, `doc write`, `sprint close`, `release cut` and `release promote`, `batch`).
   - Tests in `api/crates/kanbanr-cli/tests/local_mode.rs`:
     - `coverage_silent_without_rules` (R-4)
     - `coverage_warns_on_item_events` (R-5)
     - `coverage_warns_on_adr_accept_and_doc_write` (R-6)
   - The `architecture.rs` baseline must not rise.
   - Depends on: task 5.
9. **Docs and generated artefacts.**
   - Files: `docs/src/using/processes.md` (the check table row, exact `passes_when`), `living-docs.md`, `housekeeping.md`, `reference/cli.md`, `project/changelog.md`.
   - Regenerate `docs/src/reference/openapi.json` with `cargo run -p kanbanr-core --features schema --example openapi`.
   - In `web/src/types.ts`, add `{ docs_cover: string[] }` to `Condition`, the `conditionText` case `docs cover ${…}`, and `affects_docs?: string[]` on the gate type.
   - Tests: `readiness::tests::the_guides_check_table_matches_process_checks` (R-12), plus the existing OpenAPI contract test.
   - Depends on: task 3.
10. **Skill.** File: `skill/kanbanr/SKILL.md`, the sections listed in Affects docs. Manual check R-16. Depends on: tasks 4 and 8 (the command names).
