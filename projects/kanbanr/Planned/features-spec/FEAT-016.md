# Doc binary/image assets (P1)

kanbanr docs are markdown-text only today, so embedded images have nowhere to live. Add binary asset support so docs + diagrams travel inside the (self-contained) data repo.

## Scope
- Store binary files in the docs tree (`kanbanr doc add path.png --file local.png`, bytes).
- View daemon serves doc assets with content-type detection.
- Markdown renderer resolves relative image paths to the doc-content endpoint.
- External/project docs you don't want to duplicate: plain markdown links (no dual model).