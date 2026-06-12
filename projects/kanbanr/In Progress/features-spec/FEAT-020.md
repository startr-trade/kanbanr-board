# Filterable activity streams (P1) — extends FEAT-003

Tag each activity entry with the work item it touched (and its kind once FEAT-006 lands), so one changelog yields many views.

## Scope
- Activity entry gains a `ref` (work-item code) — derived from the write path; `batch` may list several.
- View daemon: `/projects/:p/activity?ref=FEAT-007` and `?kind=chore` filters.
- Web: a project feed + a per-item feed + a **maintenance stream** filtered to ongoing/recurring items, kept out of the feature-delivery feed.
- Depends on FEAT-006 for per-kind; per-item works today.