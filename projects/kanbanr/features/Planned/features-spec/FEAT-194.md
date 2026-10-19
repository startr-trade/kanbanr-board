# One method in the skill and the setup interview

The skill states the method once, by role, so it holds for every process:
- design-stage specs with hand-off task lists;
- living documentation and the fold-in;
- live links;
- the git model from the cadence: who merges and who pushes;
- releases and their stages;
- carry-over.

The setup interview asks whether to use sprints and releases, shows the resulting git model, and records the roles. Per-user instruction files that copy these rules become unnecessary, and the skill says so.

## Design

### Summary
The skill gets one section, **"The method by stage role"**, that states the whole method once,
keyed by the roles of [FEAT-188](/p/kanbanr/feature/FEAT-188) rather than by status names. Each
rule names the command that now carries it:
- design: a build-ready Design and its hand-off tasks ([FEAT-179](/p/kanbanr/feature/FEAT-179)),
  `affects_docs` ([FEAT-180](/p/kanbanr/feature/FEAT-180)) and live links
  ([FEAT-181](/p/kanbanr/feature/FEAT-181));
- build: the item branch from the line of integration ([FEAT-189](/p/kanbanr/feature/FEAT-189));
- integrate: the fold-in, `docs_updated` and `docs-folded`, and the merge
  ([FEAT-190](/p/kanbanr/feature/FEAT-190), [FEAT-191](/p/kanbanr/feature/FEAT-191));
- release: stages and the cut, patches ([FEAT-183](/p/kanbanr/feature/FEAT-183),
  [FEAT-184](/p/kanbanr/feature/FEAT-184));
- carry-over and the milestone compliance review.

The setup interview asks, for every process, whether sprints and releases are on, and shows the git
model that follows (`kanbanr git model --sprints … --releases …`) before the plan applies it. The tool
says so through `where --json`. The skill says personal instruction files that restate the method are
unnecessary. This item is built **last**: it describes behaviour that exists, so it waits for
FEAT-179 to FEAT-193.

### Components and files
- `skill/kanbanr/SKILL.md`: the new section; the setup interview (steps 3c, 4, 5); "Designing a
  process with the user" step 5; "The workflow decides what you ask" (a `docs_updated` row);
  "Code points back at the item"; "Where the rules live"; the command reference.
- `api/crates/kanbanr-cli/src/main.rs`: `run_where` adds the cadence question; `git model` accepts
  `--sprints on|off --releases on|off` and runs without a board (Q3).
- `api/crates/kanbanr-cli/src/skill.rs`: the guard test.
- Docs: `docs/src/using/the-method.md` (the same section, for people), `docs/src/using/with-claude.md`
  (setup), `docs/src/using/processes.md` ("Designing a process with Claude": roles),
  `docs/src/getting-started/quickstart.md`, `docs/src/reference/cli.md`, `CHANGELOG.md`.

### Skill: "The method by stage role" (content outline, in this order)
1. **Roles first.** `kanbanr process show <name>` and `process checks --json` name the status that
   holds each role. Reason from the role, never from a preset name. `kanbanr config method` says which
   parts of the method this project has on ([FEAT-193](/p/kanbanr/feature/FEAT-193)). A part that is
   off is not asked for, but it is still good practice.
2. **At the design role.** This moves today's "The design stage" subsection here, unchanged. It adds:
   - **Affects docs** as links, mirrored into `affects_docs`;
   - every reference written as a live link (the FEAT-181 link table);
   - decisions drafted as proposed ADRs and asked about at once;
   - undecided questions go to the user, never to a subagent.

   Leaving the design role asks for `spec_sections: [Design]` and a **Sign off design-review**
   question, which is offered once the section exists.
3. **At the build role.** `kanbanr start` branches from the line of integration that `git model`
   names, not always from main. Commit with `kanbanr commit`. Subagents take one task at a time from
   the todo-list. Never commit on main or on a line of integration (the hook refuses), and never push.
4. **At the integrate role.** Before moving:
   - fold the Design into each doc in `affects_docs`, as built (`docs_updated`);
   - ask **Sign off docs-folded**.

   Entering the role merges the branch into the line, with `--no-ff` and `Refs`. On conflict the
   item stays where it was. Then merge the line *into* the item branch, resolve, and move again.
   Never rebase. `kanbanr git doctor` names any branch and board disagreement; fix it before going on.
5. **At the release role.**
   - `kanbanr release promote <V> [stage]`; production is the cut, which tags and merges into main.
   - A patch is `release add <V> --patch-of <P>`, and the fixes it lists are merged forward.
   - In the sprints-only model, `sprint close` is the cut.
6. **Carry-over.** `sprint close --carry-to <SP>` keeps unfinished branches. Their catch-up merges
   are done by kanbanr, and conflicts are reported per item.
7. **Who merges, who pushes**: a table generated from `git model` output, one row per cadence (line
   of integration, where production happens, what kanbanr merges). The **code** repository is never
   pushed by kanbanr or by Claude: the user reviews and pushes. The board's own remote is synced
   after each write, which is a different repository.
8. **Each milestone ends** with an architecture compliance review: a component doc per component,
   as built, and the views updated (FEAT-180's living-docs chapter).

### Skill: other edits
- **Setup 3c**:
  - The *Cadence* bullet becomes a question for **every** process: "Sprints? Releases?" Recommend the
    chosen process's own setting. The sprint-length and release-frequency details follow only when
    on.
  - After the answer, run `kanbanr git model --sprints X --releases Y` and show its output verbatim
    in the question's follow-up and in the plan.
  - The *Definitions* bullet adds that design-before-build and the docs fold-in are on by default
    (`kanbanr config method --off` turns them off later). It's said, not asked (Q2).
  - For "our own process", the roles are part of the process design.
- **Setup 4** (plan commands):
  - `kanbanr config cadence --sprints on|off --releases on|off` for every process;
  - the `git model` output quoted under "Branching";
  - the roles, as `process show` prints them, under "Process".
- **Setup 5**: the checks also run `kanbanr git model` and, when the hooks were chosen,
  `kanbanr git doctor`.
- **Designing a process, step 5**: the process-wide question asks which stage holds each role:
  design, build, integrate and release. Build is where the branch is made. This replaces "where the
  code branch is made".
- **The workflow table**: `docs_updated` means "fold the design into the named docs; draft it into
  the plan". The `signoff` row names `design-review` and `docs-folded` as examples.
- **Code points back**: `start` branches from the line of integration. Add a pointer to the
  roles section.
- **Where the rules live**: one paragraph. This skill carries the method. A personal or project
  instruction file that restates it is unnecessary and drifts. If one disagrees with the board's
  gates, tell the user what differs, and ask which holds.
- **Command reference**: `git model`, `git doctor`, `config method`, `release promote`,
  `release add --patch-of`, `signoff --withdraw`.

### Behaviour: `where --json` and `git model`
- `run_where` asks, when the folder is not tracked, in this order: board, process, **cadence**, then
  the git identity when git has none. The cadence text:
  "Whether to work in sprints and releases — only after the process is chosen, because a process
  may switch them on (scrum, agile): recommend its own setting. Then show the resulting git model
  (`kanbanr git model --sprints on|off --releases on|off`): where items branch from and merge into,
  what kanbanr merges, and that pushing is always the user's — before the plan applies it."
- `kanbanr git model [--sprints on|off] [--releases on|off] [--json]`:
  - with either flag, it derives the model from those values over the board's cadence, or over
    all-off when there is no board;
  - without flags, it needs a board and uses its cadence (FEAT-189 R-1);
  - it uses FEAT-189's core derivation (assumed `git_model::derive(&Cadence) -> GitModel`), so the
    preview and the applied model cannot differ.

  JSON: `{line, branch_from, production_at, kanbanr_merges: [..], pushes: "you"}`.

### Compatibility
- The skill is reinstalled by `kanbanr skill` and the update path. Older skills keep working against
  newer binaries.
- `where --json` gains one array entry. A consumer that indexes by position (only our own test) is
  updated.
- `git model` flags are additive.

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `manual: skill method by role present and matches the docs` (the skill section and the-method.md section read side by side; every command named exists in `kanbanr --help`) | review |
| R-2 | `setup_asks_cadence_and_shows_git_model` (untracked git folder: `where --json` lists four questions, cadence third, naming `kanbanr git model` and "after the process"; `git model --sprints on --releases off --json` with no board gives line `sprint/<SP>`, production at sprint close, pushes `you`; the four combinations are distinct; after `init` + `config cadence --sprints on`, `git model --json` equals the preview) | cli tests/local_mode.rs |

Also: `skill::tests::skill_states_method_by_role` (the embedded SKILL.md has the section and one
subsection per role, and names `git model`, `git doctor`, `config method`, `release promote`,
`sprint close`, `affects_docs`, `docs-folded`, `design-review`). `where_names_the_questions_setup_must_ask`
is updated for four entries.

### Implementation tasks
1. **where.** main.rs `run_where`: push the cadence question after the process question. Tests:
   update `where_names_the_questions_setup_must_ask` (indices, count 4 and 3); first half of R-2.
   Depends on FEAT-189.
2. **git model preview.** main.rs: `--sprints`/`--releases` on `git model`; no board needed when
   either is given; `--json` shape above. Test: R-2. Depends on FEAT-189's derivation (skip if
   FEAT-189 shipped the flags, Q3).
3. **Skill section.** SKILL.md: write "The method by stage role" per the outline, moving "The design
   stage" into it (keep its text). Depends on FEAT-179, 180, 181, 182, 183, 184, 188, 189, 190, 191
   and 193 all released, so every command named exists.
4. **Skill edits.** SKILL.md: setup 3c, 4 and 5; process design step 5; the workflow table; Code
   points back; Where the rules live; the command reference. Depends on 3.
5. **Guard.** skill.rs: `skill_states_method_by_role`. Depends on 4.
6. **Docs.** the-method.md "The method by stage role" (the same rules for people, with the
   who-merges table); with-claude.md and quickstart.md (setup asks cadence and shows the model);
   processes.md (roles in process design); cli.md (`git model` flags); CHANGELOG with the docs sync.
   Depends on 4.
7. **Review.** Do R-1 by hand, record it as the manual green, run `kanbanr check FEAT-194`.
   Depends on 5 and 6.

### Open questions
- **Q1.** Ask the cadence question for every process, not only scrum and agile? Recommended:
  **yes**, as one question with two yes/no parts, recommending the process's own setting (off for
  most). The git model depends on it.
- **Q2.** Should setup also ask whether to keep the method gates? Recommended: **no**. The plan states
  they're on and how to turn them off. That's one question fewer (G-5), and the default is the
  point of FEAT-193.
- **Q3.** Is the no-board preview (`git model --sprints/--releases`) FEAT-189's or this item's?
  Recommended: **FEAT-189's**, as part of `git model`. Task 2 here is the fallback.
- **Q4.** FEAT-183 tags the release tip and merges `--no-ff` into main, but FEAT-190 says the line is
  fast-forwarded into main and tagged. The skill can state only one. Recommended: reconcile
  FEAT-190's design to FEAT-183 (tag, then `--no-ff` merge). The skill says "kanbanr tags it and
  merges it into main".
- **Q5.** Should kanbanr detect personal instruction files that restate the method (for example,
  doctor reading `~/.claude/CLAUDE.md`)? Recommended: **no**, because personal files are outside the
  board's boundary. The skill says such copies are unnecessary. Once this ships, the user removes the
  "Design and documentation discipline" section from their global CLAUDE.md themselves.

### Affects docs
- skill/kanbanr/SKILL.md, docs/src/using/the-method.md, docs/src/using/with-claude.md,
  docs/src/using/processes.md, docs/src/getting-started/quickstart.md, docs/src/reference/cli.md,
  CHANGELOG.md
- [design/process-as-configuration.md](/p/kanbanr/docs/file/design/process-as-configuration.md)
  (kick-starting a project: the setup interview)
