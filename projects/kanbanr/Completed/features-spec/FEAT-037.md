# Versioning, access scope, doctor

Add `schema_version` + migration step. Decide multi-team access: monorepo + daemon-auth vs per-project git repos/submodules. `kanbanr doctor` validates the portfolio-wide graph (dangling cross-project refs, orphans).

See `docs/proposals/enterprise-scale.md` §2.A.4 / §2.G.