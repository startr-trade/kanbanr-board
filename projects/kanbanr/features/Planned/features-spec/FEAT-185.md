# Monitor release actions

When an item reaches the stage before its terminal one (for example Migration), the review queue asks which planned release it belongs to, with the planned releases as choices and 'new release' as an option. The Releases page shows each release's stage and offers 'Promote to <next stage>', with production clearly marked as the cut (tag + merge). These actions use the same commands as the CLI and need the writes-enabled monitor.

## Design

### Summary
Two monitor actions, using the same core operations as the CLI:
- **Which release?** When an item's immediate next stage is the terminal one, releases are on, and
  the item isn't planned into a release, the review queue asks which planned release it belongs to.
  The choices are the planned releases, plus "New release…".
- **Promote.** The Releases page shows each release's stage and offers **Promote to <next>**. It
  marks production as the cut, which tags and merges.

Both need the writes-enabled monitor. Without writes, the monitor shows the matching CLI command.

### Components and files
- `api/crates/kanbanr-core/src/dispatch.rs`, review route: a new `approval` kind, `release`, with
  `release_choices: Vec<String>` (planned versions, in file order).
- `api/crates/kanbanr-core/src/readiness.rs`: uses `immediate_next_gate` (FEAT-182) and
  `config.is_terminal`.
- `web/src/types.ts`: `PendingReview.approval` adds `"release"`; `release_choices?: string[]`;
  `Release.stage` and `stages`.
- `web/src/api.ts`:
  - `planIntoRelease(project, version, code)` → `POST /api/write/projects/:p/releases/:v/plan {items:[code]}`;
  - `addRelease(project, version, target, name)`;
  - `promoteRelease(project, version, stage?)` → FEAT-183's route.
- `web/src/pages/ReviewPage.tsx`: in `Brief`, the "release" kind renders one button per choice, plus
  "New release…", an inline form for version and target date that adds the release then plans the
  item into it.
- `web/src/pages/ReleasesPage.tsx`: a stage chip, stage history in a tooltip, and the Promote
  button. Before a production promotion, a confirm dialog lists what the cut will do: the items it
  ships, the tag `<V>`, and the merge `release/<V> → main`.
- Skill: "Waiting decisions" covers the release question. Docs: the-monitor.md.

### Behaviour
- **The review queue.** An item is included with `approval: "release"` when all of these hold:
  - `cadence.releases` is on;
  - the item is live work;
  - `feature.release` is empty;
  - the immediate next stage is a terminal status, or its gate requires `in_release`.

  `release_choices` lists the planned releases. If there are none, the only choice is "New
  release…". Sorting puts these after approvals and sign-offs.
- **Promote.**
  - The button shows only when writes are on and the release is not yet at the last stage.
  - It posts to the promote route, which goes through the same core `releases::promote` as the CLI.
  - The daemon passes the code repository root it knows (FEAT-183 Q1). When the daemon has none,
    the first-stage and production promotions return its refusal, shown in the page with the CLI
    command to use instead.
- **After any action**, the page refreshes from the live tick, as other verdicts do.

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `review_queue_asks_release_for_ready_item` (TOGAF-like board with releases on: an item at Migration with no release appears with choices; once planned it drops out; with releases off it is absent) | core lib.rs |
| R-2 | `monitor_promote_matches_cli` (daemon with `--allow-writes`, started in a scratch code repo: POST promote to candidate creates the branch, and the resulting releases.yaml equals a CLI promote on a twin board) | cli view_daemon.rs |
Plus: `check:ui` for the new buttons, and `npm run build`.

### Implementation tasks
1. **Queue.** dispatch.rs review route: the release kind and choices; a `ReviewEntry` field
   (typed, per FEAT-177). Test: R-1. Depends on FEAT-182 task 3.
2. **API client.** types.ts and api.ts additions. Check: build. Depends on 1 and FEAT-183 task 4.
3. **ReviewPage.** Release choice buttons and the New release form. Check: `check:ui`. Depends on 2.
4. **ReleasesPage.** Stage chip, history, Promote with the production confirm. Check: `check:ui`.
   Depends on 2.
5. **Daemon test.** view_daemon.rs R-2. Depends on 4 and FEAT-183 task 6.
6. **Docs and skill.** the-monitor.md (screenshots refreshed with `make screenshots`); SKILL.md;
   CHANGELOG with the docs sync. Depends on 5.

### Open questions
- **Q1.** Should the release question also appear in Claude Code sessions, as a question Claude asks
  from the queue?
  - Recommended: yes. The queue drives both, and the skill's table already turns `in_release`
    into "which planned release?".

### Affects docs
docs/src/using/the-monitor.md, skill/kanbanr/SKILL.md (Waiting decisions).
