## Problem
Specs, docs and ADRs carry Mermaid diagrams in fenced `mermaid` blocks. kanbanr renders them in the web view, but nothing checks a diagram when it is written. A broken diagram is found only when a reviewer opens the page and sees "Syntax error". By then the item may already be waiting for approval, and an agent-written spec is likely to contain the common mistakes.

**An observed case.** In one session, three specs written by agents had invalid diagrams:
- a `;` inside a sequence-diagram message, which ends the statement;
- JSON with quotes and braces inside sequence messages;
- an unquoted flowchart label containing `;`.

## What this adds
1. **Lint on write, in the core and pure Rust.**
   - **Where it runs:** on `feature add`/`edit` (spec), `doc add`, `adr` writes and `batch`.
   - **What it does:** checks every fenced `mermaid` block in the written markdown and reports a warning with file, block and line. The write still succeeds; a strict mode in project config can refuse it.
   - **Rules, a starter set:**
     - the first line names a known diagram type;
     - no `;` inside sequence messages or labels;
     - no unbalanced `{`, `}`, `[`, `]`, `(`, `)` or `"` in a label;
     - an unquoted flowchart label must not contain `;`, `|`, `{`, `}` or unbalanced parentheses;
     - `end` is used only as a keyword, never as a node id;
     - `subgraph`/`end`, `alt`/`else`/`end`, `loop`/`end` and `opt`/`end` are balanced;
     - every line in a sequence diagram declares or uses a participant;
     - no empty block.
2. **`doctor`** lists every lint finding across the board.
3. **Real parse on the review page.**
   - **Before Approve:** the web review page runs the bundled Mermaid library's `mermaid.parse()` on every block of the item's spec and its `affects_docs`.
   - **On error:** it lists each error with its block and line, links to the source, and disables Approve until the diagrams parse.
   - **The same check** runs in the doc viewer, showing the error under the diagram instead of only "Syntax error".
4. **A `process checks` condition, `diagrams_valid`,** so a project can require it on a stage gate. The core lint and the review page's last recorded parse result both feed it.
5. **Skill guidance:** quote flowchart node labels; keep sequence messages to plain words, with no `;`, braces or quotes; never use `end` as an id; run the lint (`kanbanr doctor`) after writing diagrams.

## Out of scope
A full Mermaid grammar in Rust. The lint catches the common mistakes, and the review-page parse is the authoritative check.

## Gating moves (added 2026-10-20)
A project must be able to require `diagrams_valid` on **every** stage gate, so that no item moves between states while its spec, or any doc in its `affects_docs`, has a Mermaid block that fails the lint. `process check` must accept `diagrams_valid` in any gate's `requires`. When it fails, the move's refusal names each failing block (file, block number, line, rule). The lint result is computed at move time, not cached, so a fixed diagram unblocks the move immediately.

## Design

### Decision on the rules: follow Pele
Pele 1.7.0 is what kanbanr renders with, in the monitor and in the book (FEAT-203). So the Rust lint is held to one property: **it flags only diagrams that Pele's `parse` rejects. It never flags a diagram Pele accepts.** A shared fixture enforces this from both sides: Rust checks it, and a node script checks it against the real Pele. I probed Pele with `parse` before deciding the rules. Some of what I found differs from the spec as filed:

| Construct | Pele 1.7.0 | Lint |
|---|---|---|
| `;` inside a sequence message or note, or in a participant alias (`A->>B: a; b`) | error | `semicolon_in_text` |
| a trailing `;` at the end of a message (`A->>B: x;`) | accepted | not flagged |
| JSON, quotes or braces in a sequence message | accepted | not flagged; the skill still advises plain words |
| unquoted flowchart label containing `;` (`A[x; y]`) | **accepted** | not flagged (see Q-2) |
| unquoted flowchart label or edge label containing any of `( ) { } [ ] " \|`, **including balanced parens** (`A[f(x)]`, `A(f(x))`, `A{a[0]}`, `-->\|f(x)\|`, `subgraph s [a (b)]`) | error | `label_punctuation` |
| quoted label (`A["f(x) {y} \| z; w"]`) | accepted | not flagged |
| text inside a quoted label after the closing quote (`A["a "b" c"]`) | error | `label_punctuation` |
| `end` (lowercase) as a node or participant id: `end --> B`, `A --> end`, `A --> end.x`, `subgraph end`, `participant end` | error | `end_as_id` |
| `End`, `endpoint`, `A[the end]` | accepted | not flagged |
| subgraph/alt/loop/opt/par/critical/break/rect/box not closed by `end`, an extra `end`, `else`/`and`/`option` outside their opener, unclosed `{` in a state or class diagram | error | `unbalanced_block` |
| a sequence line that is not a statement (`this is junk`, or `A->>B` without `:`) | error | `unknown_statement` |
| empty block, block of only comments, unknown or wrong-case type (`flowchrt`, `FLOWCHART`), `title` line before the type | error (`unsupported-diagram`, line 0) | `empty_block` / `unknown_type` |
| leading blank lines, `%%` comments, `%%{init}%%`, a `---` front-matter block before the type | accepted | skipped as preamble |
| `;` in a class-diagram relation label (`A --> B : x; y`) | error | `semicolon_in_text` |
| `;` in a state-diagram label | accepted | not flagged |

`parse` takes about 0.6 ms for a 50-edge flowchart. `PeleError` carries `code`, `line` (1-based within the block, 0 when no type was found), `column` and `snippet`.

### Modules and files

**New: `api/crates/kanbanr-core/src/diagrams.rs`** (register with `pub mod diagrams;` in `lib.rs`). Pure Rust, no new dependencies, no regex.
```rust
pub const MAX_FINDINGS_PER_FILE: usize = 50;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)] #[cfg_attr(feature="schema", derive(schemars::JsonSchema))]
pub struct DiagramBlock { pub file: String, pub doc: Option<String>, pub block: usize, pub line: usize, pub source: String }
// file: "FEAT-012 spec" | "docs/<key>"; doc: the doc key, for a link (None for a spec);
// block: 1-based index among the file's mermaid blocks; line: file line (1-based) of the block's first source line.

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)] #[serde(rename_all="snake_case")] #[cfg_attr(schema…)]
pub enum LintRule { EmptyBlock, UnknownType, SemicolonInText, LabelPunctuation, UnbalancedLabel, EndAsId, UnbalancedBlock, UnknownStatement }
impl LintRule { pub fn name(self) -> &'static str }   // the snake_case name

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)] #[cfg_attr(schema…)]
pub struct DiagramFinding { pub file: String, pub block: usize, pub line: usize, pub rule: LintRule, pub message: String }
impl DiagramFinding { pub fn describe(&self) -> String }  // "{file}, diagram #{block}, line {line}: {message} ({rule})"

pub fn is_markdown_path(path: &str) -> bool;                                   // .md / .markdown, any case
pub fn blocks(file: &str, doc: Option<&str>, markdown: &str) -> Vec<DiagramBlock>;
pub fn lint_source(source: &str) -> Vec<(usize, LintRule, String)>;            // (line within the block, 1-based)
pub fn lint_markdown(file: &str, markdown: &str) -> Vec<DiagramFinding>;       // capped at MAX_FINDINGS_PER_FILE
pub fn guard(config: &crate::config::DiagramsConfig, file: &str, markdown: &str) -> crate::Result<Vec<DiagramFinding>>;
pub fn item_findings(feature: &crate::FeatureItem, docs_dir: Option<&std::path::Path>) -> Vec<DiagramFinding>;

#[derive(Debug, Clone, Serialize)] #[cfg_attr(schema…)]
pub struct ItemDiagrams { pub code: String, pub blocks: Vec<DiagramBlock>, pub findings: Vec<DiagramFinding> }
impl ItemDiagrams { pub fn load(store: &crate::Store, p: &str, code: &str) -> crate::Result<Self> }
```
- **`guard`**: lints the text. If `config.strict` is on and there are findings, it returns `Err(CoreError::InvalidDiagram(..))` with the message `"{file} has {n} diagram problem(s), and this project checks diagrams strictly: {describe; …} — fix them, or turn strict checking off with `kanbanr config diagrams --strict off`"`. Otherwise it returns `Ok(findings)`.
- **`item_findings`**: lints `feature.specification` as `"{code} spec"`. It then lints each `definition.affects_docs` entry as `"docs/{key}"`, where `key = readiness::affects_doc_key(doc)`, reading `docs_dir.join(key)`.
  - It skips a key with a `..` component or an absolute path.
  - It skips a doc that is missing or unreadable; `docs_updated` and `doctor` already report those.
  - It reads from disk on every call. No caching.
- **`ItemDiagrams::load`**: `store.load(p)`, then `feature_spec`. It reads docs through `store.read_doc(p, &key)`, which validates the path, and skips errors. It returns the blocks and the findings from `item_findings`.

**`api/crates/kanbanr-core/src/config.rs`**
- Add `#[derive(Default, …)] pub struct DiagramsConfig { #[serde(default)] pub strict: bool, #[serde(flatten, default, skip_serializing_if="Extra::is_empty")] pub extra: Extra }` with `pub fn is_default(&self) -> bool`.
- Add the field `#[serde(default, skip_serializing_if="DiagramsConfig::is_default")] pub diagrams: DiagramsConfig` to `ProjectConfig`, after `method`.
- When the key is absent it stays absent on disk. No schema bump: an older binary keeps the key through `extra`.

**`error.rs`** + `kanbanr-server/src/routes.rs::core_err`
- Add `#[error("{0}")] InvalidDiagram(String)`.
- Map it to `BAD_REQUEST` in the server.

**`store.rs`**
- `pub fn read_project_config(&self, id: &str) -> Result<ProjectConfig>`: checks `project_exists`, then calls `read_config`.
- `pub fn set_diagrams(&self, id: &str, diagrams: DiagramsConfig) -> Result<ProjectConfig>`: modelled on `set_cadence`.
- `add_feature_on`: once the code is fixed and before the push, call `crate::diagrams::guard(&project.config, &format!("{code} spec"), specification)?`. Discard the Ok value.
- `edit_feature_on`: when `specification` is `Some`, call the same guard on the final code, before any mutation.
- Because `apply_batch_with` chains these `_on` cores, a strict refusal in a batch becomes `BatchOpFailed` and the whole bundle changes nothing.
- In `apply_batch_with`:
  - **`feature.add` / `feature.edit` (with a spec):** add `"diagram_warnings": [DiagramFinding]` to the op's result JSON when it is non-empty.
  - **`DocWrite`:** when `is_markdown_path(&path)`, call `guard(&project.config, &format!("docs/{path}"), &content)?` before queueing, and attach `diagram_warnings`. This also applies in dry-run mode.

**`dispatch.rs`**
- Add a helper `fn with_diagram_warnings(body: String, w: &[DiagramFinding]) -> Result<String>`. It parses the body to a Value and sets `diagram_warnings` only when `w` is non-empty.
- `POST /projects/{p}/features` and `PATCH …/features/{code}` (spec given): after the store call succeeds, compute `diagrams::lint_markdown("{code} spec", spec)` and wrap the response.
- `PUT …/docs/content`: when `is_markdown_path`, `guard(&store.read_project_config(p)?.diagrams, "docs/{path}", content)?` before `write_doc`, then wrap `{path}`.
- New `GET /projects/{p}/config/diagrams` returns `DiagramsConfig`.
- New `PUT /projects/{p}/config/diagrams` takes `{strict: bool}` (required; otherwise `Unsupported("say whether to check diagrams strictly: `strict`")`) and returns `DiagramsConfig`.
- New `GET /projects/{p}/features/{code}/diagrams` returns `ser(&ItemDiagrams::load(..)?)`. The daemon serves it through `read_passthrough`.
- ADRs: ADR prose is written through `doc add` / `doc.write` / `PUT docs/content`, so those cover it. `adr::create` writes a scaffold with no diagrams, and `update`/`decide`/`supersede` rewrite only the front matter, so none of them needs a hook.

**`readiness.rs`**
- Add `Check::DiagramsValid` (gate name `diagrams_valid`) to the enum and to `GATEABLE`, which grows from 18 to 19, at the end.
- `passes_when`: `"every Mermaid diagram in the spec and in each doc it names in \`affects_docs\` passes the diagram lint"`.
- `parameters`: `None`.
- `Condition::reads_spec`: also true for `Condition::Check(Check::DiagramsValid)`, so `load_for_gates` loads specs.
- `evaluate_in`: `if checks.contains(&Check::DiagramsValid) && !exempt { gaps.extend(diagram_gaps(feature, ctx.docs_dir.as_deref())) }`.
- `fn diagram_gaps(..) -> Vec<Gap>`: one gap per finding, `level: Warning`, `label: "diagram #{block} in {file}"`, `message: finding.describe()`.
- Add `DiagramsValid` to the `reads_definition` exclusion list and to the no-op arm of `item_level`.
- `check_gate` already joins gap messages, so the refusal names file, block, line and rule for each finding.
- Moves load the project fully (`Store::load`), and the docs are read at evaluation time, so a fixed diagram unblocks the very next move.

**`doctor.rs`**
- `fn scan_diagrams(store: &Store, project: &Project, report: &mut Report)`, called in both `run` and `run_project` after `scan_declared_docs`.
- For every feature (finished ones too, because "across the board"): `lint_markdown("{code} spec", &f.specification)`, giving `Issue { Warning, code: Some(code), message: describe() }`.
- For every `store.list_docs(id)` path where `is_markdown_path`: `read_doc`, then `lint_markdown("docs/{path}")`, giving `Issue { Warning, code: None, … }`.

**`openapi.rs`**
- Add a `RouteDoc` for `/api/projects/{project}/features/{code}/diagrams` with the summary "The Mermaid blocks of an item's spec and affects_docs, with the lint's findings", params `[PROJECT, CODE]` and `schema_of::<crate::diagrams::ItemDiagrams>`.
- Regenerate with `cargo run -p kanbanr-core --features schema --example openapi`. This rewrites `docs/src/reference/openapi.json` and the generated table in `http-api.md`.

**CLI `kanbanr-cli/src/main.rs`** (rendering only)
- `fn print_diagram_warnings(cli: &Cli, resp: &str)`, modelled on `print_gate_warnings`. It is silent with `--json`. It reads `diagram_warnings` at the top level and in `results[*]`, deserialises them as `kanbanr_core::diagrams::DiagramFinding`, and prints `  diagram: {describe()}` on stderr.
- Call it after the writes in the feature add/edit, doc add and batch handlers.
- Add `ConfigCmd::Diagrams { #[arg(long, value_parser=["on","off"])] strict: Option<String> }`. With no flag it does a GET and shows `strict: on|off`; otherwise it PUTs.

**Web**
- `web/src/types.ts`: add `DiagramBlock`, `DiagramFinding`, `ItemDiagrams`, mirroring the Rust types.
- `web/src/api.ts`: `getItemDiagrams: (id, code) => getJson<ItemDiagrams>(apiUrl(`/projects/${enc(id)}/features/${enc(code)}/diagrams`))`.
- New `web/src/diagramCheck.ts`, pure and node-testable:
  - `export type DiagramProblem = { file: string; doc: string | null; block: number; line: number; message: string }`
  - `export function locateError(e: unknown, firstLine: number): { line: number; message: string }`: if `e.line > 0`, the line is `firstLine + e.line - 1`; otherwise it is `firstLine`. The message is the first line of `e.message`; for `code === "unsupported-diagram"` it is "no diagram type on the first line".
  - `export function checkBlocks(d: ItemDiagrams, parse: (s: string) => unknown): DiagramProblem[]`: the Pele errors, plus any Rust finding whose (file, block) Pele accepted, deduplicated by (file, block).
  - `export function approveBlocker(state: { loading: boolean; failed: string | null; problems: DiagramProblem[] }): string | null`: returns the reason the button is disabled, or null.
- `ReviewPage.tsx` `Brief`: `useAsync(() => api.getItemDiagrams(project, item.code), [project, item.code, tick])`, then `import("pele").then(({parse}) => checkBlocks(..))`.
  - It renders a "Diagrams" list. Each entry shows file, `diagram #n`, `line N`, the message, and a `Link` to `/p/{p}/feature/{code}` for a spec or `/p/{p}/docs/file/{doc}` for a doc.
  - The Approve/Ratify button gets `disabled={busy || blocker != null}` and `title={blocker}`.
  - It fails closed: while the check is loading or has failed, the button stays disabled and the failure is shown.
- `Markdown.tsx`, in the `catch`: instead of replacing the block with "diagram error: …", keep a `<pre class="diagram-source">` holding the source and append `<div class="diagram-error">` with `"Diagram error, line {n}: {msg}"` built by `locateError(e, 1)`. Set it through `textContent`, never `innerHTML`.
- `styles.css`: `.diagram-error` and `.diagram-source`, using the theme variables.
- New scripts in `package.json`, both added to `.github/workflows/ci.yml` after "Docs diagrams parse":
  - `"check:diagram-lint": "node scripts/check-diagram-lint.mjs"` (Pele ↔ fixture parity)
  - `"check:diagram-review": "node scripts/check-diagram-review.mjs"`

### Data formats
- **`config.yaml`:** `diagrams: { strict: true }`. Absent means off. This was decided in the spec: warnings by default keep the tool low-friction (G-5).
- **Write response:** `{ …existing…, "diagram_warnings": [{ "file": "FEAT-012 spec", "block": 1, "line": 14, "rule": "semicolon_in_text", "message": "`;` ends the statement early — use a comma or words" }] }`. The key is present only when non-empty. A batch puts the same key on each op entry in `results`.
- **`GET …/features/{code}/diagrams`:** `{ "code", "blocks": [DiagramBlock], "findings": [DiagramFinding] }`.
- **Fixture `api/crates/kanbanr-core/src/testdata/diagram_lint_cases.json`:** `{ "_about": "...", "cases": [{ "name", "source", "rule": "<rule>" | null, "line": <block line> | null }] }`. It holds at least the cases in the probe table above, about 40.

### Lint algorithm
**Block extraction (`blocks`)**
- Scan lines while tracking an open fence: a line indented 0–3 spaces that starts with 3 or more backticks or tildes.
- A fence whose info string's first word is `mermaid` opens a block. The block closes at a line of the same character with run length at least the opener's. An unclosed fence runs to EOF.
- A mermaid fence inside any other open fence is content, not a block. For example, a four-backtick ````markdown fence containing ```mermaid` is not linted.
- `line` is the fence line + 1.

**Preamble and type (`lint_source`)**
- Skip blank lines, lines starting with `%%`, and a leading `---`…`---` block.
- No line left gives `empty_block` (line 1).
- Otherwise the first remaining line, after `trim_start`, must start with a Pele prefix. The match is case-sensitive, and the list is ordered so that `flowchart-elk` is tested before `flowchart`. A mismatch gives `unknown_type` at that line, and the block is not checked further. The prefixes are:
  - `sequenceDiagram`, `flowchart-elk`, `flowchart`, `graph`, `classDiagram`, `stateDiagram`, `erDiagram`, `gantt`, `pie`, `journey`, `gitGraph`, `mindmap`, `timeline`, `quadrantChart`, `requirement`
  - `C4Context`, `C4Container`, `C4Component`, `C4Dynamic`, `C4Deployment`
  - `sankey`, `xychart`, `block`, `packet`, `kanban`, `architecture`, `radar-beta`, `treemap`, `info`, `venn-beta`, `agentflow-beta`, `usecase-beta`, `railroad-`, `treeView-beta`, `cynefin-beta`, `wardley-beta`, `swimlane-beta`, `ishikawa`, `eventmodeling`
- The kind is Flowchart (`flowchart*`, `graph`), Sequence, Class, State, or Other. Other gets no further rules.

**Flowchart**
- Split each line into statements at `;` only at bracket depth 0 and outside quotes. The header's text after the direction counts as statements.
- Skip statements starting with `classDef`, `class `, `style `, `linkStyle`, `click `, `direction `, or `%%`.
- A statement that is exactly `end` pops the subgraph stack. If the stack is empty, that is `unbalanced_block` ("`end` closes nothing").
- A statement starting with the word `subgraph` pushes (keyword, line). If its id is `end`, that is `end_as_id`. A `[title]` on it is checked as a label.
- Label scan, left to right:
  - **Edge text:** a ` -- ` or ` == ` that opens edge text is skipped up to the next arrow.
  - **Node shapes:** an opener is a char of `[ ( { >` directly preceded by `[A-Za-z0-9_]`. Match the longest opener: `(((`, `((`, `([`, `(`, `[[`, `[(`, `[/`, `[\`, `[`, `{{`, `{`, `>`. The closers are `)))`, `))`, `])`, `)`, `]]`, `)]`, `/]`|`\]`, `\]`|`/]`, `]`, `}}`, `}`, `]`.
  - **Quoted label:** if the next non-space char is `"`, find the closing `"`. If there is none, that is `unbalanced_label`. The text between the closing quote and the closer must be blank; otherwise it is `label_punctuation` (`"`).
  - **Unquoted label:** find the first occurrence of the closer. If there is none in the statement, that is `unbalanced_label`. Any of `" | { } ( ) [ ]` in the label is `label_punctuation`, naming the first such character.
  - **Edge labels:** a `|` at depth 0 opens an edge label. The same quoted/unquoted logic applies with closer `|`, and the forbidden chars are `" { } ( ) [ ]`.
- `end_as_id`: any word `end` (bounded by non-`[A-Za-z0-9_]`) outside labels and edge text, in a statement that is not exactly `end`.
- At the end of the block, every open subgraph gives `unbalanced_block` at its opener's line.

**Sequence**, for each significant line:
- **Block keywords:** first word in {alt, loop, opt, par, critical, break, rect, box} pushes. `else`, `and` and `option` need the top of the stack to be `alt`, `par` and `critical` respectively; otherwise `unbalanced_block`. `end` pops; an empty stack gives `unbalanced_block`.
- **Participants:** `[create ]participant|actor <id>[ as alias]`. An id of `end` gives `end_as_id`. A `;` followed by a non-space anywhere gives `semicolon_in_text`.
- **Accepted as is:** `destroy`, `activate`, `deactivate`, `autonumber`, `title`, `accTitle`, `accDescr`, `link`, `links`, `properties`, `details`.
- **Notes:** first word `note` (any case) followed by `left of|right of|over …:` text. A `;` followed by a non-space in the text gives `semicolon_in_text`.
- **Messages:** find the earliest arrow, longest first at each position, from `<<-->>`, `<<->>`, `-->>`, `->>`, `-->`, `->`, `--x`, `-x`, `--)`, `-)`. Then an optional `+`/`-`, the target id up to `:`, then the text.
  - A missing `:` gives `unknown_statement`.
  - A from or to id of `end` gives `end_as_id`.
  - A `;` followed by a non-space in the text gives `semicolon_in_text`.
- **Anything else:** `unknown_statement`.
- At the end of the block, every unclosed opener gives `unbalanced_block` at its line.

**Class and state**
- Track `{`/`}` depth outside quotes. An unclosed `{` gives `unbalanced_block` at the opener's line; a stray `}` gives `unbalanced_block`.
- Class only: on a relation line at depth 0 that contains ` : `, a `;` followed by a non-space in the label gives `semicolon_in_text`.

**Failure handling.** The lint never fails: it is a total function over `&str`.
- An unreadable doc is skipped in the gate, the route and doctor.
- Strict mode refuses before any mutation; a batch is all-or-nothing, as it already is (FEAT-093).
- The monitor fails closed: Approve stays disabled while the check is loading or has failed.

### Performance budget and security
- **Cost:** one pass per line, linear in bytes. A closer search resumes after the closer, so there is no quadratic case.
- **Budget:** no more than 1 ms per 100 KB of markdown in release. The test (`lint_is_linear`) is 2 MiB with 1,000 blocks in under 1 s in debug.
- **Per write:** the lint runs only over the text being written.
- **Per move:** the spec, plus the k `affects_docs` files read from disk.
- **Readiness views:** a `diagrams_valid` gate makes `load_for_gates` load specs, as `spec_sections` already does.
- **Dependencies:** none new in Rust. On the web, Pele is already pinned at 1.7.0 and loaded lazily.
- **Untrusted input:** the lint works on untrusted text without regex (no ReDoS) and without recursion, and findings are capped at 50 per file.
- **Doc paths:** keys with `..` or an absolute path are skipped, and the route reads through `store.read_doc`.
- **New route:** a GET returning text already readable through the doc and feature routes.
- **Monitor rendering:** errors are set as text, never HTML. The review page calls Pele's `parse`, not `render`, so no SVG is produced there.

### Requirements (EARS)
- **R-1** WHEN a spec or markdown doc is written (feature add/edit, doc add, batch feature.add/feature.edit/doc.write), THE SYSTEM SHALL lint every fenced mermaid block and report each finding with file, block number, file line, rule and message.
- **R-2** WHILE `diagrams.strict` is off (the default), THE SYSTEM SHALL complete the write and return findings as `diagram_warnings`, which the CLI prints on stderr.
- **R-3** WHILE `diagrams.strict` is on, IF the written text has a finding, THE SYSTEM SHALL refuse the write, change nothing (for a batch, nothing at all), and name each finding.
- **R-4** THE SYSTEM SHALL report an empty block (`empty_block`) and a first significant line naming no diagram type Pele knows (`unknown_type`).
- **R-5** THE SYSTEM SHALL report a `;` followed by more text inside a sequence message, note or participant alias, or a class relation label (`semicolon_in_text`).
- **R-6** THE SYSTEM SHALL report an unquoted flowchart node, subgraph or edge label containing `" | { } ( ) [ ]` (`label_punctuation`), and a label or quote that is never closed (`unbalanced_label`).
- **R-7** THE SYSTEM SHALL report `end` used as a flowchart node id, a subgraph id, or a sequence participant (`end_as_id`).
- **R-8** THE SYSTEM SHALL report unbalanced subgraph/alt/loop/opt/par/critical/break/rect/box … `end`, misplaced `else`/`and`/`option`, and unbalanced `{}` in state and class diagrams (`unbalanced_block`).
- **R-9** THE SYSTEM SHALL report a sequence-diagram line that does not declare or use a participant and is not a note, block keyword or directive (`unknown_statement`).
- **R-10** THE SYSTEM SHALL flag no fixture case that Pele 1.7.0 parses, and Pele SHALL reject every fixture case that names a rule.
- **R-11** WHEN `kanbanr doctor` runs, THE SYSTEM SHALL list every lint finding in every item's spec and every markdown doc on the board, each naming file, block, line and rule.
- **R-12** THE SYSTEM SHALL accept `diagrams_valid` in any gate's `requires` or `warns` (`process check`, workflow save) and list it with its meaning in `process checks`.
- **R-13** WHEN an item moves into a status whose gate requires `diagrams_valid`, THE SYSTEM SHALL lint its spec and each `affects_docs` doc at that moment and, IF any finding exists, refuse the move naming file, block, line and rule for each.
- **R-14** WHEN the review page shows an item, THE SYSTEM SHALL parse every block of its spec and `affects_docs` with Pele, list each error with file, block, line and a link to the source, and keep Approve/Ratify disabled until all parse.
- **R-15** WHEN a diagram in rendered markdown fails to parse, THE SYSTEM SHALL show its source and the error with its line under it.
- **R-16** (performance efficiency: time behaviour) THE SYSTEM SHALL lint 2 MiB of markdown holding 1,000 blocks within 1 s in a debug build.
- **R-17** THE SYSTEM SHALL set strict mode with `kanbanr config diagrams --strict on|off`. An absent key is off and stays absent on disk.
- **R-18** THE SYSTEM SHALL carry diagram guidance in the skill: quote flowchart labels; keep sequence messages to plain words; never use `end` as an id; run `kanbanr doctor` after writing diagrams.

### Test plan
| Req | Tests |
|---|---|
| R-1 | `diagrams::tests::extracts_mermaid_blocks_with_file_lines`, `diagrams::tests::ignores_mermaid_inside_other_fences`, `dispatch::tests::write_reports_diagram_warnings` |
| R-2 | `dispatch::tests::write_reports_diagram_warnings` (file written), `local_mode::cli_feature_add_prints_diagram_warning` |
| R-3 | `store::tests::strict_diagrams_refuse_the_write`, `store::tests::strict_diagrams_refuse_the_whole_batch` |
| R-4–R-9 | `diagrams::tests::lint_cases_fixture`, plus one focused test per rule: `empty_and_unknown_type`, `semicolon_in_text`, `flowchart_label_punctuation`, `end_is_never_an_id`, `blocks_are_balanced`, `sequence_lines_are_statements` |
| R-10 | web `check:diagram-lint` (`scripts/check-diagram-lint.mjs`), `diagrams::tests::lint_cases_fixture` |
| R-11 | `doctor::tests::doctor_lists_diagram_findings` |
| R-12 | `readiness::tests::diagrams_valid_in_vocabulary`, `readiness::tests::the_guides_check_table_matches_process_checks` (existing), `local_mode::cli_process_check_accepts_diagrams_valid` |
| R-13 | `readiness::tests::diagrams_valid_gate_blocks_and_names_findings` (spec and affects_docs cases; fixing them unblocks immediately) |
| R-14 | web `check:diagram-review` (`scripts/check-diagram-review.mjs`: `checkBlocks`, `locateError`, `approveBlocker`), `check:api-types` (existing), `contract_matches_openapi` (existing); manual: open Review with an item whose spec has a broken diagram, confirm Approve is disabled, the error is listed with a link, and fixing the spec re-enables Approve on the live tick |
| R-15 | `check:diagram-review` (`locateError` cases), `check:markdown` (existing, still passes) |
| R-16 | `diagrams::tests::lint_is_linear` |
| R-17 | `config::tests::diagrams_config_defaults_off_and_round_trips`, `local_mode::cli_config_diagrams_strict_toggles` |
| R-18 | `skill::tests::skill_carries_diagram_guidance` (kanbanr-cli/src/skill.rs: the embedded SKILL.md contains `### Diagrams` and `diagrams_valid`) |

### Affects docs
- `docs/src/using/processes.md`: a new `diagrams_valid` row in "### The checks", whose text must equal `passes_when`, and a short example of requiring it on every gate.
- `docs/src/using/documentation.md`: in "Diagrams & images in docs", describe the lint on write, strict mode, the rules, quoting advice, and that Pele is authoritative.
- `docs/src/using/the-monitor.md`: in "What the monitor shows", the review page's diagram check and the doc viewer's error under a diagram.
- `docs/src/reference/cli.md`: a `kanbanr config diagrams [--strict on|off]` row, and the `doctor` row gains "diagram problems".
- `docs/src/reference/http-api.md`: the generated table, regenerated by the openapi example, plus `docs/src/reference/openapi.json`.
- `docs/src/project/changelog.md`: an entry under [Unreleased] › Added.
- `skill/kanbanr/SKILL.md`: a new `### Diagrams` subsection after "### The design stage…", and one line in "## Every change points back at the reason for it" naming `diagrams_valid` and `kanbanr doctor`.

### Open questions
- **Q-1. Should the review page's parse result be recorded and fed into `diagrams_valid`, as the spec's item 4 says?**
  - Recommended: no.
  - The gate uses the core lint, computed at move time, which is what the 2026-10-20 addendum requires ("not cached").
  - Recording would need a new write route from a monitor that is read-only by default, and it would cache a result.
  - The parity fixture (R-10) keeps the lint inside Pele's rejections, and the review page blocks Approve on whatever the lint misses.
- **Q-2. Drop the filed rules that Pele accepts?** These are an unquoted flowchart label containing `;`, and JSON, quotes or braces in sequence messages.
  - Recommended: drop them from the lint, because a finding Pele contradicts would block a gate on a diagram that draws fine.
  - Keep them as skill advice instead. GitHub's own Mermaid still rejects `A[x; y]`, so quoting labels stays the advice.

### Decisions (21 Oct 2026, by the user: the drafted design with its recommended answers)
- Q-1: the review page's parse result is not recorded; `diagrams_valid` uses the core lint, computed at move time.
- Q-2: the lint follows Pele 1.7.0. The filed rules Pele accepts (a `;` in an unquoted flowchart label; JSON, quotes or braces in sequence messages) are dropped from the lint and kept as skill advice.
- Built after [FEAT-176](/p/kanbanr/feature/FEAT-176) is merged.

### Implementation tasks
1. **Core lint.** Depends on: none.
   - Create `api/crates/kanbanr-core/src/diagrams.rs` with `DiagramBlock`, `LintRule`, `DiagramFinding` (+`describe`), `is_markdown_path`, `blocks`, `lint_source`, `lint_markdown` and `MAX_FINDINGS_PER_FILE`, exactly as in the algorithm above. Register it in `lib.rs`.
   - Create `src/testdata/diagram_lint_cases.json` with every case from the probe table.
   - Tests: `extracts_mermaid_blocks_with_file_lines`, `ignores_mermaid_inside_other_fences` (R-1); `lint_cases_fixture` (include_str, asserting the rule and line of the first finding, or none) and the six per-rule tests (R-4–R-9); `lint_is_linear` (R-16).
2. **Config, error and strict guard.** Depends on: 1.
   - `config.rs`: `DiagramsConfig` and `ProjectConfig.diagrams`. Fix any struct literals the compiler flags.
   - `error.rs`: `InvalidDiagram`. `kanbanr-server/src/routes.rs`: map it to 400.
   - `diagrams.rs`: `guard`.
   - `store.rs`: `read_project_config`, `set_diagrams`.
   - `dispatch.rs`: GET and PUT `config/diagrams`.
   - CLI: `ConfigCmd::Diagrams`.
   - Tests: `config::tests::diagrams_config_defaults_off_and_round_trips`, `local_mode::cli_config_diagrams_strict_toggles` (R-17).
3. **Write-path hooks.** Depends on: 2.
   - Call `guard` in `add_feature_on` and `edit_feature_on`, and in the batch `DocWrite`.
   - Add `diagram_warnings` to the batch op results, plus `with_diagram_warnings` on POST/PATCH features and PUT docs/content (guard first for docs).
   - CLI: `print_diagram_warnings`, called in the feature add/edit, doc add and batch handlers.
   - Tests: `dispatch::tests::write_reports_diagram_warnings` (R-1, R-2); `store::tests::strict_diagrams_refuse_the_write`, `strict_diagrams_refuse_the_whole_batch` (R-3); `local_mode::cli_feature_add_prints_diagram_warning` (R-2).
4. **Gate check.** Depends on: 1.
   - `diagrams::item_findings`.
   - `readiness.rs`: `Check::DiagramsValid`, `GATEABLE` (19), `passes_when`, `reads_spec`, `evaluate_in`, `diagram_gaps`, `reads_definition` exclusion, `item_level` arm.
   - Add the table row in `docs/src/using/processes.md`.
   - Tests: `diagrams_valid_in_vocabulary`, `the_guides_check_table_matches_process_checks`, `local_mode::cli_process_check_accepts_diagrams_valid` (R-12); `diagrams_valid_gate_blocks_and_names_findings`, which uses a charter-adopted board and a gate `requires: [diagrams_valid]`. The move is refused; the message contains `"FEAT-… spec, diagram #1, line 3"` and `semicolon_in_text`; after the spec is edited the move succeeds; then the same again for a doc in `affects_docs` (R-13).
5. **Doctor.** Depends on: 1.
   - `scan_diagrams` in `run` and `run_project`.
   - Test: `doctor_lists_diagram_findings` (R-11).
6. **Review route.** Depends on: 4.
   - `ItemDiagrams` + `load`, and the dispatch GET route.
   - The `openapi.rs` RouteDoc. Regenerate `openapi.json` and the http-api table.
   - Test: `contract_matches_openapi` (R-14).
7. **Monitor.** Depends on: 6.
   - `types.ts`, `api.ts` (`getItemDiagrams`), new `diagramCheck.ts`.
   - `ReviewPage.tsx` `Brief`: the Diagrams list and the Approve gating.
   - `Markdown.tsx`: the error shown under the diagram. `styles.css`.
   - `scripts/check-diagram-review.mjs`, the `package.json` script, the `ci.yml` step.
   - Tests: `check:diagram-review` (R-14, R-15), `check:api-types`, `check:read-only`, `check:markdown`, and the one manual check.
8. **Parity check.** Depends on: 1.
   - `web/scripts/check-diagram-lint.mjs`: reads the fixture, then asserts that `parse` throws exactly when `rule != null`. It fails when it finds zero cases.
   - The `package.json` script `check:diagram-lint` and a `ci.yml` step.
   - Test: R-10.
9. **Docs and skill.** Depends on: 2–7.
   - Update every page listed under Affects docs, the SKILL.md sections and the changelog.
   - Test: `skill::tests::skill_carries_diagram_guidance` (R-18). `npm run check:docs` must still pass.
