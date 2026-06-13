# Single-writer daemon

Promote `kanbanr-server` (dispatch is already method+path+body; auth via security.yaml/JWT) to accept writes over a local socket/HTTP, hold projects in memory, serialize all mutations; sessions/agents become thin clients. Move `git::sync_all` (push) off the hot path — debounce/idle or `kanbanr sync`.

See `docs/proposals/enterprise-scale.md` §2.E.2-3.