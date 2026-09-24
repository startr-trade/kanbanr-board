# Surfacing and search

## Problem
`kanbanr feature show` is the markdown export and is Claude's whole view of an item, so anything not rendered there is invisible. Troubleshooting is worse: `query --full-text` searches only item titles and specs, while the graph now also holds requirements, tests, docs, ADRs, lessons and retros — and a hit without its context does not help.

## Behavior
- `export::to_markdown` gains `## Definition` and `## Requirements` sections, rendered only when a definition is present so legacy output stays byte-identical.
- **One address space** — every node is addressable in the same grammar the commit trailers use: `G-2`, `FEAT-043`, `FEAT-043/R-2`, `FEAT-043/R-2#test-name`, `ADR-0003`, `design/mirror.md`. Search returns addresses; every other command accepts one.
- **Search across the graph**: items, requirements, tests, docs, ADRs, lessons, retros; results grouped by type with counts, each hit showing the path up to its goal.
- **Drill-down is composable, not a mode**: each result line is the next query — `--in requirements`, `--goal G-2`, `--gap test`, `--since 14d`, then `kanbanr trace <address>` downward or `kanbanr why <path>` upward.
- **Structured troubleshooting filters** on the same command: `--goal`, `--quality`, `--violates`, `--adr`, `--gap why|test|approval` (requirements with no green test or stale `checked_rev`, items serving no goal, goals with no items, scope added after approval, defects introduced_by an item including fix-induced chains). `--json` throughout.
- Monitor sections (not new pages): Definition grid with gap chips and a Requirements section (EARS, ISO badges, quality scenario, TDD badges) on the feature page; a 'no definition' chip on non-terminal board cards; a 'Needs attention' panel on the Board; and ONE global search box with facet chips that narrow live, each row expanding in place to reveal parents/children.

## Out of scope
A search index (the board is ~580 KB, so brute-force scanning is instant) and an interactive TUI browser — composable commands plus expandable results cover it. A page per data type: the Charter page (FEAT-046) qualifies; NFR/EARS/approval/lessons/ADR/retro views are sections, filters or documents; the Zachman matrix ships as `trace --zachman` output; a Traceability page is built only if `kanbanr trace` proves it is reached for.
