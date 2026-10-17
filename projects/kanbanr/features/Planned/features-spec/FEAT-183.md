# Release stages and promotion

Today a release is planned or cut. A team that deploys a release branch to test and staging environments before production has nowhere to record where the release is, and the cut, which is the production event, does nothing to the code repository beyond an optional tag.

Scope:
- **A release has a current stage.** It is configurable per project, with a default list of `candidate` → `test` → `staging` → `production`. The stage is recorded with who moved it and when, as history.
- **`kanbanr release promote <VERSION> <stage>`** moves a release to the next or a named stage. Moving to `production` is the cut: it ships the finished items, writes the notes, tags the code repository, and merges the release branch into the main branch. If the merge cannot be clean, it refuses rather than forcing.
- **Candidate creates a branch.** Promoting to `candidate` (or `release add --branch`) creates `release/<VERSION>` from the integration branch the project names.
- **Operations follows the cut.** Items enter the project's terminal status only through the production stage of a release they are planned into. The existing `in_release` gate check plus the cut cover this; the docs say so.
