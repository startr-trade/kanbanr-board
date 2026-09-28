# One board per project, one workspace across boards of equal visibility

## Problem
A data folder is both the portfolio's scope and the sharing boundary, and those want opposite things. Portfolio, cross-project dependencies and `ready`/`blocked` all read one `projects/` directory; the git remote is on that whole directory. So co-locating projects is what makes the cross-project view possible, and is also what forces them to share write access and visibility.

Git has no per-path write control — CODEOWNERS gates review, not push — so a single folder cannot give `kanbanr` and another project different contributor sets.

## Behavior
- **One board repository per project.** Write access is membership of that repository, which is the granularity the git host actually offers.
- **`workspace.yaml` gains a `boards:` list** naming other board folders. The reads that span projects — `portfolio`, `ready`, `blocked`, `graph`, `impact`, `query --all-projects`, and cross-board reference resolution — read every board in the workspace. Writes remain single-board and unchanged.
- **A workspace groups boards of equal visibility.** That is the rule, not a convention: a dependency recorded on a public board names the item it depends on, so pointing at a less-visible project leaks that project's existence. The workspace carries a `visibility:` label so a reader can see which class it is.
- **A reference outside the workspace is unverifiable, not broken.** `doctor` today reports any unresolvable `depends_on` as an error saying it *does not exist*. Under split boards that is false and harmful: a contributor who cannot see `another project` would be told a valid dependency is dangling. Such a reference is reported as external to this workspace, as a warning, and is kept in the graph rather than dropped.
- **Recording a dependency the workspace cannot see is refused by default**, with an explicit override, because it asserts something the author cannot check and may expose a project they did not mean to name.

## Out of scope
Submodules per project — they break the single-writer commit model, since a write inside a submodule leaves the change uncommitted there and only a gitlink in the superproject. Any attempt at path-level access control inside one repository, which git cannot do. Merging boards, or two-way sync between them.