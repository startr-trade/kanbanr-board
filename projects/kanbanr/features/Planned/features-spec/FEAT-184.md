# Patch releases

Fixes to a release that is already in production need their own release: a branch from the cut release's tag, the defect items merged into it, tested through the stages, then promoted like any release.

Scope:
- `kanbanr release add <VERSION> --patch-of <PARENT>` creates a release with a `parent` reference, and creates its branch `release/<VERSION>` from the parent's tag.
- The patch release lists its parent's items as included, and its own items (typically defects) as added.
- Release notes show the parent and what the patch adds.
- Fixes merged into a patch release are also reported for forward-merging into the integration branch, so the next release does not lose them.

## Design

### Summary
A patch release names its parent: a release that has been cut and tagged. It branches from the
parent's tag, and goes through the same stages (FEAT-183). Its notes show the parent and what the
patch adds. When the patch reaches production, kanbanr lists the commits on the patch branch that
the integration branch doesn't have yet, so they can be merged forward and the next release keeps
them.

### Components and files
- `api/crates/kanbanr-core/src/releases.rs`: `Release.parent`, `add` with `patch_of`, notes for a
  patch, `forward_merge` in the production result.
- `api/crates/kanbanr-core/src/coderepo.rs` (FEAT-183): `create_branch_from(ref)`, used with the
  parent's tag; `log_between(base, head) -> Vec<CommitLine>`.
- `api/crates/kanbanr-core/src/dispatch.rs`: `POST /releases` accepts `patch_of`.
- `api/crates/kanbanr-cli/src/main.rs`: `release add <V> --patch-of <PARENT>`; production promotion
  prints the forward-merge list.
- Docs: processes.md, cli.md, CHANGELOG.

### Data model
```rust
// releases.rs — Release
/// The release this patches (FEAT-184); empty for an ordinary release.
#[serde(default, skip_serializing_if = "String::is_empty")] pub parent: String,
pub struct CommitLine { pub sha: String, pub subject: String }
pub struct Promoted { /* FEAT-183 fields */, pub forward_merge: Vec<CommitLine> } // non-empty only for a patch reaching production
```

### Behaviour
- `add(store, id, version, target, name, patch_of: Option<&str>, repo: Option<&Path>)`:
  - **The parent** must exist, be shipped, and have a tag in the repository. Otherwise:
    "<PARENT> has not been cut (or has no tag), so there is nothing to patch".
  - **The branch.** Creates `release/<V>` from the parent's tag, sets `branch`, and sets
    `stage = <first stage>` with a history entry ("candidate on creation"). Refuses if the branch
    already exists.
  - **With no repository:** refuses, for the same reason as FEAT-183's first stage.
  - **Version order:** the patch version is not checked against the parent's semver; the user
    names it.
- **Scope.** The parent's `shipped` items count as **included**. The patch's own planned items,
  usually defects, are **added**. `report_all` exposes `included` (the parent's shipped list) for a
  patch.
- **Notes.** A patch's notes start with "Patch of <PARENT>", then "## What this patch adds" (its
  shipped items), then "## Included from <PARENT>" (the parent's list), then carried-over as
  usual.
- **Production for a patch.** After FEAT-183's tag and merge into main, the result lists
  `forward_merge = log_between(integration_branch, branch)`: the patch's commits not on the
  integration branch. The CLI prints it, as "Merge these forward into <integration>: …", and the
  notes record it under "## To merge forward".
  - kanbanr never merges forward itself: the user decides how to bring those fixes in.
  - When the integration branch is main itself, the list is empty, because the merge already
    brought them.

### Compatibility
A new optional field (Release gains `extra` in FEAT-183).

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `patch_release_branches_from_parent_tag` (the branch's base is the parent's tag commit) | cli local_mode.rs |
| R-2 | `patch_release_notes_show_parent_and_additions` | core lib.rs |
| R-3 | `patch_release_reports_forward_merge` (integration ≠ main; a fix commit on the patch is listed; nothing listed when integration = main) | cli local_mode.rs |

### Implementation tasks
1. **Model and add.** releases.rs: `parent`, `add` with `patch_of` (parent checks, branch from
   the tag, initial stage); the dispatch body field; CLI `--patch-of`. Test: R-1. Depends on
   FEAT-183 tasks 1–3.
2. **Notes and scope.** releases.rs: patch notes sections, `included` in the report. Test: R-2.
   Depends on 1.
3. **Forward merge.** releases.rs: `promote` sets `forward_merge` for a patch; the notes section;
   the CLI prints it. Test: R-3. Depends on 1 and FEAT-183 task 3.
4. **Docs.** processes.md "Patch releases"; cli.md; CHANGELOG with the docs sync. Depends on 3.

### Open questions
- **Q1.** Should a patch release need `--patch-of` to name the **latest** cut release?
  - Recommended: no. Any cut release can be patched, for example an older supported version.

### Affects docs
docs/src/using/processes.md, docs/src/reference/cli.md.
