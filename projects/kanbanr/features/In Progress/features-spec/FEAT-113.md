## Problem

The only guardrails are hard-coded: approval on any move into an active status, readiness at finish. A process (TOGAF, PDCA, an organisation's QMS) cannot say what each stage requires.

## Behavior

`gates` in the workflow config, keyed by status: `purpose`, `requires`, `warns`, `signoffs`, `enforce: block|warn`, `kinds`, `on_enter`. Validated by `set_workflow`. With no gates, `effective_gates` synthesises today's rules exactly (golden-tested), including the "Completed" terminal fallback. Moves evaluate the target gate; `--override "<reason>"` (alias `--unapproved`) passes and is recorded in the transition history. `schema_version: 3` is stamped only when gates exist. Status is read from the record, identity is recorded as given, codes are opaque keys.

See the design doc `design/process-as-configuration.md`.

## Out of scope

- Sign-offs (separate item), presets (separate item).