## Problem

A board with a remote is meant to be pushed once ten unpushed commits have piled up (FEAT-034, the `debounce` default). The CLI never does: the count lives in the process's memory, each `kanbanr` command is a new process that commits once and exits, so the count restarts at zero every time. kanbanr's own public board drifted 58 commits behind GitHub without a word. And the only way to choose how a board is pushed is the `KANBANR_PUSH` environment variable — invisible, easy to lose between shells, and not something `kanbanr` can show or set.

Worse, it could not have pushed if it tried. `kanbanr sync` against GitHub fails with "unsupported URL protocol": the git library is built without its network transports (`default-features = false`, and neither the `ssh` nor the `https` feature switched back on), so a board can sync only with a remote on the local disk — which is all the tests ever used. After the failed push, `sync` then cleared its "unpushed" marker anyway and reported "nothing to sync (no local commits pending)" with the board 58 commits ahead.

## Behavior

- **Remotes over SSH and HTTPS work**: the git library is built with its `ssh` and `https` transports. SSH authenticates through the user's agent, then their default key; HTTPS through git's credential helper, as now.
- **A failed push leaves the board marked unpushed**, and `kanbanr sync` reports what it did: pushed, nothing to push (judged by commits ahead of the remote, not a marker), or failed — with the error and the git commands to finish by hand, and a non-zero exit.
- **A test pushes to a real remote protocol**, not only a folder on disk: an SSH or HTTP git server in a container.

- **The count comes from git**, not memory: the commits the board is ahead of its remote, so it carries across commands. A debounced board pushes when that reaches the threshold.
- **The policy is a board setting**, kept in the board's own git config (`kanbanr.push`) beside its commit identity: machine-local and never pushed, because how often a machine pushes is that machine's choice — not the code repository's `.kanbanr` marker, which is committed and shared with every contributor.
  - `kanbanr remote push-policy` shows it and where it came from; `kanbanr remote push-policy auto | off | debounce[:N]` sets it.
  - Precedence: `KANBANR_PUSH` (a one-off override) → the board's setting → the default (debounce, every 10).
- `kanbanr sync` is unchanged: push now, whatever the policy. `kanbanr doctor` warns when a board with a remote is more than the threshold behind it.
- The docs describe the setting; `KANBANR_PUSH` is documented as the override.

## Out of scope

- Pushing the code repository: kanbanr never does.
