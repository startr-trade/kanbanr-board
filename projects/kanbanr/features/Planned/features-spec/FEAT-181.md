# Live, checked links between board artifacts

Design artifacts on a board (specs, architecture and component docs, ADRs, plans) name each other in plain text: `FEAT-012`, `ADR-0005`, `architecture/data.md`. Plain names cannot be followed in the monitor, nothing checks that they still point at something, and `trace` cannot see them, so drift between documents goes unnoticed.

Scope:
- **Monitor.** Item codes (with an optional `/R-n`), ADR ids, milestone codes, charter goal ids and board doc paths in rendered markdown become links to their pages. Links that are already written are kept.
- **Doctor.** Reports links and references in specs, docs and ADRs that point at an item, ADR, doc, milestone or goal the board does not have.
- **Trace.** Doc-to-item, doc-to-doc and doc-to-ADR links count as traceability edges, so `kanbanr trace` and `why` follow them.
- **Skill.** States the rule: every reference in a design artifact is a live link, and a spec's design section ends with the docs it affects (FEAT-180). The skill also says how to write each kind of link.
