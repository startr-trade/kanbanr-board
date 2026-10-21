# A diagram opened from the book draws as black boxes

## Why
Reported 21 Oct 2026: a diagram opened full size from the book ("open in a new tab") has no
clarity. Reproduced headless on the architecture overview in the coal theme: every shape is solid
black, the labels are gone, and the page behind it is the browser's white.

Two causes, both in `docs/diagram-open.js`, which [FEAT-203](/p/kanbanr/feature/FEAT-203) retargeted
from Mermaid to Pele without checking the opened tab:
- It removes the SVG's `style` attribute (Mermaid put sizing there). Pele puts the diagram's own
  colour variables there (`--_bg`, `--_fg`, `--_s`, `--_b`, … each from a `--pele-*`), and every
  shape and label refers to them (`fill="var(--_s)"`), so without them they fall back to black.
- It takes the tab's background from `document.body`, which mdBook leaves transparent (its colour
  is on `<html>`).

## Design

### Change (`docs/diagram-open.js`)
- Keep the clone's `style`; drop only the sizing in it (`max-width`, `height`, `width`), so the
  standalone copy fills the tab and keeps Pele's variables.
- Carry the theme's resolved `--pele-*` values onto the clone, as now.
- Take the tab's background and text colour from the diagram's resolved `--pele-bg` and `--pele-fg`,
  falling back to `<html>`'s background and `<body>`'s colour, then white and dark grey.

### Test plan
| Req | Test |
|---|---|
| R-1 | `manual: a diagram opened from the book draws in its theme` (headless: capture the HTML the tab would open, in light and coal, render it, and look) |

### Implementation tasks
1. The two changes above; the manual check in light and coal. Depends on: none.

### Affects docs
None (the book's behaviour only).
