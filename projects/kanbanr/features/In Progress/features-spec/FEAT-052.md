# Method, docs, contribution bar and dogfooding

## Problem
The tooling is inert unless the skill demands the content, and kanbanr's own board would stay an example of the problem it describes.

## Behavior
- SKILL.md: charter at activation; the one bar with kind-specific shapes; every item states why, links a goal, carries requirements and test evidence; ask ONE clarifying question rather than guessing; leave unknowns blank for doctor; the approval contract (define -> brief -> approval -> code) including the subagent rule; tests-first state flips; the traceability and ADR rules.
- USER_GUIDE, DESIGN note recording the inline-vs-side-file decisions, CHANGELOG.
- CONTRIBUTING: the same bar for everyone, one fully worked example, the pre-adoption note; a PR template carrying the definition YAML; `kanbanr check --file` so CI validates without board access.
- The method document stored as a kanbanr doc.
- Dogfood: kanbanr's charter written; FEAT-014/018/019/024 defined.

## Out of scope
Backfilling the 40 completed items.
