## Problem

Presets are Rust functions (`default_for`, `togaf_preset`), only `togaf` is recognised by name (anything else silently falls back), and an organisation cannot load its own process.

## Behavior

Presets become embedded YAML with gates. `default` becomes this board's shape (Deferred, Planned, In Progress, Completed, Ongoing + no-ops); the old one stays as `scheduled`; `togaf` gets progressive gates and an Implementation→Operations edge; `pdca`; `design-control` (modelled on ISO 9001 §8.3, never claimed compliant). `config workflow --preset/--from-file/--export`; unknown preset names error. Mermaid export shows gates as notes.

See the design doc `design/process-as-configuration.md`.

## Out of scope

- The Scrum and agile presets (Part 2).