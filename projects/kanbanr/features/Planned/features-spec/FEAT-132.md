## Problem

The first supply-chain audit (FEAT-130's gate, run locally) finds advisories in what kanbanr ships and in what it builds with:

- **Rust, shipped:** `rustls` 0.23.40 (RUSTSEC-2026-0285, TLS 1.3 handshake messages accepted across encryption levels; fixed in 0.23.45), `anyhow` 1.0.102 (RUSTSEC-2026-0190, unsound `downcast_mut`; fixed in 1.0.103), `git2` 0.19.0 (three unsound APIs: RUSTSEC-2026-0008, -0183, -0184; fixed in 0.20.4 / 0.21.0).
- **Rust, tests only:** `testcontainers` 0.23 pulls `tokio-tar` 0.3.1 (RUSTSEC-2025-0111, PAX header smuggling, no fixed release) and the unmaintained `rustls-pemfile` (RUSTSEC-2025-0134).
- **Web, shipped in the monitor:** `dompurify` ≤3.4.12 (XSS and config pollution), `mermaid` ≤11.16.0 (prototype pollution, CSS injection, DoS), `react-router` ≤7.17.0 (open redirect) — all fixed by compatible updates.
- **Trivy, beyond the audits:** `docker/Dockerfile` runs as root (DS-0002, HIGH) and has no `HEALTHCHECK` (DS-0026, LOW); `tools/screenshots/Cargo.lock` (the screenshot tool, not shipped) carries `quinn-proto` 0.11.14 (GHSA-4w2j-m93h-cj5j, HIGH; fixed in 0.11.15); and Trivy's database says `react-router` needs 7.18 for one of its advisories, a major upgrade from the 6.30 the monitor uses.
- **Web, build tools only:** vite, esbuild, postcss, nanoid, browserslist. Not shipped; the gate audits production dependencies only.

## Behavior

- `cargo update` takes `rustls` and `anyhow` to their fixed releases.
- `git2` moves to 0.21 (and its libgit2), with whatever API changes that needs.
- `testcontainers` moves to its current release, which no longer depends on `tokio-tar` or `rustls-pemfile`; if a finding remains with no fix, it is suppressed time-boxed with its reason, as FEAT-130 requires.
- The web app takes the compatible fixes for `dompurify`, `mermaid` and `react-router`.
- The image runs as an unprivileged user and declares a `HEALTHCHECK` against the daemon's health endpoint.
- The screenshot tool's lockfile takes the fixed `quinn-proto`.
- If `react-router` 6.30.x has no fix for an advisory, the monitor moves to the fixed release, or the finding is suppressed time-boxed with the reason it does not apply to how the monitor uses the router — whichever the advisory's details support.
- Behaviour is unchanged: `make ci` stays green, and `make scan-deps` reports nothing outside `.trivyignore.yaml`.

## Out of scope

- Build-tool upgrades (vite 8 and friends): not shipped, a separate item.
