# The Workflow page breaks on role-addressed gates

## Why
Since [FEAT-193](/p/kanbanr/feature/FEAT-193) put the method in as role-addressed gates
(`"@build"`, `"@integrate"`), the monitor's Workflow page fails on any project that has them. This
board has had them since 19 Oct 2026.
- **The diagram** shows "mermaid error: No such shape: undefined". It writes a note for each raw
  gate key, and `@build` becomes a note on `_build`, a state that does not exist.
- **The Stages panel** says every stage "asks nothing to enter". It reads the raw keys too, so it
  misses the method's gates and the built-in start rule.

## Design

### Components and files
- `api/crates/kanbanr-core/src/mermaid.rs`: the gate notes come from `config.effective_gates()`, in
  the order of `config.statuses`. These are the gates moves are judged by: role-addressed gates
  resolved onto their stage, and the built-in rule where a workflow declares none.
- `api/crates/kanbanr-core/src/dispatch.rs`: `GET /projects/:p/gates` returns
  `config.effective_gates()` (status → Gate).
- `web/src/api.ts`: `getGates(project)`. `web/src/pages/WorkflowPage.tsx`: the Stages panel uses
  it instead of `config.gates`.

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `mermaid::tests::gate_notes_name_real_states` (every built-in process with the method, and a label-only board: every note targets a declared state, no `_build`/`_integrate`; the build stage's note names `sign-off design-review`) | core mermaid.rs |
| R-1 | `manual: the Workflow page draws the diagram and lists the method's gates on this board` | review (monitor) |

### Implementation tasks
1. mermaid.rs: notes from `effective_gates()` in status order; the unit test. Depends on: none.
2. The `/gates` route, `api.getGates`, and the WorkflowPage Stages panel. Checks: `npm run build`,
   `check:ui`. Depends on 1.
3. CHANGELOG "Fixed", docs sync, make ci, a manual check in the monitor. Depends on 2.

### Affects docs
None (behaviour fix; CHANGELOG only).
