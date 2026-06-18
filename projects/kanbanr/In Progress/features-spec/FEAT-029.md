# Write lock

Every mutation commits+pushes with no lock (`backend.rs:86-98`), so two sessions diverge. Take an OS advisory file lock around mutate->commit (per data-dir or per-project) to serialize concurrent writers.

See `docs/proposals/enterprise-scale.md` §2.E.1.