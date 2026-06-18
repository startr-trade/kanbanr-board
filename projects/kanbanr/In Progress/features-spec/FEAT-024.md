# Open-source release preparation

Make kanbanr publishable as a personal OSS project.

## Done
- Dual-licensed **MIT OR Apache-2.0** (LICENSE-MIT, LICENSE-APACHE; workspace Cargo.toml + per-crate description/repository).
- Community files: CONTRIBUTING, SECURITY (no-auth model), CODE_OF_CONDUCT (Contributor Covenant), CHANGELOG, THIRD_PARTY.
- .github: issue templates (bug/feature/config), PR template, dependabot, release.yml (cross-platform binaries + GHCR image + guarded crates.io publish).
- docs/OPEN_SOURCING.md rewritten: accounts/keys/credentials walkthrough (GitHub/crates.io/GHCR/VS Code Marketplace/Open VSX/npm; 2FA, scoped tokens, trusted publishing), checked-off created files, fixed stale auth references.
- Reproducible screenshot tooling: tools/screenshots/ (Selenium Grid in Docker + Rust thirtyfour client); 11 PNGs in docs/images/ embedded in README (light portrait frames + board full-height + dark board/feature showcases). `make screenshots`.

## Remaining (manual — user only)
Reserve names, create accounts/tokens, fill <owner> + copyright/email placeholders, cut v0.1.0.