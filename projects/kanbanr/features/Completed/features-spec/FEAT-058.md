# Rust edition 2024, toolchain pin and MSRV

## Problem
The workspace is on edition 2021. Local is rustc 1.96.0, Docker pins `rust:1.95-slim-bookworm`, and CI floats on `dtolnay/rust-toolchain@stable`, so the three drift apart — which matters more now that contributors meet the same bar. `rustup check` reports stable 1.98.1 (2026-09-01) available. There is no declared MSRV, which the planned crates.io publish (FEAT-024) will want.

## Behavior
- Update local to stable 1.98.1 (`rustup update stable`; rustup itself 1.29.0 -> 1.29.1).
- Add `rust-toolchain.toml` pinning 1.98.1 so local, Docker and CI agree, bumped deliberately as a chore rather than drifting.
- Docker base to `rust:1.98-slim-bookworm` — keeping **bookworm**: the pin exists because building on trixie links glibc 2.39 and then fails at runtime on bookworm (see the Dockerfile comment). Expect one slower image build as the cargo-chef layer re-cooks.
- `cargo fix --edition`, then `edition = "2024"` in the workspace manifest.
- Declare `rust-version` as the minimum that actually COMPILES — 1.85 for edition 2024, or 1.88 if let-chains are adopted. Not 1.98: MSRV is a promise to consumers, not a statement of the development toolchain.
- Read the `if let` sites around the advisory write lock in `kanbanr-cli/src/backend.rs` by hand: edition 2024 drops scrutinee temporaries earlier, the one behavioural change `cargo fix` will not reason about.
- Adopt let-chains where they remove real nesting (~118 `if let` sites), not as a blanket rewrite.

## Out of scope
Moving the Docker base past bookworm.
