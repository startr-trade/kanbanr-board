# ADR-0001: No accounts, no auth

**Status:** accepted

**Context.** kanbanr is a personal, single-developer tool. An earlier multi-user/JWT model added
a server, logins, and a secrets file for little benefit.

**Decision.** Remove all auth. The CLI is the sole writer of a local git-backed folder; the monitor
is read-only on localhost. Centralization and access control are delegated to a git remote.

**Consequences.** Far smaller attack surface, no credentials to leak, and sharing reuses the git
host you already trust. Exposing the monitor off-localhost is the operator's job (reverse proxy).
