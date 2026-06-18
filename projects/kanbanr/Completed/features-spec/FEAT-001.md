# Local / serverless mode (P0)

Make the **server optional**. The CLI should talk to `kanbanr-core`'s store directly against the local data dir and commit via vendored git, with **no server running**. The server is then only needed for the live web monitor.

## Scope
- `--local` flag / `KANBANR_LOCAL=1`, or auto-detect (no `KANBANR_SERVER_URL` + a data dir present).
- When a server IS configured, keep using it (monitor stays consistent).
- Local identity for commits via `kanbanr config identity --name --email` (no login needed).

## Why
Turns kanbanr from 'run a service' into 'a CLI with an optional dashboard' — the right shape for a personal tool. **Highest-leverage change.**