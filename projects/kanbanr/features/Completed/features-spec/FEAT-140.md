## Problem

The first CodeQL run on the public repository reports `js/xss-through-dom` (high) at `web/src/components/Markdown.tsx:51`, where a rendered Mermaid diagram is inserted with `innerHTML`. The finding points at a wider gap: the monitor renders every item spec and board document with `marked` and puts the result into the page with `dangerouslySetInnerHTML`, **unsanitised**. The component's comment calls the markdown "trusted (locally-authored)", but a board is shared through a git remote, so its documents are written by everyone who can push to it. With `kanbanr serve --allow-writes` — how the Review page's Approve, Ratify and Sign off buttons work — a script in a shared document runs in the maintainer's browser on the monitor's own origin and can call the write routes: approve an item, sign off, ratify, as the maintainer.

## Behavior

- Markdown is sanitised before it reaches the page, with DOMPurify (already in the tree through Mermaid): scripts, event-handler attributes and `javascript:` URLs are removed; ordinary markdown — headings, lists, tables, code, links, images — renders as before.
- A Mermaid diagram's SVG is sanitised with DOMPurify's SVG profile before it is inserted, rather than trusting the library's own output.
- The CodeQL alert is closed by the fix, not dismissed.

## Out of scope

- Authentication for the write routes: the monitor stays a localhost tool; this removes the way a shared document could use them.
