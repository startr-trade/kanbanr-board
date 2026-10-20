## Problem
Specs, docs and ADRs carry Mermaid diagrams in fenced `mermaid` blocks. kanbanr renders them in the web view, but nothing checks a diagram when it is written. A broken diagram is found only when a reviewer opens the page and sees "Syntax error". By then the item may already be waiting for approval, and an agent-written spec is likely to contain the common mistakes.

**An observed case.** In one session, three specs written by agents had invalid diagrams:
- a `;` inside a sequence-diagram message, which ends the statement;
- JSON with quotes and braces inside sequence messages;
- an unquoted flowchart label containing `;`.

## What this adds
1. **Lint on write, in the core and pure Rust.**
   - **Where it runs:** on `feature add`/`edit` (spec), `doc add`, `adr` writes and `batch`.
   - **What it does:** checks every fenced `mermaid` block in the written markdown and reports a warning with file, block and line. The write still succeeds; a strict mode in project config can refuse it.
   - **Rules, a starter set:**
     - the first line names a known diagram type;
     - no `;` inside sequence messages or labels;
     - no unbalanced `{`, `}`, `[`, `]`, `(`, `)` or `"` in a label;
     - an unquoted flowchart label must not contain `;`, `|`, `{`, `}` or unbalanced parentheses;
     - `end` is used only as a keyword, never as a node id;
     - `subgraph`/`end`, `alt`/`else`/`end`, `loop`/`end` and `opt`/`end` are balanced;
     - every line in a sequence diagram declares or uses a participant;
     - no empty block.
2. **`doctor`** lists every lint finding across the board.
3. **Real parse on the review page.**
   - **Before Approve:** the web review page runs the bundled Mermaid library's `mermaid.parse()` on every block of the item's spec and its `affects_docs`.
   - **On error:** it lists each error with its block and line, links to the source, and disables Approve until the diagrams parse.
   - **The same check** runs in the doc viewer, showing the error under the diagram instead of only "Syntax error".
4. **A `process checks` condition, `diagrams_valid`,** so a project can require it on a stage gate. The core lint and the review page's last recorded parse result both feed it.
5. **Skill guidance:** quote flowchart node labels; keep sequence messages to plain words, with no `;`, braces or quotes; never use `end` as an id; run the lint (`kanbanr doctor`) after writing diagrams.

## Out of scope
A full Mermaid grammar in Rust. The lint catches the common mistakes, and the review-page parse is the authoritative check.

## Gating moves (added 2026-10-20)
A project must be able to require `diagrams_valid` on **every** stage gate, so that no item moves between states while its spec, or any doc in its `affects_docs`, has a Mermaid block that fails the lint. `process check` must accept `diagrams_valid` in any gate's `requires`. When it fails, the move's refusal names each failing block (file, block number, line, rule). The lint result is computed at move time, not cached, so a fixed diagram unblocks the move immediately.
