# Diagrams drawn by Pele, themed like the book and the monitor

## Why
The user asked on 20 Oct 2026 for Mermaid diagrams to be rendered with
[Pele](https://pele.run) (MIT, by Obsidian), themed to match the mdBook theme. Today the book ships
`mermaid.min.js` (2.5 MB) through the `mdbook-mermaid` preprocessor, and the monitor bundles Mermaid
(about 1 MB of chunks). Pele renders Mermaid 12.1 syntax to SVG whose colours are CSS variables, so
one stylesheet makes every diagram follow the reader's theme without re-rendering. Measured before
this item: all 9 docs diagrams and the monitor's live state and gantt diagrams render with Pele
1.7.0, 1–23 ms each.

## Design

### Decisions (20 Oct 2026, by the user)
- Rendered **in the browser** (the book and the monitor), not at build time.
- **Both** the docs and the monitor.
- Pele pinned **exactly at 1.7.0** (no ranges), locked, covered by `npm audit`; updating it is a
  deliberate change re-checked against every diagram.
- The docs check renders every diagram **with Pele** (the same pinned version) instead of
  Mermaid's parser.

### The book
- Remove `mdbook-mermaid` (`[preprocessor.mermaid]`), `docs/mermaid.min.js` and
  `docs/mermaid-init.js`.
- `docs/pele.global.js`: Pele 1.7.0's browser build, copied from `web/node_modules/pele` by a
  script (`tools/docs/pele.sh`) and committed, so building the book needs no npm; CI checks the
  committed copy equals the pinned package.
- `docs/pele-init.js`: on load, every `pre > code.language-mermaid` becomes a `div.diagram` holding
  Pele's SVG (`mount`, so it fits the column); a block Pele cannot render shows the source and the
  error, never a blank.
- `docs/pele-theme.css`: maps Pele's variables to mdBook's, so the five themes (light, rust, coal,
  navy, ayu) and theme switching apply: `--pele-bg: var(--bg)`, `--pele-fg: var(--fg)`,
  `--pele-muted: var(--icons)`, `--pele-line: var(--fg)`, `--pele-surface: var(--quote-bg)`,
  `--pele-surface-alt: var(--table-alternate-bg)`, `--pele-border: var(--table-border-color)`,
  `--pele-accent: var(--links)`, `--pele-font: var(--main-font, inherit)`.
- `diagram-open.js` (open a diagram full-size) and the overflow rules of `mermaid-fix.css` are kept,
  retargeted from Mermaid's markup to `div.diagram`; the Mermaid-specific rules go.

### The monitor
- `web/src/components/Markdown.tsx` renders `code.language-mermaid` with Pele's `render`, the SVG
  through the existing `safeSvg` sanitiser; the Workflow and Gantt pages go through the same
  component, as now.
- The monitor's light and dark palettes map onto Pele's variables in `styles.css`.
- `mermaid` is removed from `web/package.json`; `pele@1.7.0` added (exact).

### Checks
- `check:docs` (`web/scripts/check-mermaid.mjs` → `check-diagrams.mjs`) renders every block in
  docs/src, README.md and SKILL.md with Pele; any that throws fails CI, naming file and block.
- `check:markdown` keeps its sanitiser test with Pele's SVG.
- A check that `docs/pele.global.js` is byte-identical to the pinned package's build.
- [FEAT-200](/p/kanbanr/feature/FEAT-200)'s diagram validation should use the same Pele.

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `check:docs` — every docs diagram renders with Pele 1.7.0 | web/scripts/check-diagrams.mjs |
| R-2 | `monitor_diagrams_render_with_pele` (check script: the Workflow and Gantt sources from a fixture, and a markdown block, render through `markdownToSafeHtml` + Pele with no script surviving) | web/scripts/check-markdown.mjs |
| R-3 | `manual: diagrams follow each mdBook theme and the monitor's light and dark` | review (screenshots of the five book themes and the two monitor themes) |

### Implementation tasks
1. Pin Pele 1.7.0 in web; `tools/docs/pele.sh` and the committed `docs/pele.global.js`; its
   identity check. Depends on: none.
2. The book: remove mdbook-mermaid and Mermaid's files; `pele-init.js`, `pele-theme.css`,
   `diagram-open.js` retargeted; book.toml. Depends on 1.
3. `check:docs` with Pele (R-1); ci.yml / ci_local.py keep running it. Depends on 1.
4. The monitor: Markdown.tsx with Pele, the palette mapping, `mermaid` removed; R-2. Depends on 1.
5. Docs (contributing: how diagrams render and how Pele is updated), CHANGELOG, the manual theme
   check (R-3), make ci. Depends on 2–4.

### Affects docs
docs/src/project/contributing.md, docs/book.toml, docs/src/using/documentation.md (diagrams).
