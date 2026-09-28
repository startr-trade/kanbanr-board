## Problem

Commit c5b38a5 (FEAT-065) replaced `skill/kanbanr/hooks/session-start.sh` (89 lines) and `stop-check.sh` (135 lines) with `#!/bin/sh\nexit 0` — the stub the tests write into their fake skill folder. Since 2026-09-28 no session recovers the board at start and no turn is nudged to record work, on every machine, while `kanbanr hooks status` reports both as ✓ because the files exist. The `.ps1` versions are untouched.

## Behavior

- Restore both scripts from c5b38a5^ (which already carries the FEAT-054/FEAT-055 additions).
- A test asserts the shipped scripts are the real ones, so a stub cannot be committed over them again unnoticed.

## Out of scope

- Changing what either hook does.