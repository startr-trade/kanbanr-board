# Process files checked before they are applied

## Problem
A process file can only be checked by applying it: `config workflow --from-file` parses it and the
store validates while saving. The checks live in two places (serde's closed `Check` enum, and the
store's private `validate_gates` inside `set_workflow_with_gates`). Nothing lists the gate
vocabulary, so Claude cannot offer the user the conditions kanbanr can actually check, and the docs'
check table is written by hand.

## Behavior
- `config::validate_workflow(&WorkflowFile)`: one pure validator holding every check the store made
  (statuses, transitions, default/displayed/no-op/terminal states, gates, sign-off names, Zachman
  columns). The store calls it; so does `process check`.
- `kanbanr process check <file|name>`: validates without applying, then prints the working agreement
  and a Mermaid diagram. A bad file exits non-zero and changes nothing.
- `readiness::Check::ALL` with a one-line description each; `kanbanr process checks [--json]` lists
  them with their parameters. The docs' check table is compared with it by `check:docs`.

## Out of scope
Saving processes (the next item).
