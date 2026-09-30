---
id: ADR-0011
status: accepted
date: 2026-09-30
deciders:
- Venkatraman B
affects:
- FEAT-024
- FEAT-092
driven_by:
- FEAT-024/R-5
zachman:
- where
- how
layer: physical
---

# kanbanr ships only as GitHub releases; ears-classifier is the one published crate

## Context

ADR-0009 put the monitor inside the binary and, because a published crate cannot carry the built
web assets, noted that crates.io "carries the CLI" while the release archive carries the complete
binary. The open-sourcing guide, the release workflow's comments and the VS Code extension went
further and told people to `cargo install kanbanr`. A crate that installs a binary without its
monitor is a worse first experience than no crate (G-5), and publishing `kanbanr-core` would
promise an API stability nobody means to owe. `ears-classifier` (FEAT-092) is different: it is
useful to people who will never run kanbanr, and its name is confirmed free on crates.io.

## Decision

We distribute kanbanr only through its GitHub releases: the platform archives, the `install.sh` /
`install.ps1` installers, and the GHCR image; from source, `make install` builds the web assets
and installs the binary. `kanbanr-cli`, `kanbanr-core` and `kanbanr-server` declare
`publish = false`. `ears-classifier` is the one crate published to crates.io, by the release
workflow's `crates` job once `PUBLISH_CRATES=true` and a token or Trusted Publishing are set.
This replaces ADR-0009's remark about crates.io; the rest of ADR-0009 stands.

## Alternatives considered

- **Publish `kanbanr-cli` without the monitor.** Lost: `cargo install kanbanr` would hand out a
  binary whose `serve` explains that its UI is missing — the failure ADR-0009 set out to avoid.
- **Commit `web/dist` so the crate carries it.** Already rejected in ADR-0009: generated files in
  history, and the UI on crates.io, which the maintainer did not want.
- **Publish nothing, not even `ears-classifier`.** Lost: the library is the part of kanbanr that is
  useful on its own, which is why FEAT-092 extracted it.

## Consequences

- One way to get kanbanr, and it is always complete: archive, installer or image.
- No `kanbanr` crate name is held on crates.io; someone else could take it. Accepted: the name that
  matters for installation is the GitHub repository.
- Users with only a Rust toolchain build from a clone (`make install`), not `cargo install`.

## Compliance

`cargo metadata` reports `publish: []` for every kanbanr crate, so `cargo publish` of one of them is
refused; `release.yml` runs `cargo publish -p ears-classifier` and nothing else; FEAT-024/R-5's
check greps the tracked docs for `cargo install kanbanr`.
