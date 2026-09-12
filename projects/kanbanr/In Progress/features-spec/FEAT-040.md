# Project docs default to kanbanr

## Problem
Claude sessions on kanbanr-tracked projects tend to write documentation (design notes, decisions, research, runbooks, plans) as markdown files inside the working folder / codebase. That scatters project knowledge outside the system of record.

## Rule
- **Default:** every document, whether the user requested it or Claude created it on its own initiative, goes into kanbanr docs (`kanbanr doc add <folder>/<name>.md`), organized in doc folders; detail for one piece of work goes in that feature's spec.
- **Exception:** the doc goes in the project folder **only when the user asks** for it there, typically a deliverable such as a hand-rolled mdBook / MkDocs / Docusaurus / Sphinx site, README, CHANGELOG, contributor or API docs. Keeping such a user-requested deliverable in sync with later code changes is covered by that request.
- Code comments / doc comments are part of the code, not documents, so the rule doesn't cover them.
- **Don't ask each time:** default to kanbanr and state where the doc was saved.
- **One home per doc:** never duplicate; link to the kanbanr doc path instead.

## Where the contract is encoded
- `skill/kanbanr/SKILL.md`: "Where documentation goes" section + frontmatter description.
- SessionStart hooks (`session-start.sh` / `.ps1`): reminder in the recovered-state footer.
- `docs/USER_GUIDE.md`: contract bullet.
