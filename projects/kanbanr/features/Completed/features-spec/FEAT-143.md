# Defect: the v0.1.0 release fails its installer check, and skips crates.io

## Problem
The v0.1.0 Release run published every binary, the image and the release, then failed
"verify the installer" on both containers: `--version does not name the released commit`, although
it does. The step runs in a container job, whose default shell is `sh` (dash), and uses the bash
substring `${GITHUB_SHA:0:12}` — dash stops with "Bad substitution", and `|| { … }` turns that into
the misleading message. `make ci` never ran the step (it installs from a published release), and
actionlint shellchecks container steps as bash, so nothing local caught it.

The crates job was skipped: `PUBLISH_CRATES` was created as a repository *secret*, but the job's
condition reads `vars.PUBLISH_CRATES`, a *variable*. A secret is invisible to `vars`.

## Behavior
- The commit check takes its 12 characters with POSIX `cut`, so it runs under any `sh`.
- `make ci` shellchecks the run blocks of container jobs without `shell: bash` as POSIX `sh`.
- `make ci` reports a workflow `vars.NAME` that the repository holds as a secret instead of a variable.
- The release docs say PUBLISH_CRATES is a *variable*, and how to re-run the release.

## Out of scope
Re-running the release itself — the maintainer pushes and re-tags.
