# Batch loads project once

`store.rs::apply_batch` currently reloads the whole project per sub-op (a K-op bundle ≈ K+ full loads). Refactor to load one mutable `Project`, apply all ops in-memory, validate once, persist only changed files.

See `docs/proposals/enterprise-scale.md` §2.D.1.