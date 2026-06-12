# Collapse to single-user auth (P0, decided)

Local mode + git-remote access control make the per-user account model redundant for a personal tool. Remove it.

## Scope
- security.yaml -> a single optional `access_token` (header-gated; open on localhost).
- Drop JWT/users/view-operate/admin/login-profiles/email-fingerprint.
- Server commit identity = git config (same `kanbanr identity` as local mode).
- Access control for collaboration is delegated to the git remote.
- Supersedes FEAT-004 (token refresh) — a static token needs no refresh.
- Rewrite the integration test for the simplified model.