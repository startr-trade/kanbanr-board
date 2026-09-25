---
id: ADR-0001
status: accepted
date: 2026-07-02
affects:
- FEAT-015
quality:
- Security
- Maintainability
trade_offs:
- gain: Security
  cost: Flexibility
zachman:
- Who
- Where
layer: conceptual
---

# ADR-0001: No accounts, no auth

## Context

kanbanr is a personal, single-developer tool. An earlier multi-user/JWT model added a server,
logins, and a secrets file for little benefit: the only user was the person running it, and the
only threat model that mattered was leaking their own credentials.

## Decision

We will remove all authentication. The CLI is the sole writer of a local git-backed folder; the
monitor is read-only on localhost. Centralization and access control are delegated to a git
remote, which the user already trusts with their code.

## Alternatives considered

Keeping the JWT model and hiding it behind defaults — rejected, because the complexity stayed in
the code whether or not it was exercised. Adding a single shared password — rejected as security
theatre on a localhost-only daemon.

## Consequences

Far smaller attack surface and no credentials to leak, and sharing reuses the git host. The cost
is flexibility: a genuinely multi-user deployment is now out of scope rather than merely
unconfigured, and exposing the monitor off-localhost becomes the operator's job (reverse proxy
plus TLS).

## Compliance

`SECURITY.md` states the model. The daemon binds 127.0.0.1 by default and exposes no write routes
without `--allow-writes`; `docs/USER_GUIDE.md` carries the reverse-proxy note for anyone who needs
remote access.
