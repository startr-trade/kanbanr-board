# Patch releases

Fixes to a release that is already in production need their own release: a branch from the cut release's tag, the defect items merged into it, tested through the stages, then promoted like any release.

Scope:
- `kanbanr release add <VERSION> --patch-of <PARENT>` creates a release with a `parent` reference, and creates its branch `release/<VERSION>` from the parent's tag.
- The patch release lists its parent's items as included, and its own items (typically defects) as added.
- Release notes show the parent and what the patch adds.
- Fixes merged into a patch release are also reported for forward-merging into the integration branch, so the next release does not lose them.
