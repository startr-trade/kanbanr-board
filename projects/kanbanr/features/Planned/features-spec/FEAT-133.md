## Problem

kanbanr has no visual identity: the monitor's header is the text `▦ kanbanr`, browser tabs show a generic icon, the docs site has mdBook's default, the README opens with a heading, the VS Code extension has no icon, and the repository has no social preview. Its sibling projects under startr.trade share a palette and a lockup pattern; kanbanr does not use either.

## Behavior

- **The mark:** a `k` whose stem is a kanban column of three cards and whose arms are the thread the work runs along — one climbs to the next item (an open ring), one lands on done (a saffron dot). Navy `#26317E` / saffron `#E8871E` on light; `#AEB6E8` / `#F49D1A` on `#0F1117` dark, the startr.trade family palette.
- **Assets** in `assets/brand/`: the mark, a favicon cut (solid cards, heavier arms, theme-aware so it reads at 16 px on light and dark tabs), light and dark lockups (the mark's upper arm runs on as the headline bar the wordmark hangs from, ending in a saffron arrow, with 看板 beneath), an app icon, and a 1280×640 social preview, each as SVG with PNG renders where a PNG is needed.
- **Wired in:** the README header (light/dark `<picture>`), the docs site's favicon, the monitor's favicon and header mark (replacing `▦`), and the VS Code extension's icon. The social preview is uploaded by the maintainer (Settings → Social preview).

## Out of scope

- A style guide beyond the palette and the mark's construction notes in the SVG comments.
