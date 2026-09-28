# The project root mixes kinds of thing with states of one thing

## Problem
A project folder holds nine status directories — `Planned/`, `In Progress/`, `Completed/`, `Deferred/`, `Scheduled/`, `Ongoing/`, `No Action/`, `Not Applicable/`, `Out-of-Scope/` — beside `milestones/` and `docs/`. Nine of the eleven directories are states of a single entity, sitting at the same level as entirely different entities. Adding a status adds a root directory, and the root grows with the workflow rather than with the model.

## Behavior
- Item files move to `features/<Status>/FEAT-001.yaml`, with their specs at `features/<Status>/features-spec/FEAT-001.md` as now. The project root then holds a stable five: its own settings files, `features/`, `milestones/`, the log folders, and `docs/`.
- A status move relocates within `features/`; nothing else about the store changes.
- Migration on first write, with reads accepting both shapes until then — the same discipline the log restructure uses. No file is deleted before its replacement is written.
- `kanbanr index` rebuilds correctly from either shape.

## Out of scope
Renaming the spec subfolder, or flattening status into a field instead of a folder. Status-as-folder is what makes the board greppable and is not in question here.