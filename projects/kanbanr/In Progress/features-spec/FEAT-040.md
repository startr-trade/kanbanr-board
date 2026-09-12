# Project docs default to kanbanr

## Problem
Claude sessions on kanbanr-tracked projects tend to write documentation (design notes, decisions, research, runbooks, plans) as markdown files inside the working folder / codebase. That scatters project knowledge outside the system of record.

## Rule
- **Default:** any documentation *about the project* goes into kanbanr docs (`kanbanr doc add <folder>/<name>.md`), organized in doc folders; feature-specific detail goes in the feature spec.
- **Exception — write into the codebase only when:** the user explicitly asks for it there, or the docs are a **deliverable of the codebase** (mdBook / MkDocs / Docusaurus / Sphinx site sources, README, CHANGELOG, LICENSE/CONTRIBUTING/SECURITY, API reference & doc comments, man pages), or tooling requires the file in the repo (e.g. CLAUDE.md).
- **Ambiguous:** default to kanbanr, and say where it was saved (no need to ask each time).
- Never duplicate: a doc lives in exactly one place.

## Where the contract is encoded
- `skill/kanbanr/SKILL.md` — new "Where documentation goes" section + frontmatter description.
- SessionStart hooks (`session-start.sh` / `.ps1`) — one-line reminder in the recovered-state footer.
- `docs/USER_GUIDE.md` — contract bullet.
