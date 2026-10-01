## Problem

A sprint's burndown counts an item as finished when it first reaches the workflow's end status. In the `scrum` preset that is **Released**, reached only when `release cut` ships it, so a sprint burns down nothing until release day and then drops in one step — while Scrum's Definition of Done, and the team's sense of a finished item, is the **Done** column. Closing a sprint has the same blind spot: an item that is Done but not yet released counts as unfinished and is carried over.

## Behavior

- A workflow can mark a stage as **counting as done for the cadence views**: in its gate, `done: true`. An item counts as finished — for the burndown, the sprint's done total, and what a closing sprint carries over — from the first time it reaches a marked stage, or an end status.
- With no stage marked, nothing changes: the end statuses count, as today.
- The `scrum` preset marks **Done**. The working agreement it renders says so beside the Definition of Done.
- `config workflow --export` shows the mark; validation accepts it only on a declared status.

## Out of scope

- Releases: `release cut` already ships the items that are Done.
