# Living architecture docs

Feature specs describe what one feature changed. Nothing gathers those changes into a current picture of the product, so architecture and design documents drift as features ship, and hand-written books drift with them.

The method, for any project:
- **Architecture repository in board docs.** Vision (the charter), the business, data, application and technology views, a component catalog, ADRs and standards. Each view answers the six Zachman columns.
- **One design doc per component, as built.** Its front matter lists the code paths it covers and the items that changed it. A feature's Design section is the change; finishing the feature folds that change into each affected component doc.
- **Generated views where possible** (catalogs, graphs, reference pages), never hand-copied.

Scope:
- **Skill guidance.** At the design stage, the spec names the component docs and views the item affects (`affects_docs`). Completing the item folds its design into them. A milestone ends with an architecture compliance review.
- **A gate check `docs_updated`.** It passes when every doc the item declares it affects has been changed since the item entered its current stage, judged from the board's history.
- **Docs.** A chapter on living architecture documentation.

## Revision (2026-10-16): the links are the dependency list

`affects_docs` and the links written in specs, component docs and ADRs form one dependency graph: item → docs it changes; doc → items, ADRs and code it reflects. `docs_updated` reads that graph. Live links between artifacts are FEAT-181.

## Design

### Summary
An item's definition can list the board docs it affects, in `affects_docs`. A gate check,
`docs_updated`, passes when each of those docs has changed since the item entered its current
stage. "Changed" is judged from the board's git history: the doc's content now, compared with its
content in the last board commit at or before the time the item entered the stage. The skill
carries the method:
- at the design stage, name the docs;
- on completion, fold the design into them;
- at each milestone, review compliance.

This builds on FEAT-181's reference finder and `doctor`.

### Components and files
- `api/crates/kanbanr-core/src/models.rs`: `FeatureDefinition.affects_docs`; `FeatureItem::entered_status_at`.
- `api/crates/kanbanr-core/src/git.rs`: `doc_changed_since`.
- `api/crates/kanbanr-core/src/readiness.rs`: `Check::DocsUpdated`, its `Context` data, and its gap
  messages.
- `api/crates/kanbanr-core/src/store.rs`: `load_for_gates` loads doc history only when a gate needs it.
- `api/crates/kanbanr-core/src/doctor.rs`: unknown `affects_docs` (through FEAT-181's `scan_references`).
- `api/crates/kanbanr-cli/src/main.rs`: `feature define` template and `feature show` list the docs.
- `web/src/types.ts`, `web/src/pages/FeaturePage.tsx`: shows them as links.
- `skill/kanbanr/SKILL.md`, `docs/src/using/processes.md` (check table), `docs/src/using/with-claude.md`
  (check table), a new `docs/src/using/living-docs.md` chapter listed in SUMMARY.md, `CHANGELOG.md`.

### Data model
```rust
// models.rs — FeatureDefinition, declared as the last typed field before `extra`
/// Board docs this item changes (FEAT-180), e.g. "architecture/data.md". Declared at the design
/// stage; `docs_updated` checks each was changed before the item moves on.
#[serde(default, skip_serializing_if = "Vec::is_empty")]
pub affects_docs: Vec<String>,
```
Paths are normalized the way `Store::doc_path` does it: `.md` appended when missing, with `..` and
absolute paths refused at `feature define`. Whether the field is part of `content_rev` (and so lapses
approval when it changes) is open question Q1.

```rust
// models.rs — FeatureItem
/// When the item entered its current status: the last transition into it, else its creation.
pub fn entered_status_at(&self) -> &str;
// git.rs
/// Has board file `rel` (relative to the board root) changed since `t` (RFC 3339)? Compares the
/// file now (working tree) with its blob in the newest commit at or before `t`. Absent then and
/// present now counts as changed. `Ok(None)` when the board is not a git repository.
pub fn doc_changed_since(board: &Path, rel: &str, t: &str) -> Result<Option<bool>>;
```
The algorithm:
1. Revwalk from HEAD, newest first, to the first commit whose time is at or before `t`; call it
   C. If no commit qualifies, treat the baseline as absent.
2. `tree.get_path(rel)` gives the blob id at C.
3. `Oid::hash_file(Blob, path)` gives the id of the file now.
4. Compare. Comparing against the working tree means a doc written in the same batch as the move,
   which is not yet committed, still counts.

### Behaviour
- **The check.** `Check::DocsUpdated` (`docs_updated`) is added to GATEABLE, with `passes_when`:
  "every doc the item declares in `affects_docs` has changed since it entered its current stage".
  Its gaps:
  - **Not yet changed** (a blocking gap): "architecture/data.md has not changed since FEAT-012
    entered System Design".
  - **Unknown** (`Level::Error`): "architecture/x.md is declared in affects_docs but is not on the
    board".
  - **No history** (a warning): "cannot tell whether docs changed: the board is not a git
    repository".
  - **Nothing declared**: the check passes vacuously, and a warning says "declares no docs it
    affects". Q2 asks whether that should fail instead.
- **Laziness.** `Condition::reads_doc_history()` is true for `docs_updated`. When a project's gates
  ask for it, `Context` gains `doc_changes: BTreeMap<(String /*code*/, String /*path*/), Option<bool>>`,
  computed for items that declare docs.
- **Doctor.** An unknown `affects_docs` path is a `Severity::Error`, reported by FEAT-181's
  `scan_references`.
- **Skill guidance.** At the design stage, the spec's Design ends with **Affects docs**, given as
  links (FEAT-181) and mirrored into `affects_docs`. Before the item is released, its design is
  folded into those component docs and views. A milestone ends with an architecture compliance
  review: a doc per component, as built, with front matter listing `items`, `adrs` and `covers`.
  Suggested gate:
  ```yaml
  gates:
    Migration:
      requires: [tests_green, docs_updated]
  ```
- **Docs.** A "Living architecture docs" chapter covering the architecture repository layout,
  component docs, and how `affects_docs` and `docs_updated` keep them current.

### Performance
One revwalk per (item, doc) pair, and only for items with declared docs, and only when a gate needs
it. Budget: under 50 ms per item on this board's history (about 3,000 commits), measured in a unit
test against a 3,000-commit fixture.

### Compatibility
- `affects_docs` is a new optional key; an older reader keeps it in `extra`.
- Because the field is declared last, the YAML is identical when it's the only unknown key, so old
  and new revs agree.
- A new gate check is additive; an older reader refuses a gate naming it, through `Condition`'s
  "not a check" error (FEAT-168).

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `manual: skill living-docs guidance present and matches the docs` | review |
| R-2 | `readiness::tests::affects_docs_round_trips` (define, show, export, and older-reader extra preservation) | core |
| R-3 | `readiness::tests::docs_updated_gate` (a temp git board: doc unchanged blocks; changed after entry passes; changed before entry blocks; uncommitted change passes) | core |
| R-4 | `readiness::tests::affects_docs_unknown_is_error` | core |
Plus: `git::tests::doc_changed_since_*` (absent baseline, no repo, file deleted).

### Implementation tasks
1. **Model.** models.rs: `affects_docs` (with `content_rev` handling per Q1) and
   `entered_status_at`. Test: R-2. Depends on: none.
2. **git.** git.rs: `doc_changed_since`. Tests: `git::tests::doc_changed_since_*`. Depends on: none.
3. **Readiness.** readiness.rs: `DocsUpdated` (GATEABLE, passes_when, the `item_level` no-op arm,
   `reads_doc_history`, the `Context` field, the evaluation and its gaps); store.rs `load_for_gates`
   fills the context lazily. Tests: R-3, R-4, plus the docs-table and with-claude coverage checks.
   Depends on 1, 2.
4. **CLI.** main.rs: `define --template` shows `affects_docs`; `feature show` lists them. Test:
   local_mode.rs round trip. Depends on 1.
5. **Monitor.** types.ts and FeaturePage show "Affects docs" as links. Check: build and
   `check:ui`. Depends on 1 and FEAT-181 task 6.
6. **Doctor.** The unknown-path error through `scan_references`. Test: R-4 at doctor level.
   Depends on 1 and FEAT-181 task 2.
7. **Skill and docs.** SKILL.md guidance; the living-docs chapter plus SUMMARY; the check-table rows
   in processes.md and with-claude.md; CHANGELOG with the docs sync. Test: R-1. Depends on 3.

### Open questions
- **Q1.** Should declaring or changing `affects_docs` lapse the item's approval?
  - Recommended: **no**, exclude it from `content_rev`, like sign-offs. The list is part of the
    design, written after the definition was agreed.
- **Q2.** If an item declares no docs, should `docs_updated` pass with a warning, or fail?
  - Recommended: **pass with a warning**. Not every item affects an architecture doc.

### Affects docs
docs/src/using/processes.md, docs/src/using/with-claude.md, docs/src/using/living-docs.md (new),
skill/kanbanr/SKILL.md.
