# Stop hook reminder never reaches Claude

## Problem
`stop-check.sh`/`.ps1` printed the record-your-work reminder to stderr and exited 0. Claude Code does not pass a Stop hook's output to Claude in that case (it only shows in the transcript view), so the nudge had no effect.

## Fix
When a reminder is due, print `{"decision":"block","reason":"…"}` so Claude sees the reason, records unrecorded work (or says there is nothing to record) and stops. To avoid noise and loops, a reminder is due only when all hold:
1. the board's last commit is older than the window (default 30 min);
2. the project shows work since then: uncommitted changes (marker aside) or a newer commit; outside a git repo, staleness alone;
3. no reminder in this session within the window (per-session timestamp in the temp dir);
4. not already continuing because of a Stop hook (`stop_hook_active`).
