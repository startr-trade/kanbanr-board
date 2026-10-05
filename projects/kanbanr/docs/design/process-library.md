# Your own process: designed in conversation, saved on the board, reused

## Context

A project can already run a custom process: `kanbanr config workflow --from-file` loads statuses,
transitions and gates, and `--export` writes them out. But nothing helps a user *write* that file
(the skill's setup interview just says "load your own with `--from-file`"), nothing checks a file
without applying it, and a process lives only inside the project it was applied to — every other
project, and every teammate, has to copy it by hand.

The user wants:
- the setup step (and any later "let's change our process") to design a process with gates
  **through dialogue**;
- the result kept as a **separate YAML** that other projects reuse;
- the shared copies kept **on the board**, so the team gets them through the board's git remote
  (which is already the sharing and access boundary);
- a personal folder too, for carrying a process to another board;
- when a saved process changes, projects using it are **told** (doctor) and change **only on
  request**;
- all of it **before 1.0**, lifting FEAT-150's "new features wait for 1.x".

## Design

### 1. Where processes live, and how a name is found

| Library | Location | Shared with | Written by |
|---|---|---|---|
| Board (default) | `<board>/processes/<name>.yaml`, beside `projects/` | everyone who has the board, via its remote | `kanbanr process save <name>` (one board commit) |
| Personal | `~/.kanbanr/processes/` (`%USERPROFILE%\.kanbanr\processes` on Windows; `KANBANR_PROCESSES_DIR` overrides, as tests need) | only this user, on any board | `kanbanr process save <name> --personal` |
| Built-in | the 7 presets embedded in the binary | everyone | releases |

- **The user chooses where each process is saved**, board or personal, every time it is saved.
  The dialogue asks it as one question (board recommended when the board has a remote others
  use); the CLI defaults to the board.
- **`~/.kanbanr/` as a folder is safe:** `find_marker` (project.rs) matches only a *file* named
  `.kanbanr` and skips the home folder entirely, so a `~/.kanbanr/processes/` directory is never
  mistaken for a project marker. A test pins that.
- **Lookup order for a name:** board → personal → built-in. A saved process may not take a
  built-in name. When the board and the personal folder both have a name, the board wins and
  `process list` flags the shadowed copy.
- **One resolver**, used by `config workflow --preset`, `project init --workflow` and every
  `process` command, extending `config::preset(name)` (`api/crates/kanbanr-core/src/config.rs`).

### 2. The process file

Today's `WorkflowFile` (config.rs) plus an optional header, so the file stays loadable by
`--from-file` on older binaries (unknown keys are ignored there):

```yaml
process:
  name: our-process
  description: Design review before build; QA signs off the release.
  version: 3                 # bumped by `process save` when the content changes
statuses: [...]
transitions: {...}
gates: {...}
```

The **content rev** (a hash of everything but the header, as `content_rev` is for definitions)
is what drift is measured against; the version number is for people.

### 3. Provenance on the project

`ProjectConfig` gains an optional `process: {name, library: board|personal|builtin, version,
rev}`, written when a workflow is applied from a named process (and cleared by
`--from-file`/flags that don't name one). Older binaries keep it untouched through `extra`
(FEAT-151), so **no schema bump**.

### 4. Commands (a new `kanbanr process` group; `config workflow` keeps working)

| Command | Does |
|---|---|
| `process list` | every process by library: name, version, description, which projects on this board use it, shadowing |
| `process show <name>` | the YAML, its working agreement and a Mermaid diagram |
| `process checks [--json]` | the gate vocabulary: each check's name, what it means, parameters (Zachman columns) — what Claude maps answers onto |
| `process check <file\|name>` | validate **without applying** (statuses, transitions, gates, checks, Zachman columns), then print the working agreement and diagram |
| `process save <name> [--from-file F \| --from-project P] [--personal] [--description D]` | write to the library; bump the version when the content changed; a board save is one commit |
| `process diff [--project P]` | what differs between the project's workflow and the saved version it came from (statuses, transitions, gates) |
| `process update [--project P]` | apply the saved process's current version to the project; refused if a status that still holds items would disappear, naming `config rename-status` as the way through |
| `config workflow --preset <name>` | now resolves saved processes too, and records provenance |

Core work behind them:
- **`config::validate_workflow(&WorkflowFile)`**: the checks now inside `Store::set_workflow_with_gates`
  and the private `validate_gates` (store.rs) moved into one pure function; the store calls it,
  `process check` calls it alone. One validator, not two.
- **`readiness::Check::ALL` plus a one-line description per check**, so `process checks` and the
  docs' check table come from the same source (`check:docs` compares them).
- Routes for the CLI's single-writer path: `GET /processes`, `GET /processes/{name}`,
  `PUT /processes/{name}` (board library), `GET /projects/{p}/process/diff`,
  `POST /projects/{p}/process/update`. The monitor stays read-only.

### 5. Telling projects a process has changed (report, apply on request)

- **`doctor`** gains `scan_process_drift` (doctor.rs, beside `scan_stray_folders`):
  - "this project uses *our-process* v3; the board has v4 — `kanbanr process diff` /
    `process update`" (a warning);
  - "this project's workflow was edited after it was applied from *our-process* v3" (a warning).
- **Session start** (the SessionStart summary) mentions an available update in one line, like it
  counts waiting approvals.
- **Monitor Workflow page**: "Process: *our-process* v3 (board)" and the drift notice.
- **In-flight items** meet the new gates on their next move; existing approvals stay valid.

### 6. The dialogue (skill)

In the setup interview's **c. Process** step, and whenever the user asks to design or change a
process later — always in plan mode:

1. **Saved processes first.** `kanbanr process list --json`: offer the board's and personal
   processes before the built-ins, in one AskUserQuestion.
2. **"Our own" starts from the nearest built-in.** Claude asks how work flows today in the user's
   words, picks the closest process, and proposes stages to correct, not a blank page.
3. **One AskUserQuestion per stage: "What must be true before work enters *Stage*?"** Options are
   the checkable conditions from `process checks --json`, phrased in the user's words,
   multi-select. Anything kanbanr can't see becomes a **named sign-off**, said back plainly ("so
   *architecture-review* is a sign-off a person records").
4. **Process-wide questions, batched**: block or warn per stage; where the code branch starts;
   which stage ends the work; which rework moves back are allowed.
5. **Name it and choose where it is kept**: on the board (the team gets it through the board's
   remote) or personal (`~/.kanbanr/processes`, yours on any board). One question, board first
   when the board has a remote.
6. **Draft, check, show.** Claude writes the YAML to the scratchpad, runs `process check` on it,
   and puts the **working agreement and diagram** in the plan, with the exact commands
   (`process save <name> [--personal] --from-file …`, then `config workflow --preset <name>`).
   Accepting the plan accepts the process.
7. **Changing a process later** uses the same steps from `process show`, and then offers
   `process update` for each project on the board that uses it, one question per project.

The "workflow decides what you ask" section (SKILL.md) is unchanged: it already reads gates, not
preset names.

### 7. Decision record and 1.0

- **ADR-0013 (proposed, accepted when the last item lands):** *Shared processes are board data.*
  They travel with the board's git remote like everything else; there is no separate process
  server or registry; the personal folder exists only to carry a process between boards.
- **FEAT-150** is amended: its "Out of scope: new features wait for 1.x" gains "except the process
  library (FEAT-…), decided 5 Oct 2026", and it depends on the new items. Editing it lapses its
  approval, so it comes back for re-approval.
- **Stability policy** (`docs/src/project/stability.md`): the process file format, the board's
  `processes/` folder and the `process` commands join the stable surface at 1.0.
- **Risk, stated plainly:** the three-weeks-without-a-break clock exists so the stable surface has
  been used before it is promised. This surface would be days old at 1.0. If you want, 1.0 can
  label it "new in 1.0" in the stability policy, to be promised stable from 1.1.

## Board items (one batch after approval, milestone MS-009, each with the house definition)

| Item | Scope | Depends on |
|---|---|---|
| A | `validate_workflow` extracted; `Check::ALL` + descriptions; `process checks`, `process check`; docs check table generated-and-compared | — |
| B | Libraries (board, personal, built-in) and the resolver; the file header; `process list/show/save`; `--preset` resolves saved names; provenance on `ProjectConfig`; routes | A |
| C | Drift: `process diff`, `process update`, `scan_process_drift`, the session-start line, the monitor Workflow page's process line | B |
| D | Skill dialogue (setup interview c. Process, and "change our process"); docs (`processes.md`: "Designing a process with Claude", "Saving and sharing processes"; `with-claude.md`); ADR-0013; CHANGELOG; stability policy entry | B, C |
| FEAT-150 | amended as above, re-approved, depends on A–D | A–D |

Order: A → B → C → D. Each is approved before it starts, on its own branch, with `make ci` before
merging. Nothing is pushed.

## Critical files

- `api/crates/kanbanr-core/src/config.rs`: `preset()` → resolver; `WorkflowFile` header; provenance on
  `ProjectConfig`; `validate_workflow`
- `api/crates/kanbanr-core/src/store.rs`: `set_workflow_with_gates` / `validate_gates` call the shared
  validator; board library read/write beside `projects_dir()`
- `api/crates/kanbanr-core/src/readiness.rs`: `Check::ALL`, descriptions
- `api/crates/kanbanr-core/src/dispatch.rs`: `apply_workflow` records provenance; new routes
- `api/crates/kanbanr-core/src/doctor.rs`: `scan_process_drift`
- `api/crates/kanbanr-core/src/project.rs`: personal library dir (beside `home_dir()`)
- `api/crates/kanbanr-cli/src/main.rs`: the `process` command group; `ConfigCmd::Workflow` unchanged in
  shape
- `web/src/pages/WorkflowPage.tsx`, `web/src/types.ts`, `web/src/api.ts`
- `skill/kanbanr/SKILL.md`, `docs/src/using/processes.md`, `docs/src/using/with-claude.md`,
  `docs/src/project/stability.md`, `CHANGELOG.md`, the SessionStart hook summary

## Verification

- **Core unit tests** (lib.rs, beside `presets_apply_with_their_gates` and `workflow_files_round_trip`):
  validate refuses each bad shape and applies nothing; a saved name resolves board → personal →
  built-in; a built-in name can't be saved; save bumps the version only on a content change;
  applying records provenance; `--from-file` clears it; a schema-2 board with provenance loads in
  the current reader unchanged.
- **One validator:** every case `set_workflow_with_gates` refused before still refuses, with the same
  message (golden over the existing tests).
- **CLI integration tests** (`tests/local_mode.rs`, fake `HOME`, `KANBANR_PROCESSES_DIR` set):
  - two projects on one board share a saved process; a `git clone` of the board (the teammate) lists
    and applies it;
  - a personal process carried to a second board; a `~/.kanbanr/processes/` folder never acts as a
    project marker (`project use`/`where` from under home unaffected);
  - save v2, then `doctor` reports drift on the first project, `process diff` shows the gate change,
    `process update` applies it; an update that would drop an occupied status is refused naming
    `rename-status`;
  - `process check` on a bad file exits non-zero and changes nothing on the board (`git status`
    clean).
- **The guardrail seen failing (ADR-0008):** reintroduce a second validator path or drop the drift
  scan, and watch the tests go red.
- **Walkthrough with a real Claude session** in a scratch folder (created and checked in its own
  step, lesson L-37): design "our process" through the dialogue, save it to the board, start a
  second project that picks it from the list, change it, and see the drift notice and the update
  offer. The walkthrough folder and GTM notes outside the repo are updated afterwards.
- **Monitor:** headless screenshot of the Workflow page's process line and drift notice.
- **`make ci`** (all checks) before each merge; the legacy-load invariant (`kanbanr board` and
  `feature show` on this board give zero YAML diff).

## Out of scope

- A process registry or server outside the board (sharing is the board's git remote).
- Applying a process change to projects automatically.
- Editing processes in the monitor (it stays a viewer).
- Merging two diverged versions of a process; `process diff` shows them, a person decides.
