## Problem

`claude plugin validate .` fails on the repository, so the plugin cannot be installed from the marketplace:

- `plugin.json` lists its skill as `${CLAUDE_PLUGIN_ROOT}/skill`. The `skills` field takes a path relative to the plugin root (`./skill/`); the variable is only expanded in hook commands, so the validator reports "Path not found" and the loader would fail.
- Both manifests carry `_comment…` keys, which the validator reports as unknown fields.

The manifests are also stale: the plugin's description says the binary "ships separately via crates.io" (it does not, ADR-0011), its licence says `Apache-2.0` (the project is `MIT OR Apache-2.0`), and the open-sourcing guide tells users to run `claude plugin marketplace add <github-owner>/kanbanr` with the placeholder still in it. Nothing checks the manifests, which is how this shipped.

## Behavior

- `skills` is `["./skill/"]`; the explanatory `_comment…` keys move into a short `.claude-plugin/README.md`.
- The descriptions say where the binary comes from (the GitHub release installers) and what the plugin bundles; the licence is `MIT OR Apache-2.0`.
- The install instructions name the real marketplace: `claude plugin marketplace add startr-trade/kanbanr`, then `claude plugin install kanbanr@kanbanr`.
- `make ci` runs `claude plugin validate .` where the `claude` CLI is installed, and says it skipped it where it is not.

## Out of scope

- Which hooks the plugin bundles (it registers the session, stop and summary hooks; the commit and docs guards come from `kanbanr hooks install`).
