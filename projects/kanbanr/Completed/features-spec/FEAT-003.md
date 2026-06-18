# Recent activity view (P1) — per-project changelog files

Each write appends to `projects/<p>/activity.yaml` (a capped, newest-first list of {time, actor, message}); the monitor's project page renders it. Plain data in the data folder (no git plumbing needed); actor = the git identity. Works in local + server mode.