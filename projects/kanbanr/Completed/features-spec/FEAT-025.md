# Diagrams & images in documentation

The markdown doc viewer renders:
- **Mermaid** fenced ```mermaid blocks -> inline SVG (flowchart/sequence/etc.), theme-aware (light/dark), via the `mermaid` package, lazily loaded.
- **Embedded images**: relative `<img>` names resolve **per document folder** (DocPage parentPath) to the daemon's `/docs/raw` endpoint, so a bare image name is meaningful in ANY docs folder. Verified across two folders (design/, guides/).
- Any other diagram tool (PlantUML, Graphviz/DOT, D2, Excalidraw, draw.io) works by exporting PNG/SVG and embedding it as an asset.

Implemented in web/src/components/Markdown.tsx (+ styles). Screenshot tool polls until mermaid blocks render before capture. Showcased in README + docs/images (doc-mermaid.png, doc-file.png).