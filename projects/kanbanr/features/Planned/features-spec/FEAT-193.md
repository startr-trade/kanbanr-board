# Method on by default in every preset

Every built-in process asks for the same discipline at the same roles, with an opt-out per project:
- **Before build:** the spec has a `Design` section (`spec_sections`), and the person gives a `design-review` sign-off.
- **Before integrate:** the docs the item declares are updated (`docs_updated`), and the person gives a `docs-folded` sign-off.
- **Everywhere:** references in specs, docs and ADRs are live links, checked by doctor.

`kanbanr config method --off` (or per gate) turns these off.
