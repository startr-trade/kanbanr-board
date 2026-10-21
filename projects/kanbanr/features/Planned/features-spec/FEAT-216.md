# A release's notes can be read and edited from the release

## Why
On 22 Oct 2026, after promoting v0.3.0 to candidate, the user could not find its notes:
"v0.3.0.md is not found" — "why can't I see it in my IDE and board?". FEAT-212's `prepare` writes
the draft notes onto `release/<V>` without checking that branch out, so the person's checkout does
not show them; and the board's pages show board docs, not files in the code repository. A
candidate's notes could not be changed either: people may not commit on `release/*`, so the only
way was a separate fix item — the redundancy FEAT-212 removed.

## Design

### Core (`api/crates/kanbanr-core/src/releases.rs`)
- `pub struct ReleaseNotes { pub version, pub path: String, pub text: String, pub at: String /* sha7 of release/<V> */, pub editable: bool, pub why_not: String }`
- `pub fn release_notes(store, id, version, repo: Option<&Path>) -> Result<ReleaseNotes>`: the notes
  file is `release_prepare.notes` expanded for the version (`releaseprep::expand`); its text is read
  at the tip of `release/<V>` with `coderepo::read_blob`. Editable while the release has a branch
  and is not shipped. Errors, plainly: no notes path configured; no branch yet ("promote it to
  candidate first"); no repository; the file absent at the tip.
- `pub fn set_release_notes(store, id, version, repo, text, by) -> Result<(String /*sha*/, ReleaseNotes)>`:
  commits `text` to that path on `release/<V>` with `coderepo::commit_files` (no checkout; refused,
  as the prepare commit is, when the branch is checked out in a worktree), message
  `Release <V>: notes` + body `Edited through kanbanr release notes by <by>.` + `[no-ref] release notes, written by kanbanr` + `Kanbanr-Release: <V>`. Same text → no commit. Refused once
  shipped. Also re-applies the `notes_listings` entries (idempotent), so a listing added to the
  config later reaches a candidate already made.
- Agent scopes (FEAT-214): an operation outside every scope (refused from agent worktrees).

### Routes (`dispatch.rs`), internal
- `GET /projects/{p}/releases/{v}/notes` → `ReleaseNotes` (the daemon reads with its repository, as
  the plan route does: add it to the read routes that get `repo_for`).
- `PUT /projects/{p}/releases/{v}/notes` `{text, by}` → `{sha, notes}`; a write route (only on a
  write-enabled daemon), commit message on the board `release <V>: notes edited`.

### CLI (`main.rs`)
- `kanbanr release notes <V>` prints the notes and where they are (`release/v0.3.0 @ 8f995e1:
  docs/src/releases/v0.3.0.md`); `--json`.
- `kanbanr release notes <V> --file F` (or `-` for stdin) commits F's text; prints the new sha.
- `kanbanr release notes <V> --edit` opens `$VISUAL`/`$EDITOR` on a temporary copy and commits it
  when it changed.

### Monitor (`web/src/pages/ReleasesPage.tsx`)
- For a release with a branch and configured notes: a **Release notes** section, collapsed by
  default, rendering the text with the `Markdown` component, headed "draft on release/v0.3.0 @
  8f995e1" (or "as shipped" after the cut).
- On a write-enabled monitor, for an unshipped release: **Edit notes** opens a textarea with the
  text; **Save** sends the PUT and shows the new sha; **Cancel** discards. Read-only monitors show
  the text and the CLI command only (`check:read-only`).
- `types.ts`/`api.ts`: `ReleaseNotes`, `getReleaseNotes`, `saveReleaseNotes`.

### kanbanr's own board
- Add `docs/src/releases/index.md` as a second notes listing (after its "- **[0.2.1](v0.2.1.md)**"
  line form: entry `- **[{number}]({version}.md)** — {name}`), so the release-notes index lists each
  new release; saving v0.3.0's notes then also lists it there.

### Test plan
| Req | Test |
|---|---|
| R-1 | `release_notes_read_from_the_release_branch` (unit: path from config, text at the tip, errors) |
| R-2 | `set_release_notes_commits_onto_the_release_branch` (unit: one commit, nothing checked out, same text no commit, refused once shipped, listings re-applied) |
| R-3 | `cli_release_notes_shows_and_saves` (local_mode: show, `--file`, `--json`) |
| R-4 | `web::release_notes_section` (check script over the section builder: draft/shipped headings, edit offered only when writable and unshipped) and `check:read-only`; `manual: v0.3.0's notes rewritten from the Releases page in light and dark` |

### Implementation tasks
1. Core: `ReleaseNotes`, `release_notes`, `set_release_notes`; R-1, R-2. Depends on: none.
2. Routes and daemon read repo; CLI `release notes` (show, --file, --edit); R-3. Depends on 1.
3. Monitor section with edit; types, api; check script, ci.yml step, ci_local LOCAL; R-4 automated part. Depends on 2.
4. Docs (processes.md "Preparing a release": the notes can be read and edited from the release; cli.md; the-monitor.md; SKILL.md release role), CHANGELOG. Depends on 3.
5. kanbanr's board: the index.md listing; rewrite v0.3.0's notes through the new command; the manual check. Depends on 3 (coordinator).

### Affects docs
docs/src/using/processes.md, docs/src/reference/cli.md, docs/src/using/the-monitor.md, skill/kanbanr/SKILL.md, docs/src/project/changelog.md.
