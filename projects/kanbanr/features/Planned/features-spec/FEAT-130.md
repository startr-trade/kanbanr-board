## Problem

CI builds and tests, but nothing looks for vulnerable dependencies, committed secrets, insecure code or a vulnerable release image, and the licence check `THIRD_PARTY.md` promises (`cargo deny`) never runs. With Dependabot version updates removed, dependency risk has to be surfaced another way. CI also runs twice for every pull-request branch (a `push` run and a `pull_request` run), never cancels superseded runs, and runs the macOS leg — billed at ten times the Linux rate on a private repository — on every push to every branch.

## Behavior

**Security scanning**
- `codeql.yml`: CodeQL on push to `main`, on pull requests to `main`, and weekly, for **Rust, JavaScript/TypeScript** (the monitor and the VS Code extension) **and the workflows themselves** (`actions`, which catches script injection from PR titles and bodies). A shared `codeql-config.yml` keeps test code out of scope.
- `trivy.yml`: a Trivy filesystem scan (dependencies in `Cargo.lock` and both `package-lock.json`, committed secrets, Dockerfile misconfiguration) on push, pull request and weekly; every severity reported to code scanning.
- `release.yml`: the release image is scanned **before it is pushed**, and a HIGH or CRITICAL finding that has a fix stops the push — instead of a separate job rebuilding the image only to report on it.
- A **supply-chain** job in `ci.yml`: `cargo deny check` (licence allowlist matching `THIRD_PARTY.md`, sources, bans, advisories) and `cargo audit`, plus `npm audit --omit=dev` for the web app; these fail the build.
- **Suppressions are time-boxed**: `.trivyignore.yaml` entries carry a written reason and an expiry date, and CI refuses an entry without either.
- **Private-repository safety**: code-scanning uploads need GitHub Advanced Security on a private repository; until the repository is public they are skipped instead of failing the run.
- **Local parity**: `make audit`, `make scan-deps` and `make codeql` run the same checks before a push (`scripts/security-scan.sh`), and fail on any finding.

**Run hygiene**
- CI runs on push to `main` and on pull requests only — one run per change, not two — with superseded runs cancelled.
- Every third-party action is pinned to a full commit SHA (with its version in a comment) and updated deliberately; a CI check refuses a `uses:` that is not pinned.
- Fork pull requests from first-time or outside contributors need a maintainer's approval before any workflow runs (a repository setting; documented in the open-sourcing guide).

## Out of scope

- Fixing what the first scans find: each finding becomes its own item.
- Requiring code-scanning results in the `main` ruleset (a repository setting, after the first scans are clean).
