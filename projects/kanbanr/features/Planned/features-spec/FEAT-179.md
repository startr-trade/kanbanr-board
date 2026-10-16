# Design stage: a build-ready design in the spec

At a design stage (one whose purpose is how and where, such as System Design or Design), the item's spec should carry the actual technical design at implementation level. That means components, modules and files; public interfaces with signatures and responsibilities; data model and formats; algorithms; control flow; concurrency and failure handling; configuration and defaults; dependencies; security; performance budgets; a test plan mapping each requirement to its tests; compatibility; and ADR links and open questions. The definition's how and where lines are one-line summaries of it. A spec that stays non-technical at this point leaves the implementer to guess.

Scope:
- **Skill guidance.** State the rule in the skill, and suggest `signoffs: [design-review]` on the build stage when a project wants a human review of the design before build.
- **Gate check.** A new gateable check, `spec_sections: [<heading>, …]`, that refuses entry to a stage until the spec contains each named heading with non-empty content. It is listed in the gate vocabulary and in the working agreement.
- **Docs.** The process chapter explains both.
