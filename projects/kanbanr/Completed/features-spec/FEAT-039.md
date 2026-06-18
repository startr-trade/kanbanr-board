# Workflow state-chart: explicit terminal states + Mermaid I/O

**Design decision (locked):** the per-project `config.yaml` (`statuses`, `transitions`,
`default_state`, `displayed_states`, `no_op_states`) is the **single source of truth**. Mermaid is
**only an I/O format** — never the stored representation.

## Scope
1. **Explicit terminal states.** Add `terminal_states: Vec<String>` to `ProjectConfig`
   (`#[serde(default)]`, backward-compatible). Replaces the inferred "done" heuristic
   (`is_terminal_status` = name=="Completed" OR no-op) with an explicit declaration; auto-complete
   and readiness use it. Back-transitions out of a terminal state (reopen) remain expressible via
   the normal `transitions` map.
2. **Export (config -> Mermaid)** + **Workflow page.** A read route + a read-only web "Workflow"
   page that renders the config as a `stateDiagram-v2` (serves as the transition guide / "how do I
   change status"). Also `kanbanr config workflow --to-mermaid`.
3. **Import (Mermaid -> config).** `kanbanr config workflow --from-mermaid <file|->` parses a
   constrained `stateDiagram-v2` and SETS statuses/transitions/default_state/terminal_states in the
   YAML (which stays the truth). Round-trips with the exporter.

## Mermaid conventions (the I/O contract)
- `[*] --> X` => `default_state` (start).
- `X --> [*]` => `X` is a terminal state.
- `A --> B [: label]` => allowed transition A->B (label is advisory, e.g. `reopen`).
- `state "In Progress" as in_progress` => multi-word status names (label is the kanbanr status).
- no-op states: edge label `: no-op` or a `classDef noop` convention (TBD during build).
- Parser accepts the FLAT subset only; reject composite/parallel/history states with a clear error.
- `displayed_states` stays a separate config knob (a view choice, not a transition rule).

## Notes
Self-contained; independent of the other MS-005 items. Gantt (per-project + cross-project) is
tracked separately under FEAT-035 (dates/scheduling) + FEAT-030 (portfolio), reusing the
FEAT-026/027 graph.