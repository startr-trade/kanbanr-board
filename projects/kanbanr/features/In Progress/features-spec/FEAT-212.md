# Release stages that act: move main, then tag it

## Why
On 21 Oct 2026 the user set out the release flow they want: the release is merged into main and
pushed, CI runs on that commit, and only then is it tagged. Today the last stage of a release does
both at once: it tags the release tip and fast-forwards main to it, so the tag exists before CI has
seen the commit, and the release workflow then refuses the tag.

The user's request: a release stage should be like an item stage, a status the release enters with
guard rules (as gates are), whose entry does one thing. Entering a stage can merge the release into
main; the final stage (the cut) tags main. Pushing code and tags stays the user's, by hand.

## What it adds (to be designed)
- Release stages declared with conditions and an action, as item gates are, for example:
  - candidate: make `release/<V>` from the line of integration;
  - main: fast-forward main to the release (refused if main has commits the release lacks);
  - production (the cut): tag main, which must be at the release tip and on `origin/main`.
- The Releases page and `release promote` say what each stage will do and what it still needs
  ("push main, then wait for CI").
- The default stages keep today's behaviour.
- **The release prepares itself** (the user, 21 Oct 2026, approving FEAT-211): a release is not
  prepared by a separate feature item made for the purpose. Its own state change does it: for
  example, entering the first stage commits the version bump, the changelog heading and a notes
  draft (from its items) onto `release/<V>`, which kanbanr may write although people may not.
  FEAT-207 and FEAT-211 are the redundancy this removes.

- **One click to cut** (the user, 21 Oct 2026, cutting 0.2.1): today "Promote to production (cut)"
  opens a second panel with a "Cut \<V\>" button. The cut's button should say what it does ("Cut
  v0.2.1") and show its preview (the commit it will tag, what ships and what carries over) beside
  it, so one click cuts. The stage's conditions (main at the release tip, on `origin/main`) are what
  keep it safe: the button is offered only once they hold, and says what is missing until then.

## As lived with 0.2.1 (21 Oct 2026)
Stages `candidate, production`. Promote to candidate made `release/v0.2.1` from `sprint/SP-001`;
main was fast-forwarded to it by hand; the user pushed main and CI went green; the cut tagged
`0685a5b`, which main already was; the user pushed the tag and the release ran green. The manual
fast-forward, the separate release-prep item (FEAT-211) and the second confirmation click are what
this item removes.

## Design

### 0. What exists today (verified)
- `api/crates/kanbanr-core/src/releases.rs` `promote(store, id, version, to, by, reason, repo)`:
  - Every forward move makes `release/<V>` when the release has no branch yet. The base comes from `gitmodel::release_base` when the git model is on, otherwise from `integration_branch` or `coderepo::default_branch`.
  - The last stage calls `promote_to_production`. Its preflight checks, in order: `cut_preview`, `is_clean(repo)`, the branch exists, the tag does not exist, main exists, and `is_ancestor(main, branch)` (patch exception, FEAT-184).
  - It then runs `create_tag`, then `fast_forward`, then `cut_with`. On failure it calls `reset_branch_to` and `delete_tag`, and wraps the error with `rolled_back` ("…put back as it was").
- `config.rs`: `Cadence { release_stages: Vec<String>, integration_branch, main_branch, git_model, extra }`. Also `Cadence::stages()` (default `DEFAULT_RELEASE_STAGES`) and `Cadence::validate_stages`.
- Item gates are `ProjectConfig.gates: BTreeMap<String, Gate>`, keyed by status, with `requires: Vec<readiness::Condition>` and `on_enter: Vec<Action>`. `Condition`'s hand-written `Deserialize` names the valid checks when one is misspelt (FEAT-168).
- `coderepo.rs`: `run()` refuses `push`. `merge_no_ff` already writes a commit with `commit-tree` + `update-ref` without checking anything out. The code repo's hooks therefore never see kanbanr's own commits.
- `gitmodel::line_commit_verdict` refuses non-merge commits on `release/*` from people. `gitdrift` skips line commits that carry no `Refs` (`[no-ref]` escapes and generated commits).
- `dispatch.rs`: `POST …/releases/{v}/promote`, `GET …/releases/{v}/cut-preview`, and `PUT …/config/cadence`. The cadence route reads `release_stages` through `vec_field`, which handles strings only.
- The daemon passes its repo only on writes (`routes.rs` `run_write`). `read_passthrough` calls `dispatch` without one. FEAT-213 task 2 is adding the repo for git reads.
- kanbanr's own cadence is `release_stages: [candidate, production]` with `git_model: true`.
- The release workflow (`.github/workflows/release.yml`) refuses a tag unless `[workspace.package]` version, `editor/vscode/package.json`, and `docs/src/releases/<tag>.md` all agree with it.
- `docs.yml` fails when a `.md` file is not listed in `SUMMARY.md`. CI also runs `tools/docs/sync.sh` (`CHANGELOG.md` → `docs/src/project/changelog.md`) and fails on a difference.

### 1. Config format

**Decision: stage names stay a list of strings, and the rules go in a separate map, like item `gates`.** You suggested string-or-map entries inside `release_stages`. An older binary deserialises `Cadence.release_stages: Vec<String>`, so a map entry would fail to parse the whole project config. That is a hard break, not something `extra` can absorb. A new key under `cadence` lands in `Cadence.extra` in older binaries (FEAT-151) and survives their writes. This shape also mirrors `statuses` + `gates`, keeps FEAT-213's "stages by name" display unchanged, and leaves the CLI `--release-stages a,b` and `vec_field` untouched.

```yaml
cadence:
  release_stages: [candidate, main, production]   # unchanged: names only; the last is the cut
  release_gates:                                  # NEW, optional, keyed by stage name
    candidate: { on_enter: [branch, prepare] }
    main:      { purpose: "main holds the release; push it and let CI run", requires: [items_finished], on_enter: [move_main] }
    production: { requires: [main_at_release, pushed], on_enter: [tag] }
  release_prepare:                                # NEW, optional; empty by default
    version_files:
      - path: api/Cargo.toml                      # default match for *.toml: ^version = "{version}" (first)
      - path: api/Cargo.lock
        match: "name = \"kanbanr-core\"\nversion = \"{version}\""   # explicit match: every occurrence
      - path: editor/vscode/package.json          # default for *.json: "version": "{version}" (first)
      - path: web/package.json
      - path: .claude-plugin/plugin.json
    changelog: CHANGELOG.md
    changelog_copies: [docs/src/project/changelog.md]
    notes: docs/src/releases/{version}.md
    notes_listings:
      - { path: docs/src/SUMMARY.md, after: "- [Release notes](releases/index.md)", entry: "  - [{number}](releases/{version}.md)" }
```
The example above is kanbanr's own config. The Cargo.lock entry is repeated for `kanbanr-cli` and `kanbanr-server`, and the lockfile entries should be confirmed when it is configured.

**Types** (new `api/crates/kanbanr-core/src/releasegates.rs`, all `#[cfg_attr(feature="schema", derive(schemars::JsonSchema))]`, each struct with a flattened `extra: Extra`):
- `enum ReleaseAction { Branch, Prepare, MoveMain, Tag }`, snake_case. The derived `Ord` is the apply order.
- `enum ReleaseCheck { ItemsFinished, Prepared, MainAtRelease, Pushed }`. Its hand-written `Deserialize` names the valid ones, as `Condition` does.
- `struct ReleaseGate { purpose: String, requires: Vec<ReleaseCheck>, on_enter: Vec<ReleaseAction> }`.
- `struct ReleasePrepare { version_files: Vec<VersionFile>, changelog: Option<String>, changelog_copies: Vec<String>, notes: Option<String>, notes_listings: Vec<NotesListing> }`.
- `struct VersionFile { path: String, #[serde(rename="match")] pattern: Option<String> }`.
- `struct NotesListing { path, after, entry }`.
- `Cadence` gains `release_gates: BTreeMap<String, ReleaseGate>` and `release_prepare: ReleasePrepare`, both `skip_serializing_if` empty. Nothing is written for boards that do not use them.

**Actions:**

| action | does | allowed |
|---|---|---|
| `branch` | makes `release/<V>` from `gitmodel::release_base` (or today's fallback), without checking it out. Idempotent: the branch is already recorded. Any forward move of a release with no branch includes it implicitly (today's rule). | any stage, at most once |
| `prepare` | one commit on `release/<V>`, nothing checked out: the version files, the dated changelog heading, the changelog copies, the notes draft, and the notes listings. Idempotent: no change means no commit. | at most once, not on a stage after the one holding `move_main` |
| `move_main` | fast-forwards main to the release tip. Refused if main has commits the release lacks. A patch of an older release leaves main where it is (FEAT-184). Idempotent if main is already there. | at most once, not after `tag` |
| `tag` | annotated tag `<V>` (as today, `"Release <V>"`) on the release tip | the last stage only |

**Conditions** (`requires`, each with a `passes_when` sentence and a fix):

| check | holds when | fix shown |
|---|---|---|
| `items_finished` | `cut_preview` carries nothing over | "FEAT-x carries over: \<why\>. Finish it, or plan it into another release" |
| `prepared` | at the release tip, every version file names `{number}`, the changelog has `## [{number}]`, and the notes file exists. Holds trivially when `release_prepare` is empty. | "promote to \<stage holding prepare\>" |
| `main_at_release` | `rev(main) == rev(release/<V>)`, or a patch whose main has moved on | "promote to \<stage with move_main\>", or "merge main into release/\<V\> first" plus the commits |
| `pushed` | the release tip is an ancestor of main's remote-tracking branch (`main@{upstream}`, else `origin/<main>`). For a patch left behind: any remote-tracking branch contains it (`git branch -r --contains`). | "push main (`git push origin main`), then wait for CI" |

**Rules:**
- Conditions are evaluated against the repository as it is before the move. A condition counts as met when an action of the same promotion makes it true: `prepare` makes `prepared` true, and `move_main` makes `main_at_release` true. `pushed` is never made true by a move. So skipping straight from candidate to production still refuses until main is pushed.
- A forward move runs the `on_enter` actions of every stage it passes through or enters, and checks the `requires` of all of them.
- A move back stays board-only and needs `--reason`, as today. Main is never moved back, because it may already be pushed.
- Promoting to the stage the release is already at re-applies that stage's actions ("again", recorded as a stage change with reason `again: <steps>`). It is allowed only when at least one step is not a no-op; otherwise it is refused as today ("already at").

**Defaults (`Cadence::effective_release_gates`), which reproduce today:**
- A stage without an entry gets:
  - the first stage: `[branch]`, unless some declared gate holds `branch`;
  - the last stage: `[move_main, tag]`, with `move_main` dropped if some declared gate holds it;
  - a single stage: `[branch, move_main, tag]`;
  - middle stages: nothing.
- No synthesised `requires`. The last stage is always the board cut (`cut_with`), whatever its actions.
- **Intrinsic preconditions** (not configurable; these are today's preflight messages kept word for word):
  - `move_main`: `is_clean(repo)`, main exists, main is an ancestor of the release (unless a patch).
  - `tag`: the tag does not exist; the release branch exists. If this promotion or an earlier stage has `move_main` and the release is not a patch left behind, main must be at the tip after this move's steps.
  - `prepare`: `release/<V>` is not checked out in any worktree; the files exist and their match patterns hit.
  - Every git step needs a repo (`needs_repo`).

**Validation** (`Cadence::validate_release_gates() -> Result<(), String>`). It runs in `Store::set_cadence`, in the new routes, and in doctor (for hand edits). Refusals:
- a key that is not a stage;
- an action placed twice across stages, or `tag` before the last stage;
- `move_main` after `tag`'s stage, or `prepare` after `move_main`'s stage;
- an unknown check or action (at parse time);
- a version-file or notes path that is absolute, contains `..`, or starts `.git/`;
- a `match` without exactly one `{version}`;
- `notes` without `{version}` or `{number}`.

Renaming or removing a stage that has a gate is refused, naming `kanbanr config release-stage <S> --clear`. A `prepare` with nothing configured is allowed: it is a reported no-op.

**Placeholders:** `{version}` is the release version verbatim (`v0.2.1`). `{number}` is the version with one leading `v` removed when a digit follows (`0.2.1`); it is what the files get, and it must match `[0-9A-Za-z.+-]+`. `{name}` is the release name, `{date}` is `YYYY-MM-DD` (`sprints::today`).

**Match templates** (no regex dependency):
- The template is literal text with exactly one `{version}`, which matches `[0-9A-Za-z.+-]+`.
- Every run of whitespace in the template matches any run of zero or more whitespace characters, newlines included.
- A leading `^` anchors to the start of a line (leading spaces allowed).
- An explicit `match` replaces every occurrence. The built-in default replaces the first.
- Built-in defaults: `*.toml` → `^version = "{version}"`; `*.json` → `"version": "{version}"`. Any other file needs `match`.
- No hit means a refusal that names the file.

**When `version_files` is empty:** `prepare` bumps no version, and the plan says "no version files configured: `kanbanr config release-prepare --version-file <path>`". It still dates the changelog and drafts the notes if those are set. If nothing at all is configured, `prepare` is a no-op the plan names, and no empty commit is ever made.

**Changelog:**
- Below the first `## [Unreleased]` line (case-insensitive), insert a blank line and `## [{number}] - {date}`. What was under Unreleased now belongs to the new heading.
- If there is a `[Unreleased]: <base>compare/<prev>...HEAD` link: rewrite it to `compare/{version}...HEAD` and add `[{number}]: <base>compare/<prev>...{version}` below it.
- If `## [{number}]` is already present: no-op. If there is no Unreleased heading: skip, with a plan note (not a refusal).
- Each `changelog_copies` path gets the identical new content.

**Notes draft:** `releases::notes(release, parent, &shipping, &[])`, where `shipping` is the items `cut_preview` marks `ships`. It is written only if the file is absent at the tip, so a hand-written page is kept and the plan says so. Each `notes_listings` entry inserts the expanded `entry` directly below the first line equal (trimmed) to `after`. If the entry is already there: no-op. If `after` is not found: refused.

### 2. Core changes (signatures)

`releaseprep.rs` (pure, unit-tested):
```rust
pub struct Placeholders { pub version: String, pub number: String, pub name: String, pub date: String }
pub fn number_of(version: &str) -> Result<String, String>;
pub fn expand(template: &str, p: &Placeholders) -> String;
pub fn check_repo_path(path: &str) -> Result<(), String>;
pub fn set_version(text: &str, path: &str, pattern: Option<&str>, number: &str) -> Result<String, String>;
pub fn date_changelog(text: &str, p: &Placeholders) -> Result<Option<String>, String>; // None: already / no Unreleased (note)
pub fn add_listing(text: &str, after: &str, entry: &str) -> Result<Option<String>, String>;
pub fn names_version(text: &str, path: &str, pattern: Option<&str>, number: &str) -> bool; // for `prepared`
```

`coderepo.rs` additions (nothing pushes; `run` keeps its push refusal):
```rust
fn run_with(root: &Path, args: &[&str], stdin: Option<&[u8]>, env: &[(&str, &str)]) -> Result<Output>;
pub fn read_blob(root: &Path, rev: &str, path: &str) -> Result<Option<(String /*mode*/, String)>>; // ls-tree + cat-file
pub fn commit_files(root: &Path, branch: &str, files: &[(String, String)], message: &str) -> Result<(String, String)>;
pub fn undo_commit(root: &Path, branch: &str, old: &str, new: &str) -> Result<()>; // update-ref refs/heads/<b> old new
pub fn upstream_of(root: &Path, branch: &str) -> Option<String>; // rev-parse --abbrev-ref <b>@{upstream}, else origin/<b> if it exists
pub fn remote_of(root: &Path, branch: &str) -> String;            // branch.<b>.remote, else "origin"
pub fn fetch_branch(root: &Path, remote: &str, branch: &str) -> Result<()>;
pub fn remote_branches_containing(root: &Path, commit: &str) -> Result<Vec<String>>;
```
- `commit_files` refuses if the branch is checked out in a worktree (`checked_out_in`). It uses a temporary index at `git rev-parse --git-path kanbanr-prepare.index`, removed afterwards on every path. The sequence is `read-tree <tip>` → `hash-object -w --stdin` per file → `update-index --add --cacheinfo <mode>,<blob>,<path>` (mode kept, `100644` for new files) → `write-tree` → `commit-tree <tree> -p <tip> -m <msg>` (the user's identity and signing config) → `update-ref refs/heads/<b> <new> <tip>`.
- `fetch_branch` runs `git fetch --quiet --no-tags <remote> <branch>` with `GIT_TERMINAL_PROMPT=0`, `GIT_HTTP_LOW_SPEED_LIMIT=1000`, `GIT_HTTP_LOW_SPEED_TIME=10`, and `GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=10"` only when that variable is not already set.

**Prepare commit identity and trailers.** Author and committer are the person's git identity, as for `merge_no_ff`. The message:
```
Release v0.2.1: version, changelog and notes

Prepared by `kanbanr release promote v0.2.1 candidate`: <files, one per line>.
Draft notes from FEAT-209, FEAT-210.

[no-ref] release preparation, made by kanbanr
Kanbanr-Release: v0.2.1
```
- There are no `Refs` lines, so `gitdrift`'s unfinished-item rule never fires.
- `[no-ref]` satisfies `scm::escape_reason`.
- People's commits on `release/*` stay refused by the hooks. kanbanr's plumbing commit never runs hooks, which is the "kanbanr may, people may not" rule.

`releases.rs`:
```rust
pub enum Fetch { No, Try }
#[derive(Serialize, JsonSchema)] pub struct PlanCondition { pub check: ReleaseCheck, pub stage: String, pub holds: bool, pub detail: String, #[skip_if_empty] pub fix: String }
#[derive(Serialize, JsonSchema)] pub struct PlanStep { pub action: ReleaseAction, pub stage: String, pub does: String, pub noop: bool, #[skip_if_none] pub blocked: Option<String> }
#[derive(Serialize, JsonSchema)] pub struct OriginState { pub tracking: String, pub fetched: bool, #[skip_if_empty] pub fetch_error: String }
#[derive(Serialize, JsonSchema)] pub struct ReleasePlan {
  pub version: String, pub from: String, pub to: String,
  pub direction: String /* forward | back | again */, pub cut: bool,
  pub button: String /* "Promote to main" | "Cut v0.2.1" | "Promote to main again" */,
  pub conditions: Vec<PlanCondition>, pub steps: Vec<PlanStep>,
  pub preview: Vec<CutPreview> /* cut only */, pub tag_commit: Option<CommitLine>,
  pub release_tip: String, pub missing: Vec<String>, pub ready: bool, pub needs_reason: bool,
  pub origin: Option<OriginState>, pub after: String /* e.g. "push main, wait for CI, then Cut v0.2.1" */,
}
pub fn plan(store: &Store, id: &str, version: &str, to: Option<&str>, reason: &str, repo: Option<&Path>, fetch: Fetch) -> Result<ReleasePlan>;
pub struct PromoteOptions<'a> { pub expect_tip: Option<&'a str>, pub fetch: Fetch }
pub fn promote_with(store, id, version, to, by, reason, repo, opts: PromoteOptions) -> Result<Promoted>;
pub fn promote(...same as today...) -> Result<Promoted> // = promote_with(.., {expect_tip: None, fetch: Fetch::Try})
```
- `Promoted` gains `#[skip_if_empty]` fields: `steps: Vec<PlanStep>` (what was done), `prepared: Option<Prepared { sha, files: Vec<String>, notes: String }>`, `main_moved: Option<(String, String)>`, `next: String`, `origin: Option<OriginState>`.
- Existing fields (`branch_created`, `tagged`, `main_branch`, `preview`, `notes`, `forward_merge`, `forward_into`) keep their meaning. `main_branch` is now set whenever main moved, at any stage.

**Apply (`promote_with`):**
1. `plan(…, Fetch::Try)`. A fetch happens only if a `pushed` condition is among the checked stages, and a failed fetch is recorded in `origin.fetch_error`. Refuse unless `ready`, joining `missing` with the fix sentences ("…: nothing was changed").
2. If `expect_tip` is given and differs from `release_tip`, refuse: "release/\<V\> moved since the plan you saw (now \<sha7\>): look again".
3. Apply the git steps in `ReleaseAction` order and push each onto `Vec<Undo>`, where `enum Undo { DeleteBranch(String), UndoCommit{branch, old, new}, ResetMain{branch, to}, DeleteTag(String) }`.
4. Board: for the cut, save the `branch` record first (as today), then `cut_with(store, id, version, Some(change))`. Otherwise push the `StageChange` and `save`.
5. On any failure after a step: undo in reverse. Restore `original` releases if the branch record was saved. Return `rolled_back(e, first_undo_error)`, so the messages are unchanged.
6. `next`: `plan(…, next stage, Fetch::No)` gives "next: `kanbanr release promote <V>` (\<button\>)" when ready, else "next: \<first missing fix\>, then \<button\>". After a tag: "push the tag: `git push origin <V>`".

**Other changes in `releases.rs`:**
- The forward-merge list (`commits_between(integration, branch)`) is reported for every release whose main moved or that was tagged, not only patches. It is appended to the notes doc only for patches, as today.
- `add_patch` runs the first stage's effective actions other than `branch` (that is, `prepare`) through the same apply engine, with the branch made from `refs/tags/<parent>`, and undoes them if the board save fails.
- `promote_to_production` is folded into the step functions `step_move_main` and `step_tag`, with the preflight messages kept verbatim.

### 3. Store, routes, daemon, CLI
- **Store:**
  - `Store::set_cadence` also runs `validate_release_gates` on the new stage list.
  - New `Store::set_release_gate(id, stage, Option<ReleaseGate>) -> Result<ProjectConfig>` (`None` clears).
  - New `Store::set_release_prepare(id, ReleasePrepare) -> Result<ProjectConfig>`.
- **Dispatch:**
  - `PUT …/config/cadence` copies `release_gates` and `release_prepare` from `current` (the struct literal must name them).
  - New routes:
    - `GET /projects/{p}/releases/{v}/plan?stage=&fetch=1`. `fetch=1` is honoured only by the CLI's `--plan --fetch`; the monitor never sends it.
    - `GET /projects/{p}/release-stages` returns `[{name, purpose, requires, on_enter, cut, declared}]` from the effective gates.
    - `PUT /projects/{p}/config/release-stages/{stage}` with body `{purpose?, requires?, on_enter?, clear?}`.
    - `PUT /projects/{p}/config/release-prepare` with body `{version_files?, changelog?, changelog_copies?, notes?, notes_listings?}` (`""` clears).
  - `POST …/promote` reads `expect`.
  - `openapi.rs` lists the plan route (`ReleasePlan`). Regenerate `docs/src/reference/openapi.json` with `cargo run -p kanbanr-core --features schema --example openapi`.
- **Daemon** (`api/crates/kanbanr-server/src/routes.rs`): extract `fn code_repo_for<'a>(st: &'a AppState, path: &str) -> Option<&'a Path>` from `run_write`. `read_passthrough` calls `dispatch::dispatch_in(…, code_repo_for(&st, dpath))` for its own project. This is the same change as FEAT-213 task 2: whichever item lands second reuses the helper. Fetch in the daemon happens only on POST promote when `pushed` is in play.
- **CLI** (`api/crates/kanbanr-cli/src/main.rs`):
  - `release promote <V> [STAGE] [--reason] [--by] [--plan [--fetch]]`. `--plan` prints the button, steps, conditions (✓/✗ with fixes) and preview, and changes nothing. It calls `client.get_in` with the repo.
  - After a promotion, `promote_release` prints each step's `does`, then `next:`. The "tagged …, main fast-forwarded" wording follows `main_moved` and `tagged` separately.
  - New `release stages` command (table of the effective gates).
  - New `config release-stage <STAGE> [--purpose] [--requires a,b] [--on-enter a,b] [--clear]`.
  - New `config release-prepare [--version-file PATH[=MATCH]]… [--clear-version-files] [--changelog PATH] [--changelog-copy PATH]… [--notes TEMPLATE] [--notes-listing PATH::AFTER::ENTRY]…`. `\n` in MATCH and ENTRY means a newline.
  - `release cut --tag` stays "promote to the last stage".

### 4. Releases page (`web/src/pages/ReleasesPage.tsx`)
- Remove the `confirming` state and the second panel.
- For each unshipped release with a next stage, fetch `api.getReleasePlan(project, version)`.
- A pure builder in new `web/src/releaseAction.ts`, `releaseAction(plan, writable) → { label, enabled, does: string[], preview?: {tag: string, ships: string[], carries: {code, why}[]}, missing: {text, fix}[] }`, decides what is shown.
- One button labelled `plan.button` ("Promote to candidate", "Promote to main", "Cut v0.2.1"). It is enabled only when `writable && plan.ready`.
- Beside the button: the step sentences ("makes release/v0.3.0 from sprint/SP-002", "commits the version 0.3.0, the changelog heading and draft notes to release/v0.3.0", "fast-forwards main to release/v0.3.0 (abc1234)", "tags abc1234 'Release …' v0.3.0").
- For the cut, the preview sits inline: the commit it will tag, "Ships: …", and the carry-overs. It comes from `plan.preview`; `CutPreviewList` takes it as a prop, and the `cut-preview` route stays for others.
- When not ready: "Needs:" and the missing list with fixes (e.g. "push main (`git push origin main`), then wait for CI"), plus a **Check again** button that refetches the plan (no network fetch, because `git push` updates `origin/main` locally).
- Clicking calls `api.promoteRelease(project, v, who, plan.to, plan.release_tip)`, which sends `expect`.
- When not writable: the CLI command and the same plan lines.
- When the daemon has no repo: the plan's repo-needing conditions read "the monitor was not started in the project folder", and the CLI command is shown.
- `types.ts`: `Cadence.release_gates?`, `release_prepare?`, `ReleasePlan`, `PlanCondition`, `PlanStep`. `release_stages?: string[]` is unchanged.

### 5. Compatibility and migration
- No schema bump (still 5) and no migration. A board with `release_stages: [names]` or none gets the effective gates of today.
- The new keys sit under `cadence` and are kept by older binaries via `Cadence.extra`. An older binary promoting such a board does today's thing (tag and fast-forward at the last stage) and ignores the gates. Release notes should say "use one version per board".
- The only output difference on default boards is an added `forward_merge` list for non-patch releases with commits the line lacks, which is report-only. Today's errors and refusals are byte-identical.

### 6. Security
- kanbanr writes only to the code repo it was given: the CLI's cwd repo, or the daemon's start folder for its own project only. What it writes there:
  - git objects;
  - `refs/heads/release/<V>` and `refs/heads/<main>`;
  - `refs/tags/<V>`;
  - remote-tracking refs (fetch);
  - a temporary index under `.git`.
- `prepare` never touches the working tree. Paths are validated against escape (`..`, absolute, `.git/`). Versions are restricted to `[0-9A-Za-z.+-]`.
- There is never a push: `coderepo::run`'s refusal applies to every new call, and `fetch` only reads the remote. No hosting API is used. Fetch is non-interactive with timeouts, and offline falls back to the last-fetched refs and says so.
- Read-only monitors (FEAT-178) never get a button.

### 7. Requirements (EARS) and tests
| R | EARS | Tests |
|---|---|---|
| R-1 | THE SYSTEM SHALL read each release stage's conditions and entry actions from `cadence.release_gates`, keyed by stage name, keeping `cadence.release_stages` a list of names. | `release_gates_read_beside_stage_names` (unit), `release_stage_routes_round_trip` (unit) |
| R-2 | IF a release gate names an unknown stage, check or action, or orders `prepare`, `move_main` and `tag` against the rules, THEN THE SYSTEM SHALL refuse the configuration and say why. | `release_gates_validated` (unit) |
| R-3 | WHILE a stage declares no gate, THE SYSTEM SHALL act as before: the first stage makes the branch, the last tags and fast-forwards main. | `default_release_gates_reproduce_today` (unit); the existing `promote_to_production_tags_and_fast_forwards_main`, `a_failed_cut_rolls_back_the_tag_and_main`, `promote_candidate_creates_branch`, `promote_production_cuts_tags_merges`, `promote_production_refuses_unclean_merge`, `promote_without_branch_makes_it_first`, `monitor_promote_matches_cli` unchanged |
| R-4 | WHEN a release is promoted, THE SYSTEM SHALL work out every condition and step of the stages entered or passed before changing anything, and refuse with every missing condition and its fix if any fails. | `promotion_refused_lists_every_missing_condition` (integration), `condition_met_by_same_promotion_counts` (unit) |
| R-5 | WHEN a stage with `move_main` is entered, THE SYSTEM SHALL fast-forward main to the release tip without tagging, refusing if main has commits the release lacks. | `move_main_stage_fast_forwards_without_tagging` (integration) |
| R-6 | WHEN a stage with `tag` is entered, THE SYSTEM SHALL tag the release tip only when main is at it and its required conditions hold. | `cut_tags_main_only_when_pushed` (integration, bare remote) |
| R-7 | THE SYSTEM SHALL judge `pushed` from main's remote-tracking branch, fetching first when applying, using the last-fetched refs when the fetch fails, and SHALL never push. | `pushed_condition_reads_remote_tracking_ref` (unit), `promote_fetches_and_works_offline` (integration), `git_model_never_pushes` (existing) |
| R-8 | WHEN a stage with `prepare` is entered, THE SYSTEM SHALL commit the version files, the dated changelog heading, its copies, the notes draft and listings onto `release/<V>` in one commit, without checking anything out. | `version_template_sets_first_or_every_match`, `changelog_heading_dated_with_compare_links` (unit), `commit_files_moves_branch_without_checkout` (unit), `prepare_commits_version_changelog_and_notes` (integration) |
| R-9 | IF a version file is missing or its match finds nothing, THEN THE SYSTEM SHALL refuse the promotion and change nothing. | `prepare_refuses_unmatched_version_file` (integration) |
| R-10 | WHILE nothing is configured to prepare, THE SYSTEM SHALL bump no version, say so in the plan, and make no commit. | `prepare_with_nothing_configured_makes_no_commit` (integration) |
| R-11 | IF a step or the board write fails after earlier steps, THEN THE SYSTEM SHALL undo every git step in reverse order. | `failed_promotion_undoes_every_step` (integration) |
| R-12 | THE SYSTEM SHALL show on each unshipped release one button naming its next step, with what it will do and, for the cut, its preview, enabled only when the plan is ready, and otherwise what is missing. | `web::release_button_says_what_it_does` (`web/scripts/check-release-action.mjs`), `release_plan_route_matches_promote` (view_daemon), `check:api-types`, `check:read-only`; manual: "on kanbanr's board, v0.3.0 goes Promote to candidate → Promote to main → 'Cut v0.3.0' disabled with 'push main, then wait for CI' until main is pushed, then one click cuts it, light and dark" |
| R-13 | WHEN `release promote --plan` is run, THE SYSTEM SHALL print the plan and change nothing; after a promotion it SHALL print what is next. | `promote_plan_changes_nothing` (local_mode) |
| R-14 | IF the release tip differs from the plan the caller saw, THEN THE SYSTEM SHALL refuse the promotion. | `promote_refuses_when_release_moved_since_plan` (unit) |
| R-15 | THE SYSTEM SHALL keep `release_gates` and `release_prepare` across cadence writes that do not name them. | `release_gates_survive_cadence_put` (unit) |
| — | The flow as lived with 0.2.1 | `release_flow_as_lived_with_0_2_1` (local_mode: candidate → branch + prep commit; main → ff; production refused "push main"; the test pushes to a bare remote; production tags main's tip; the remote has no tag) |

### 8. Affects docs
- `docs/src/using/processes.md`:
  - "Release stages": add the stage gates and actions, the default table, and preparing a release;
  - a new "Preparing a release" subsection;
  - the commands block at lines 324–327.
- `docs/src/using/the-method.md`:
  - "At the release role" (line 138);
  - the who-merges table, lines 155–158. Those rows become "`release/<V>` into main at its `move_main` stage (by default the last); tagged at the cut, after main is pushed if the stage requires `pushed`", plus the line "kanbanr commits only its release-preparation commit on `release/<V>`".
- `docs/src/using/the-monitor.md`: the "Promote" bullet (lines 274–282) becomes one button with steps, preview and missing list, and no confirm panel.
- `docs/src/reference/cli.md`: lines 59–60, plus `release stages`, `config release-stage`, `config release-prepare`.
- `docs/src/reference/http-api.md`: the plan route; regenerate `docs/src/reference/openapi.json`.
- `skill/kanbanr/SKILL.md`:
  - "At the release role" (line 621): a release prepares itself, so never make a release-prep item; the stage gates; Claude runs `release promote` and states `next`; the user pushes main and the tag;
  - the command reference (lines 1063–1064).
- `CHANGELOG.md` `[Unreleased]`, then `tools/docs/sync.sh`.
- Optional: `docs/src/project/open-sourcing.md` lines 235–239 (cut via promote).

### 9. Open questions (each with a recommended answer)
1. **Config shape:** separate `release_gates` map, or string-or-map entries in `release_stages`? **Recommend the separate map.** Mixed entries make older binaries fail to load the board, while a new key is kept by them (FEAT-151). It also mirrors `statuses`/`gates`.
2. **kanbanr's own board:** adopt `[candidate, main, production]` with prepare on candidate? **Recommend yes.** It needs the user's go, since it is a kanbanr write (task 11).

### Implementation tasks
1. **Config types and validation.**
   - New `api/crates/kanbanr-core/src/releasegates.rs` (`pub mod` in `lib.rs`): `ReleaseAction`, `ReleaseCheck` (`ALL`, `name`, `passes_when`, `does`, hand-written `Deserialize` naming the valid ones), `ReleaseGate`, `ReleasePrepare` (`is_empty`), `VersionFile`, `NotesListing`, and `impl Cadence { effective_release_gates(&self) -> Vec<(String, ReleaseGate)>, validate_release_gates(&self) -> Result<(), String> }`, with the rules in §1.
   - `config.rs` `Cadence` gains the two fields (serde default, skip when empty).
   - Tests: `release_gates_read_beside_stage_names` (R-1), `release_gates_validated` (R-2), `default_release_gates_reproduce_today` (R-3).
   - Depends on: none.
2. **Text transforms.**
   - New `releaseprep.rs` with the §2 signatures, template matching and changelog rules exactly as in §1.
   - Tests: `version_template_sets_first_or_every_match`, `changelog_heading_dated_with_compare_links` (R-8).
   - Depends on: none.
3. **Git plumbing in `coderepo.rs`.**
   - `run_with`, `read_blob`, `commit_files`, `undo_commit`, `upstream_of`, `remote_of`, `fetch_branch`, `remote_branches_containing` as in §2. The push refusal is kept in `run_with`.
   - Tests: `commit_files_moves_branch_without_checkout` (R-8), `pushed_condition_reads_remote_tracking_ref` (R-7, a bare remote made with `git init --bare` in a temp dir).
   - Depends on: none.
4. **Plan.**
   - `releases.rs`: `Fetch`, `PlanCondition`, `PlanStep`, `OriginState`, `ReleasePlan`, `plan(...)`. It walks the stages passed and entered, collects actions in `ReleaseAction` order, evaluates the conditions with the same-promotion rule, adds the intrinsic preconditions with today's messages, and sets `preview`, `tag_commit`, `button`, `missing` and `after`.
   - Tests: `condition_met_by_same_promotion_counts` (R-4).
   - Depends on: 1, 2, 3.
5. **Apply.**
   - `releases.rs`: `PromoteOptions`, `promote_with`, the `promote` wrapper, the `Undo` engine, and `step_branch`, `step_prepare` (the file set from `read_blob` + `releaseprep`, the message from §2, `commit_files`), `step_move_main`, `step_tag`. Fold `promote_to_production` into these steps.
   - Extend `Promoted`, add "again", report forward merges for every release, and run prepare in `add_patch`.
   - Tests: the existing R-3 tests unchanged, plus `move_main_stage_fast_forwards_without_tagging` (R-5), `cut_tags_main_only_when_pushed` (R-6), `promote_fetches_and_works_offline` (R-7), `prepare_commits_version_changelog_and_notes` (R-8), `prepare_refuses_unmatched_version_file` (R-9), `prepare_with_nothing_configured_makes_no_commit` (R-10), `failed_promotion_undoes_every_step` (R-11, using the existing folder-in-the-way trick), `promote_refuses_when_release_moved_since_plan` (R-14), `promotion_refused_lists_every_missing_condition` (R-4).
   - Depends on: 4.
6. **Store, routes and OpenAPI.**
   - `store.rs`: `set_cadence` validation, `set_release_gate`, `set_release_prepare`.
   - `dispatch.rs`: the cadence PUT keeps the new fields; the new routes from §3; `expect` on promote.
   - `openapi.rs`: the plan route. Regenerate `openapi.json`.
   - Tests: `release_gates_survive_cadence_put` (R-15), `release_stage_routes_round_trip` (R-1).
   - Depends on: 1, 5.
7. **Daemon.**
   - `api/crates/kanbanr-server/src/routes.rs`: the `code_repo_for` helper, and `read_passthrough` → `dispatch_in` with it. Coordinate with FEAT-213 task 2.
   - Test: `release_plan_route_matches_promote` in `api/crates/kanbanr-cli/tests/view_daemon.rs` (R-12).
   - Depends on: 6.
8. **CLI.**
   - `api/crates/kanbanr-cli/src/main.rs`: `ReleaseCmd::Promote` gains `--plan` and `--fetch`; `promote_release` prints steps and `next`; new `ReleaseCmd::Stages`, `ConfigCmd::ReleaseStage`, `ConfigCmd::ReleasePrepare`.
   - Tests in `tests/local_mode.rs`: `promote_plan_changes_nothing` (R-13), `release_flow_as_lived_with_0_2_1`; the existing promote tests pass unchanged.
   - Depends on: 6.
9. **Web.**
   - `web/src/types.ts` (Cadence fields, ReleasePlan types), `web/src/api.ts` (`getReleasePlan`, `promoteRelease(..., expect?)`), new `web/src/releaseAction.ts`, and `ReleasesPage.tsx` as in §4.
   - New `web/scripts/check-release-action.mjs` (`web::release_button_says_what_it_does`, R-12; cases: middle stage, cut ready, cut missing `pushed`, read-only, no repo), `web/package.json` `check:release-action`, and a step in `.github/workflows/ci.yml` next to `check:card-text` (line 213).
   - Run `check:api-types`, `check:read-only`, `check:ui`.
   - Depends on: 6, 7.
10. **Docs and skill.**
    - Everything in §8, plus the CHANGELOG entry and `tools/docs/sync.sh`.
    - The manual check for R-12.
    - Depends on: 8, 9.
11. **kanbanr's own board** (needs the user's go; these are kanbanr writes).
    - `kanbanr config cadence --release-stages candidate,main,production`
    - `kanbanr config release-stage candidate --on-enter branch,prepare`
    - `kanbanr config release-stage main --requires items_finished --on-enter move_main`
    - `kanbanr config release-stage production --requires main_at_release,pushed --on-enter tag`
    - `kanbanr config release-prepare` with the §1 file list. Confirm the Cargo.lock and package-lock entries with `--plan` first.
    - Depends on: 8.
