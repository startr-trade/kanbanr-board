# Live, checked links between board artifacts

Design artifacts on a board (specs, architecture and component docs, ADRs, plans) name each other in plain text: `FEAT-012`, `ADR-0005`, `architecture/data.md`. Plain names cannot be followed in the monitor, nothing checks that they still point at something, and `trace` cannot see them, so drift between documents goes unnoticed.

Scope:
- **Monitor.** Item codes (with an optional `/R-n`), ADR ids, milestone codes, charter goal ids and board doc paths in rendered markdown become links to their pages. Links that are already written are kept.
- **Doctor.** Reports links and references in specs, docs and ADRs that point at an item, ADR, doc, milestone or goal the board does not have.
- **Trace.** Doc-to-item, doc-to-doc and doc-to-ADR links count as traceability edges, so `kanbanr trace` and `why` follow them.
- **Skill.** States the rule: every reference in a design artifact is a live link, and a spec's design section ends with the docs it affects (FEAT-180). The skill also says how to write each kind of link.

## Design

### Summary
A single reference finder in core, `refs::find`, with a TypeScript port in the monitor, recognizes
references to board artifacts in markdown. It skips code and existing links, and it resolves each
reference against the board, so a token is a reference only when its **shape** belongs to the board:
- an item or milestone prefix the board uses, such as `FEAT-` or `MS-`;
- `ADR-`;
- a charter goal id;
- a doc path.

This keeps `UTF-8`, `ISO-9001` and `RUSTSEC-2024-0449` from being read as items. The monitor turns
references into links; doctor reports the ones that point at nothing; trace and why follow
doc↔item, doc↔doc and doc↔ADR links.

### Components and files
- `api/crates/kanbanr-core/src/refs.rs` (new): the finder and the board resolver.
- `api/crates/kanbanr-core/src/doctor.rs`: `scan_references`.
- `api/crates/kanbanr-core/src/trace.rs`: `Subject::Doc`, doc edges, `parse_subject` for paths.
- `api/crates/kanbanr-cli/src/main.rs`: `why` prints documents.
- `web/src/boardRefs.ts` (new), `web/src/markdownHtml.ts`, `web/src/components/Markdown.tsx`,
  `web/src/pages/FeaturePage.tsx` (requirement anchors), `web/scripts/check-markdown.mjs`.
- `skill/kanbanr/SKILL.md`, `docs/src/using/` (a "Links between artifacts" section), `CHANGELOG.md`.

### Interfaces (core)
```rust
// refs.rs
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum Ref {
    Item { code: String, requirement: Option<String> },   // FEAT-012, FEAT-012/R-3
    Milestone { code: String },
    Adr { id: String },                                   // ADR-0005
    Goal { id: String },                                  // G-2
    Doc { path: String },                                 // architecture/data.md
}
pub struct Found { pub reference: Ref, pub line: usize, pub explicit: bool } // explicit = written as a link
/// What the board has, for resolution.
pub struct BoardIndex { pub project: String, item_prefixes: BTreeSet<String>, items: BTreeSet<String>,
    milestones: BTreeSet<String>, adrs: BTreeMap<String, String /*doc path*/>, goals: BTreeSet<String>,
    docs: BTreeSet<String> }
impl BoardIndex { pub fn load(store: &Store, project: &str) -> Result<Self>; }
/// Every reference in `markdown`, in order. Skips fenced and indented code, inline code spans and
/// HTML comments. A markdown link counts as an explicit reference when its target is a monitor
/// path (`/p/<project>/feature/<CODE>`, `.../milestone/<MS>`, `.../charter#<G>`,
/// `.../docs/file/<path>`) or a relative `.md` path.
pub fn find(markdown: &str, index: &BoardIndex) -> Vec<Found>;
/// Is the reference something the board has? (`Item` with a requirement checks the requirement.)
pub fn resolves(r: &Ref, index: &BoardIndex, store_project: &Project) -> bool;
pub fn href(r: &Ref, index: &BoardIndex) -> Option<String>; // the monitor path, for the TS port's tests
```

How text is recognized (not explicit links):
- **Item and milestone codes.** `\b([A-Z][A-Z0-9]*)-(\d+)\b`, optionally followed by `/R-\d+`, and
  only when the prefix is one the board's item or milestone codes use (computed from the codes
  themselves).
- **ADR ids.** `\bADR-\d{4}\b`.
- **Goals.** `\bG-\d+\b`, only when the charter has goals.
- **Doc paths.** A bare path ending in `.md`, recognized **only when the doc exists**. A bare
  path is never reported as broken, because prose names files that aren't board docs.

**Broken** means one of two things:
- an explicit link that does not resolve;
- an item, milestone, ADR or goal reference, with a board prefix, that does not resolve.

### Behaviour
- **Doctor**: `scan_references(store, project, report)` scans each item's spec, every doc (ADRs
  included), and each definition's `design_doc`. It reports one `Severity::Warning` per broken
  reference: "<source>:<line> refers to FEAT-999, which this board does not have". `<source>` is the
  item's code or the doc's path. It is called from `run` and `run_project`.
- **Trace**:
  - `Subject::Doc { path }`. `parse_subject` treats a subject ending in `.md`, or starting with
    `docs/`, as a doc. This is checked first, so `x/R-1` still parses as a requirement.
  - For an item subject, `documents` adds docs whose text refers to the item, alongside front-matter
    `refs:`. Decisions add ADRs whose body refers to it.
  - For a doc subject, the trace lists the items, ADRs, goals and docs the doc refers to, and the
    docs and ADRs that refer to it.
  - `Trace` gains `links_out: Vec<Ref>` and `links_in: Vec<String>`. Both are skipped when empty, so
    the JSON shape only grows.
- **why**: also prints "Documented in: …" from the trace's `documents`.
- **Monitor**:
  - `markdownToSafeHtml(md, opts?: { project, index })`. With an index, a `marked` `walkTokens` hook
    rewrites `text` tokens only, so code, code spans and existing links are untouched. It wraps
    references in `<a class="board-ref" href="…">` before DOMPurify. A broken reference renders
    with `class="board-ref broken"` and a title "not on this board".
  - The index comes from `/api/projects/:p` (items, milestones), `/charter` (goals), `/adrs`
    (id→path) and `/docs` (paths). It is built once per page by `useBoardIndex(project)` and cached.
  - `Markdown.tsx` intercepts clicks on `a[href^="/p/"]` and navigates with the router, without a
    full reload.
  - Requirement tiles on FeaturePage get `id="R-3"`, so `/feature/FEAT-012#R-3` lands on them.
- **Link forms**:

  | Reference | Monitor path |
  |---|---|
  | item | `/p/<p>/feature/<CODE>` (requirement: `#R-n`) |
  | milestone | `/p/<p>/milestone/<MS>` |
  | goal | `/p/<p>/charter#G-n` |
  | ADR | `/p/<p>/docs/file/<adr.path>` |
  | doc | `/p/<p>/docs/file/<path>` |

- **Skill**: every reference in a design artifact is written as a live link, in these forms; a
  spec's Design ends with **Affects docs** (FEAT-180).

### Performance
`BoardIndex::load` runs once per doctor/trace run. The scan is linear in text size (this board has
about 1 MB of specs and docs). Budget: doctor on this board stays under 2 s, measured by
`time kanbanr doctor` before and after.

### Compatibility
Additive. Trace JSON gains optional fields. Rendering changes only for text that resolves.

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `markdownHtml autolinks board references` (assertions in check-markdown.mjs: item, item/R-n, ADR, milestone, goal, doc; not in code spans or fences; existing links kept; `UTF-8` untouched; a broken reference is classed) | web/scripts/check-markdown.mjs |
| R-2 | `doctor::tests::broken_board_references_reported` (spec mentions FEAT-999, doc links missing.md, ADR body ADR-9999; `ISO-9001` not reported) | core doctor.rs |
| R-3 | `trace::tests::doc_links_are_trace_edges` (doc→item, doc→doc, doc→ADR, the reverse for an item subject) | core trace.rs |
| R-4 | `manual: skill linking rules present and match the docs` | review |
Also: `refs::tests` for the finder (code skipping, prefixes, explicit links), and a parity fixture
shared with the TS port: `web/scripts/refs-fixture.json`, read by both the Rust test and
check-markdown.mjs.

### Implementation tasks
1. **refs.rs.** Write `Ref`, `Found`, `BoardIndex::load`, `find`, `resolves` and `href`; add
   `pub mod refs`. Tests: `refs::tests::*` and the shared fixture. Depends on: none.
2. **Doctor.** doctor.rs: `scan_references`, wired into both runs. Test: R-2. Depends on 1.
3. **Trace.** trace.rs: `Subject::Doc`, `parse_subject` path rule, doc edges, `links_out` and
   `links_in`. Test: R-3. Depends on 1.
4. **why.** main.rs `run_why` prints documents. Test: extend local_mode.rs
   `cli_trace_and_why_follow_the_chain_in_both_directions`. Depends on 3.
5. **TS finder.** web/src/boardRefs.ts: a port of `find`/`href`, plus `useBoardIndex`. Test: fixture
   parity in check-markdown.mjs. Depends on 1.
6. **Renderer.** markdownHtml.ts takes the index; Markdown.tsx handles router clicks; FeaturePage
   requirement ids; every Markdown use passes the index. Checks: R-1, `npm run build`, `check:ui`.
   Depends on 5.
7. **Docs and skill.** The SKILL.md linking rules; a docs section; CHANGELOG with the docs sync.
   Test: R-4. Depends on 2, 3, 6.

### Open questions
- **Q1.** Should a broken reference be a doctor **warning** or an **error**? Recommended: warning
  for prose, error for an explicit link.

### Affects docs
docs/src/using/the-monitor.md, docs/src/using/the-method.md (traceability), skill/kanbanr/SKILL.md.
