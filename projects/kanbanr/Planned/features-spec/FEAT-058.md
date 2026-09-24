# Rust edition 2024, toolchain pin and MSRV

## Problem
The workspace is on edition 2021. Local is rustc 1.96, Docker pins `rust:1.95-slim-bookworm`, and CI floats on `dtolnay/rust-toolchain@stable`, so the three can drift apart — which matters more now that contributors meet the same bar. There is no declared MSRV, which the planned crates.io publish (FEAT-024) will want.

## Behavior
- `cargo fix --edition`, then `edition = "2024"` in the workspace manifest.
- Add `rust-toolchain.toml` pinning the channel so local, Docker and CI agree.
- Declare `rust-version = "1.85"` (the edition-2024 floor).
- Read the `if let` sites around the advisory write lock in `kanbanr-cli/src/backend.rs` by hand: edition 2024 drops scrutinee temporaries earlier, which is the one behavioural change `cargo fix` will not reason about for us.
- Adopt let-chains where they remove real nesting (~118 `if let` sites), not as a blanket rewrite.

## Out of scope
Bumping the Docker base past bookworm — the glibc pin exists so the binary runs on bookworm and newer (see the Dockerfile comment).
