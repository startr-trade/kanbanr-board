# The Workflow page shows the cadence, the git model and every guard rail

## Why
Asked 21 Oct 2026: the monitor's Workflow page should show the project's release and sprint
setup and its git branching, together with the guard rails the project has on. Today it shows the
process diagram and each stage's gates only. The rest exists but is spread over CLI commands:
`config show` (cadence, release stages), `sprint show`, `release list`, `git model`, `config
method`, `config diagrams`, `config coverage`, the commit guard's rules and the board's push
policy. A person, or a session after a break, cannot see in one place how work moves from an item
branch to a tagged release, or what will be refused along the way.

## Design

### The page (`web/src/pages/WorkflowPage.tsx`), sections in this order
1. **Process** and **Stages**, as now.
2. **Cadence** (only when sprints or releases are on): sprints (length; the active sprint, its
   dates, linked to the Sprint page), releases (how often; the stages in order, the last marked
   "the cut"; each planned or unshipped release with its stage, linked to the Releases page).
3. **Git model**: topology, main, the line of integration and where items branch from, where
   production moves, item branch names, protected branches, what kanbanr merges and when, and
   "pushing is yours". Whether automation is on (and the command that switches it). When
   `git doctor` finds problems, their count and the first few, as a warning box.
4. **Guard rails**, one list, each with its state and the command that changes it:
   - the method's parts (`config method`): design, design-review, docs, docs-folded, links;
   - commits: only on an item branch, `Refs:` trailer naming the item, never on a protected branch;
     whether the hooks are installed in this repository;
   - diagrams: lint on write, strict or not (`config diagrams`);
   - coverage rules: how many, each rule's id and how many subjects it leaves uncovered
     (`config coverage`);
   - the board's push policy (`remote push-policy`), and that kanbanr never pushes code.

   Read-only, like the rest of the page; each line names its CLI command.

### Daemon (`kanbanr-server`)
- The read passthrough passes the project's code repository (the folder `kanbanr serve` started
  in, as release promotion already does) to `dispatch_in` for `GET …/git/model` and
  `GET …/git/doctor`, which answer 400 today because they get none. A daemon with no repository
  answers as the CLI does outside one, and the page then shows the model from the cadence alone.

### Core (`kanbanr-core`)
- `GET /projects/{p}/guards`: one read giving the guard rails above, as
  `{method: {...}, commits: {item_branch: true, trailer: "Refs", protected: [...],
  hooks_installed: bool|null}, diagrams: {strict}, coverage: [{id, uncovered}], push_policy}`.
  Built from what exists (`config method`, the git model's protected branches, `scm` policy,
  `DiagramsConfig`, the coverage report, the board's push policy); internal, not in the OpenAPI v1
  set. Pure assembly: no new rule lives here.

### Web
- `types.ts` / `api.ts`: `getGitModel`, `getGitDoctor`, `getGuards`, `getSprints` and
  `getReleases` (the last two exist).
- New components in `WorkflowPage.tsx` (or `components/workflow/*.tsx`) for the three sections,
  in the page's existing tile and chip styles; light and dark.

### Test plan
| Req | Test |
|---|---|
| R-1 | `guards_route_reports_every_guard_rail` (core: a board with sprints, releases, the git model on, strict diagrams and one coverage rule) |
| R-2 | `daemon_serves_git_model_with_its_repository` (view_daemon: `GET …/git/model` answers 200 with the line, from a daemon started in a scratch repository) |
| R-3 | `web::workflow_shows_cadence_git_model_and_guards` (check script over the page's pure section builders) and `check:api-types`, `check:read-only`, `check:ui` |
| R-4 | `manual: the Workflow page on kanbanr's board shows its sprint, releases, git model and guard rails, in light and dark` |

### Implementation tasks
1. Core: `GET /projects/{p}/guards`; its test (R-1). Depends on: none.
2. Daemon: repository for the git routes; its test (R-2). Depends on: none.
3. Web: the three sections, types and api; the check script (R-3). Depends on 1, 2.
4. Docs: the-monitor.md's Workflow page section; CHANGELOG; the manual check (R-4). Depends on 3.

### Affects docs
docs/src/using/the-monitor.md (the Workflow page), docs/src/project/changelog.md.
