# Workflow stage roles

Gates and actions name statuses, so anything automatic is tied to one process's vocabulary. A design gate written for `System Design` means nothing to PDCA, and a merge on entering `Migration` means nothing to kanban.

Scope:
- A workflow maps statuses to **roles**: `design` (how and where are decided), `build` (code is written on the item's branch), `integrate` (the item is finished and joins the integration line), and `release` (the terminal, in use). A status may have no role, and each role belongs to at most one status.
- Every built-in preset declares its roles. For example, TOGAF: System Design → design, Implementation → build, Migration → integrate, Operations → release. Default kanban: Planned → design, In Progress → build, Completed → integrate and release.
- Gates and actions may name a role instead of a status, so presets and the skill can state rules once.
- `kanbanr process checks` and the working agreement show the roles.
