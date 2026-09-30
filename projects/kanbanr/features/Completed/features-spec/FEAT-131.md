## Problem

Every CI failure so far passed locally first: a monitor test against a binary built without `web/dist`, a macOS symlinked temp path, a Windows link error and then a Windows stack overflow, a mirrored changelog chapter only `docs.yml` compared, and a release job naming a retired runner. Nothing local runs what the workflows run, and once the repository is public every red run is public.

## Behavior

- `make ci` (over `scripts/ci-local.sh`) runs, in a clean copy of the tracked tree at a fixed cache path with its own build cache, every check the workflows run that does not need GitHub:
  - the workflows themselves: YAML parses, **actionlint** (expressions, runner labels, shellcheck of every `run:` block), and every `uses:` reference resolves upstream;
  - `ci.yml`: web (`npm ci`, build, `check:docs`, `check:ui`), Rust (fmt, clippy, the full test suite with the monitor built), installers (TLS backend, shellcheck, `install.ps1` parse, https pins, published targets);
  - `docs.yml`: table of contents, mirrored chapters in sync, `mdbook build`;
  - `release.yml`: the version is releasable, the Docker image builds;
  - FEAT-130's scanners, once they exist.
- Where a workflow step is a script, the harness runs **that step's `run:` block read from the workflow file**, so the local check cannot drift from CI.
- The output ends by naming what it could **not** verify locally: the macOS and Windows legs, uploads and publishing. Those are verified on a private run before anything is pushed to the public repository.
- Tools come from pinned container images where they are not installed (actionlint, PowerShell), as the scan scripts do.

## Out of scope

- Emulating macOS or Windows locally.
