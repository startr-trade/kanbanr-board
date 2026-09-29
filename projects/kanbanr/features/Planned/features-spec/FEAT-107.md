## Problem

Every page renders inside `.content`, capped at `max-width: 1200px`. The board lays its columns out at `minmax(240px, 1fr)` each, so any workflow with more than four displayed statuses — TOGAF's six phases, in katalog — needs about 1,550px and scrolls horizontally inside a 1,200px box, while a wide screen shows empty margins on both sides.

## Behavior

The board (and the portfolio board, which lays out the same way) uses the full window width; reading pages — specs, docs, the charter — keep the 1,200px measure, which is there for line length. Columns still scroll sideways only when the window itself is too narrow for them.

## Out of scope

- Changing column widths or card design.