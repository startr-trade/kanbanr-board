# Project charter: purpose, goals, stakeholders (charter.yaml)

## Problem
A project records a one-line `description` and nothing about why it exists. Features cannot link to goals because there are no goal ids, so nothing can check whether work serves anything.

## Behavior
- Per-project `charter.yaml` (the `mirror.yaml` side-file pattern): `purpose`, `goals[{id: G-1, statement, measure}]`, `non_goals[]`, `stakeholders[{name, role, interest}]`, `constraints[]`, `adopted_at`.
- Absent = default, empty = file removed; not part of `Project`, so `GET /projects/{p}` is unchanged. Blank goal ids filled on save.
- `GET`/`PUT /projects/{p}/charter` + commit-message arm; `kanbanr charter show|set --file` (YAML or JSON); `export::charter_to_markdown`.
- Monitor: a Charter tab (purpose, goals with linked-item counts, non-goals, stakeholders, constraints).
- A standing goal (e.g. `G-0` operable and maintainable) lets maintenance trace honestly instead of faking a delivery link.
- Doctor: no purpose; purpose but no goals; goals with no linked items.

## Out of scope
Feature-side goal links (FEAT-047).
