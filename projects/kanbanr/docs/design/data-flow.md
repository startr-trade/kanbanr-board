# Data flow

How a change moves through kanbanr — rendered live from a Mermaid code block:

```mermaid
flowchart LR
  C["Claude (skill)"] --> CLI["kanbanr CLI<br/>(only writer)"]
  CLI -->|commit| D[("data/ git repo<br/>YAML + markdown")]
  D -->|push / pull| R["git remote<br/>(sharing)"]
  D -->|read| S["kanbanr serve<br/>read-only"]
  S --> UI["React monitor<br/>+ SSE"]
```

Diagrams can be authored as Mermaid (above) **or** embedded as images (see the Overview), so any
tool that exports PNG/SVG works too.
