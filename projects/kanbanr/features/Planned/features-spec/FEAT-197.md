## Problem
Living architecture docs drift even when every item's design is folded in. The fold-in check (`docs_updated`) only covers the docs an item names in `affects_docs`. The cross-cutting views are rarely named, so nothing notices when they fall behind:
- a Zachman or coverage matrix;
- an ADR index;
- the component catalog in an application view.

**An observed case.** A board ran a sprint in which more than twenty items moved past the vision stage and five ADRs were accepted. Every item's own component docs were updated. Even so:
- the Zachman matrix lacked 24 of those items;
- 8 ADRs were referenced from no architecture view;
- the component catalog lacked 7 shipped items and 6 designed components.

No gate fired, and `doctor` reported only broken links.

## What this adds
1. **Project-configured coverage rules** in the project config, generic over any process. Examples:
   - "every item at stage S or later is referenced from doc D";
   - "every accepted ADR is referenced from some doc under folder F";
   - "every doc under folder C is referenced from doc K" (a catalog lists every component doc);
   - "every item in stage S lists doc D in `affects_docs`".

   References use the existing reference finder: live links and board-shaped tokens.
2. **Lifecycle triggers.** The rules are evaluated:
   - when an item is added, moved or its definition edited;
   - when an ADR is accepted;
   - when a doc is written;
   - at sprint close and release cut.

   A move reports the uncovered rule as a warning, or refuses it when the rule is a gate condition (`docs_cover`) on that stage's gate. The other events report it as a warning in the command's output and in the board-update hook. `doctor` lists every uncovered rule.
3. **Default `affects_docs` per stage.** A process can name docs that every item entering a stage must list, so the views are always part of the fold-in and `docs_updated` covers them.
4. **Skill guidance.** The skill tells Claude:
   - to add the project's view docs to `affects_docs` when it writes a design;
   - to add every new ADR to the architecture index when the ADR is accepted;
   - to fix coverage warnings before moving an item;
   - to run `doctor` before a sprint merge or a release cut.
5. **`process checks`** lists `docs_cover` with its narrowing (rule ids).

## Out of scope
Checking that the content of a doc is semantically accurate.
