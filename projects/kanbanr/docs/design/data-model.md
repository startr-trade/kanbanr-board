# Data model

Everything is human-readable files under `data/projects/<name>/`:

| File | Holds |
|------|-------|
| `config.yaml` | statuses, allowed transitions, displayed/no-op states |
| `features/FEAT-*.yaml` | a feature item: spec, status, milestone, todo-lists, fields |
| `milestones/MS-*.yaml` | a milestone and its `depends_on` (a DAG) |
| `activity.yaml` | the per-project changelog (newest first) |

A **feature item** is an epic: a markdown specification plus one or more persistent **todo-lists**
whose tasks are tri-state. When every task is done the feature auto-advances to Completed.
