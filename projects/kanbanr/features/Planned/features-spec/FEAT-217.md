# An item's code says what kind of work it is

## Why
On 22 Oct 2026 the user: "FEAT prefix confuses me on the type." Every item gets a `FEAT-` code
whatever its kind, so a defect, a chore or a docs change reads as a feature (FEAT-208 to FEAT-210
are defects, FEAT-206 a chore, FEAT-215 docs). The user also said work items for maintenance should
not read as features.

## Decided (22 Oct 2026, by the user)
- Prefix by kind: **FTR** feature, **DEF** defect (and the older `bug` kind), **MNT** chore
  (maintenance), **DOC** docs, **SPK** spike. Configurable per project; a project that sets none
  keeps `FEAT-` for everything, as today.
- **A counter per kind**: DEF-001, MNT-001, FTR-001, … (so DEF-012 and FTR-012 can both exist).
- **Existing codes are kept**: the 216 `FEAT-` items keep their codes (they are in commit trailers,
  branch names, links and the public board's history). Changing an item's kind later does not
  rename it.

## Design

### Decisions

1. **How a code is recognised: by the set of prefixes on the board.** The set is the configured prefixes, plus `FEAT` when nothing is configured, plus every prefix an existing item already has. The general shape `[A-Z]{2,6}-\d{3,}` is rejected:
   - It matches `SHA-256`, `RFC-3339`, `ISO-9001` and `CVE-2024` as item references. Doctor would then warn about each as a broken reference, and the monitor would strike them through.
   - It breaks the fixture case "tokens that are not this board's", which contains `ISO-9001`.
   - It contradicts the documented rule in refs.rs:9–11 and `docs/src/using/traceability.md:68`.
   
   With the prefix set, a false positive is only possible when the board itself uses that prefix (for example, a project that configures `RFC`). That is the board's own choice. `FEAT-` keeps working wherever `FEAT-` items exist.
2. **The counter is per prefix.** Kinds that share a prefix share its counter: `bug` and `defect` both draw from `DEF`. The next number is the highest existing one with that prefix plus one, padded to 3, so `FTR-001` starts fresh. It is allocated inside the existing write lock and in-memory `Project`, so a batch numbers its items in bundle order.
3. **Which prefix a kind gets.** The kind is trimmed and lowercased.
   - It is looked up in `codes.kinds`.
   - An absent or empty kind counts as `feature`, because `feature add` with no `--kind` is a feature (`definition_template` defaults to `"feature"`, main.rs:6421).
   - A kind that is not mapped gets `codes.default`, which itself defaults to `FEAT`.
   - With no `codes` configured at all, every item gets `FEAT-`, exactly as today.
4. **Codes are never renamed.** Changing a kind (`feature edit --kind`, batch `feature.edit`, `defect`) leaves the code alone. An explicit `--code` / `new_code` behaves as today.
5. **"Distinct" means distinct kind keys.** Two kind keys may not be the same after trim and lowercase. Several kinds may map to the same prefix on purpose, because that is how `bug` → `DEF` works.

### Format: `projects/<p>/config.yaml`

```yaml
codes:
  default: FEAT        # optional; absent = FEAT
  kinds:               # kind (lowercase) -> prefix
    bug: DEF
    chore: MNT
    defect: DEF
    docs: DOC
    feature: FTR
    spike: SPK
```

The block is absent when nothing is set, and stays absent on disk. No schema bump is needed (`CURRENT_SCHEMA_VERSION` stays 5): it is the same additive pattern as `process` and `diagrams`.

### Public signatures

**`api/crates/kanbanr-core/src/config.rs`:**

```rust
pub const LEGACY_ITEM_PREFIX: &str = "FEAT";
/// Prefixes other board ids use: milestone, ADR, scope, sprint, todo-list. (G-, R-, T, L- are too short.)
pub const RESERVED_PREFIXES: &[&str] = &["MS", "ADR", "SC", "SP", "TL"];

#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
#[cfg_attr(feature = "schema", derive(schemars::JsonSchema))]
pub struct CodesConfig {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub default: Option<String>,
    #[serde(default, skip_serializing_if = "BTreeMap::is_empty")]
    pub kinds: BTreeMap<String, String>,
    #[serde(flatten, default, skip_serializing_if = "crate::models::Extra::is_empty")]
    #[cfg_attr(feature = "schema", schemars(with = "crate::models::ExtraSchema"))]
    pub extra: crate::models::Extra,
}
/// A change to the codes, applied atomically by the store.
#[derive(Debug, Clone, Default, Deserialize)]
pub struct CodesChange {
    #[serde(default)] pub set: BTreeMap<String, String>,
    #[serde(default)] pub unset: Vec<String>,
    /// Some("") resets the default to FEAT.
    #[serde(default)] pub default: Option<String>,
    #[serde(default)] pub clear: bool,
}
pub fn kind_key(kind: &str) -> String;                 // trim + to_ascii_lowercase
impl CodesConfig {
    pub fn is_default(&self) -> bool;
    pub fn prefix_for(&self, kind: Option<&str>) -> &str; // rule in Decision 3
    pub fn prefixes(&self) -> BTreeSet<String>;           // kinds' values ∪ {default or FEAT}
    pub fn apply(&self, change: &CodesChange) -> CodesConfig; // keys normalised, extra kept
    /// Problems as sentences naming the entry; empty = valid.
    pub fn problems(&self, milestone_prefixes: &BTreeSet<String>) -> Vec<String>;
}
// ProjectConfig gains:
#[serde(default, skip_serializing_if = "CodesConfig::is_default")]
pub codes: CodesConfig,
```

`problems` reports:
- a prefix that does not match `^[A-Z]{2,6}$`;
- a prefix in `RESERVED_PREFIXES`, or used by a milestone of the project;
- an empty kind key;
- two keys that collide after `kind_key`.

The two `ProjectConfig` struct literals get `codes: Default::default()`: config.rs:679 (`WorkflowFile::into_config`) and dispatch.rs:365. `set_workflow_with_gates` copies fields one by one, so it keeps `codes` without changes.

**`store.rs`:**

```rust
pub fn add_feature_of_kind(&self, id: &str, title: &str, specification: &str, milestone: &str,
                           code: Option<String>, kind: Option<&str>) -> Result<FeatureItem>;
// add_feature(...) unchanged: delegates with kind = None, so ~200 test call sites are untouched.
fn add_feature_on(project, pending, title, spec, milestone, code: Option<String>, kind: Option<&str>)
pub fn set_codes(&self, id: &str, change: crate::config::CodesChange) -> Result<ProjectConfig>;
```

- In `add_feature_on`, when `code` is None:
  1. If `project.config.codes.problems(&milestone_prefixes)` is non-empty, refuse with `CoreError::Unsupported("<problem> — fix with `kanbanr config codes`")`.
  2. Otherwise allocate with `validate::next_code(project.config.codes.prefix_for(kind), &existing)`.
  
  It also stores `kind` (non-empty) on the new item in the same write. The attrs path that runs afterwards is idempotent.
- `set_codes` runs `load_meta`, applies the change, validates (refusing the first problem and changing nothing), then calls `save_config`.
- Batch `FeatureAdd` (store.rs:2135) passes `kind.as_deref()`.

**`dispatch.rs`:**
- `POST /projects/{p}/features` calls `add_feature_of_kind(..., str_field(b,"kind").as_deref())`.
- New `GET /projects/{p}/config/codes` returns `CodesView`.
- New `PUT /projects/{p}/config/codes` takes a `CodesChange` body and returns `CodesView`.
- The write description already reads "update config: codes" through the generic arm (dispatch.rs ~1577).

```rust
#[derive(Serialize)] pub struct CodesView {
    pub default: String,                         // effective
    pub kinds: BTreeMap<String, String>,
    pub next: BTreeMap<String, String>,          // prefix -> next code, for every prefix in use or configured
    pub in_use: BTreeMap<String, usize>,         // prefix -> item count
}
```

**`refs.rs`:** `BoardIndex::of` adds `p.config.codes.prefixes()` into `item_prefixes`. On an unconfigured board this adds only `FEAT`, which a board with items already has.

**`scm.rs:504`:** the fallback suggestion becomes `format!("Refs: kanbanr:{}-001", project.config.codes.prefix_for(None))`.

**`doctor.rs`:** new `scan_codes(project, report)`, called in `run_project`. It reports each `codes.problems` entry as `Severity::Error`, with `code: None`.

**CLI, `api/crates/kanbanr-cli/src/main.rs`:**
- New `ConfigCmd::Codes` variant:
  ```
  kanbanr config codes [--set KIND=PREFIX,…] [--unset KIND,…] [--default PREFIX|""] [--clear] [--json]
  ```
  Args: `set: Vec<String>` and `unset: Vec<String>`, both with `value_delimiter=','`; `default: Option<String>`; `clear: bool` (`conflicts_with_all = set, unset, default`). It parses `K=P` and refuses a malformed pair before sending.
  - With no flag it calls GET and prints `kind  prefix  next` rows, then `(other) <default> <next>`, then `in use: FEAT (216)`.
  - With flags it calls PUT and prints through `print_write`.
- The `--kind` help on `feature add` (main.rs:748) gains: "and, when the project maps kinds (`config codes`), the code's prefix: set it here, a later change does not rename."

**Web:**
- `web/src/types.ts`: `ProjectConfig` gains `codes?: CodesConfig`, with `export interface CodesConfig { default?: string; kinds?: Record<string, string> }`.
- `web/src/boardRefs.ts`:
  - new `export function codePrefixes(codes?: { default?: string; kinds?: Record<string,string> } | null): string[]`, a port of `CodesConfig::prefixes`;
  - `makeIndex` takes an optional `codes` and adds `codePrefixes(codes)` into `itemPrefixes`;
  - keep it erasable-only TypeScript, because `check-markdown.mjs` imports the `.ts` file directly.
- `web/src/useBoardIndex.ts` passes `codes: p.config.codes`.

**Shared fixture `web/scripts/refs-fixture.json`:**
- `index` gains `"codes": {"default":"FEAT","kinds":{"defect":"DEF","bug":"DEF","feature":"FTR","spike":"SPK"}}` and item `"DEF-001": ["R-1"]`.
- New case **"kind prefixes beside FEAT"**: `"DEF-001/R-1 fixes FEAT-012; FTR-001 and SPK-004 are not made yet."` Expected:
  - DEF-001/R-1: item, ok;
  - FEAT-012: item, ok;
  - FTR-001: item, broken;
  - SPK-004: item, broken.
- New case **"standard ids are not codes"**: `"SHA-256, RFC-3339, ISO-9001, UTF-8, CVE-2024-1234, DEF-1a"`. Expected: `[]`.
- The Rust `FixtureIndex` (refs.rs:415) gains `#[serde(default)] codes: CodesConfig`, and `index_of` unions `codes.prefixes()`.
- `check-markdown.mjs` passes `codes: fx.codes`.
- Both finders therefore check the prefix derivation itself, not just the scanning.

**OpenAPI:** regenerate `docs/src/reference/openapi.json` and `http-api.md` with `cargo run -p kanbanr-core --features schema --example openapi`, because `ProjectConfig` gains `codes`. `check:api-types` then passes with the optional TypeScript field.

### Compatibility

- **An older binary reading a board with `codes` and `DEF-001` items:**
  - It keeps `codes:` on every config write, through `ProjectConfig.extra` (FEAT-151).
  - It loads `DEF-…` files normally, because a code is only a filename and a string.
  - It allocates `FEAT-<max+1>` for every new item whatever its kind. That never collides, because the counters are per prefix.
  - It recognises `DEF-` in markdown once a `DEF-` item exists, since it takes prefixes from items. It misses a configured prefix that has no item yet, so it raises no broken-reference warning for `SPK-999`. That is harmless.
  - Branches, trailers, `why`, `trace` and gitdrift all accept any prefix, so they already work.
- **An older monitor** behaves the same way as the older finder.
- **An unconfigured board** behaves byte-for-byte as today.
- **Ordering:** items in a status are listed in filename order (`read_feature_metas`, store.rs:571). So the CLI `board` groups `DEF-`, `FEAT-`, `FTR-` alphabetically. This is accepted; the monitor already sorts by `created_at` (`featuresNewestFirst`, types.ts:325).

### Security

None. The new values are validated `[A-Z]{2,6}` strings and are written only by the CLI.

### Requirements (EARS) and tests

- **R-1** WHEN an item is created without an explicit code and the project's `codes` gives its kind a prefix, THE SYSTEM SHALL code it `<PREFIX>-<n>`, where n is one more than the highest number among the project's items with that prefix, zero-padded to 3.
  - Test: `kanbanr-core lib.rs tests::codes_follow_the_kind_with_a_counter_per_prefix` (expects DEF-001, then FTR-001, then DEF-002 for a `bug`).
- **R-2** WHERE a project sets no codes, THE SYSTEM SHALL code every new item `FEAT-<n>` as before.
  - Tests: `tests::an_unconfigured_project_keeps_feat_codes`, and the existing `tests::code_generation_is_sequential`.
- **R-3** WHEN an item has no kind, THE SYSTEM SHALL use the `feature` entry; WHEN its kind has no entry, THE SYSTEM SHALL use `codes.default`, or `FEAT` when that is absent.
  - Test: `config::tests::prefix_for_falls_back_to_feature_then_default`.
- **R-4** WHEN an item's kind changes, THE SYSTEM SHALL keep its code.
  - Test: `tests::a_kind_change_never_renames` (covers `feature edit --kind`, batch `feature.edit` and `set_defect`).
- **R-5** WHEN `config codes` would set a prefix that is not 2–6 uppercase letters, is reserved (`MS`, `ADR`, `SC`, `SP`, `TL`), or is used by a milestone, or a blank or duplicate kind, THE SYSTEM SHALL refuse it naming the entry and leave the config unchanged.
  - Tests: `config::tests::codes_problems_name_the_entry`, `tests::set_codes_refuses_and_changes_nothing`.
- **R-6** WHEN a batch creates several items, THE SYSTEM SHALL number each by its own prefix in bundle order, and `ref` aliases SHALL resolve to the assigned codes.
  - Test: `tests::batch_numbers_each_kind_in_bundle_order`.
- **R-7** THE SYSTEM SHALL treat a prose token as an item reference only when its prefix is configured or used by an existing item, so `SHA-256`, `RFC-3339`, `ISO-9001` and `UTF-8` are not references; the monitor SHALL agree.
  - Tests: `refs::tests::finder_matches_the_shared_fixture`, `npm run check:markdown`.
- **R-8** WHEN `start` runs on a kind-coded defect, THE SYSTEM SHALL branch `fix/DEF-001-<slug>`, `commit` SHALL fill `Refs: kanbanr:DEF-001`, and the hooks, gitdrift and `why` SHALL resolve it.
  - Tests: `flow::tests::a_kind_coded_defect_starts_on_its_fix_branch`, `scm::tests::kind_prefixed_codes_round_trip_branch_and_trailer`, and CLI `tests/local_mode.rs::kind_coded_item_start_commit_why`.
- **R-9** WHILE `codes` is unset, THE SYSTEM SHALL load, reference and allocate around existing kind-coded items. This simulates an older reader.
  - Test: `tests::an_unconfigured_reader_handles_kind_coded_items` (explicit `--code DEF-001`, no codes; it loads, `BoardIndex` links it, the next item is FEAT-…).
- **R-10** WHEN another config write happens, THE SYSTEM SHALL keep `codes` unchanged.
  - Test: `tests::other_config_writes_keep_codes` (`set_diagrams`, `set_workflow`, `set_coverage`).
- **R-11** WHEN the config's codes are invalid (hand-edited), THE SYSTEM SHALL refuse code allocation naming the problem, and doctor SHALL report it as an error.
  - Test: `doctor::tests::doctor_reports_invalid_codes`.
- **R-12** WHEN `kanbanr config codes` runs, THE SYSTEM SHALL show each kind's prefix, the default, and the next code per prefix; `--set`, `--unset`, `--default` and `--clear` SHALL change them.
  - Test: `kanbanr-cli tests/local_mode.rs::config_codes_sets_shows_and_clears` (temporary board).

### Affects docs

- `docs/src/using/traceability.md`: the prefix paragraph at line 68 now includes configured prefixes, with SHA-256 and RFC-3339 as examples.
- `docs/src/reference/cli.md`: a new `config codes` row next to `config diagrams` (line 20).
- `docs/src/reference/data-layout.md`: note that codes may be `DEF-001` and so on by kind.
- `docs/src/architecture/data-model.md`: the FEATURE `code` attribute is prefixed by kind and never renamed.
- `docs/src/using/everyday.md`: `--kind` at `feature add` chooses the prefix.
- `docs/src/reference/openapi.json` and `http-api.md`: regenerated.
- `skill/kanbanr/SKILL.md`:
  - near "feature add" (~line 923): codes say the kind, so **pass `--kind` when creating**, because a later change does not rename;
  - cheatsheet: `kanbanr config codes`;
  - no new setup-interview question (G-5); new projects keep `FEAT-` unless the user asks.
- Changelog entry, through the normal `tools/docs/sync.sh`.

### Open question (needs the user)

1. Should `refactor` (3 items) and `recurring` also map to `MNT` on kanbanr's own board, or fall through to `FEAT`? **Recommended: map both to `MNT`.** `definition_template` already treats `chore` and `refactor` alike (models.rs ~1083), and leftover `FEAT-` codes are exactly the confusion being fixed.

### Implementation tasks (in order)

1. **config.rs:** add `LEGACY_ITEM_PREFIX`, `RESERVED_PREFIXES`, `CodesConfig`, `CodesChange` and `kind_key`, plus the `ProjectConfig.codes` field. Fix the struct literals at config.rs:679 and dispatch.rs:365. Unit tests for R-3 and R-5 (`problems`).
2. **store.rs:** thread `kind: Option<&str>` through `add_feature_on`. Add `add_feature_of_kind`, keeping `add_feature` as a wrapper. Use the batch `FeatureAdd` kind. Refuse invalid codes. Add `set_codes`. Tests R-1, R-2, R-4, R-6, R-9, R-10, R-11 (store part) in lib.rs tests.
3. **dispatch.rs:** have the POST features route pass the kind, and add the GET/PUT `config/codes` routes with `CodesView`.
4. **refs.rs:** in `BoardIndex::of`, union `codes.prefixes()`. Extend the test `FixtureIndex` and `index_of`.
5. **`web/scripts/refs-fixture.json`:** add `codes`, `DEF-001` and the two new cases. Run `cargo test -p kanbanr-core refs`.
6. **boardRefs.ts:** add `codePrefixes` and the `makeIndex` `codes` parameter. Update `types.ts` (`CodesConfig`) and `useBoardIndex.ts`. Pass `codes` in `check-markdown.mjs`. Run `npm run check:markdown`, `check:api-types` and `build`.
7. **scm.rs:504:** fallback suggestion from `prefix_for(None)`. **doctor.rs:** add `scan_codes` (R-11 test).
8. **CLI:** add `ConfigCmd::Codes` and its handler next to `ConfigCmd::Diagrams` (main.rs:6809), and the `--kind` help text. CLI tests R-8 and R-12 in `tests/local_mode.rs`, temporary boards only. Add the flow and scm unit tests for R-8.
9. Regenerate OpenAPI with `cargo run -p kanbanr-core --features schema --example openapi`, then confirm `--check` passes.
10. Docs and skill edits from "Affects docs". Run `make check-docs`, `cargo test`, `cargo clippy`.
11. After the merge and the user's answer to the open question, the coordinator (not the build agent; the board write needs scope) runs: `kanbanr config codes --set feature=FTR,defect=DEF,bug=DEF,chore=MNT,docs=DOC,spike=SPK[,refactor=MNT,recurring=MNT]`.
