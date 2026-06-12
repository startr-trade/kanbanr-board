# Remote sync safety (P1)

Ensure no data loss when syncing to remotes. The change is always committed locally first (so it's safe), but a failed push/conflict is silent today.

## Scope
- CLI warns (with exact `git pull/push` resolution commands) when a sync can't complete.
- USER_GUIDE/SKILL guidance: conflicts are resolved with normal git in the data folder; nothing is lost.