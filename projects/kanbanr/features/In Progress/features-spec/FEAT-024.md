# Open-source release prep

## Problem
The repo needs the scaffolding and the account-level steps that only the owner can do before it can be published.

## Behavior
- Dual MIT/Apache licensing, community files, CI and a release workflow (done).
- The GitHub owner slug and the contact address filled consistently everywhere (done: `startr-trade`, kanbanr-oss-support@startr.trade).
- **kanbanr is not published to crates.io — no crate, not the CLI and not `ears-classifier`.** It is distributed only through GitHub releases: the platform archives, the `install.sh` / `install.ps1` installers, and the GHCR image; from source, `cargo install --path api/crates/kanbanr-cli` after building the web assets. Every crate declares `publish = false`, the release workflow's crates.io job and its `CARGO_REGISTRY_TOKEN` / `PUBLISH_CRATES` settings are removed, and the open-sourcing guide, the VS Code extension's install hint and the docs stop pointing at crates.io. ADR-0009's remark that crates.io carries the CLI is superseded by a short ADR recording this.
- The remaining steps are account-level: create the repo, sweep secrets, make it public, tag v0.1.0, add screenshots.

## Out of scope
Open VSX, npm reservation and MCP packaging, which can follow the first release.
