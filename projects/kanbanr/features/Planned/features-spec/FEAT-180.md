# Living architecture docs

Feature specs describe what one feature changed. Nothing gathers those changes into a current picture of the product, so architecture and design documents drift as features ship, and hand-written books drift with them.

The method, for any project:
- **Architecture repository in board docs.** Vision (the charter), the business, data, application and technology views, a component catalog, ADRs and standards. Each view answers the six Zachman columns.
- **One design doc per component, as built.** Its front matter lists the code paths it covers and the items that changed it. A feature's Design section is the change; finishing the feature folds that change into each affected component doc.
- **Generated views where possible** (catalogs, graphs, reference pages), never hand-copied.

Scope:
- **Skill guidance.** At the design stage, the spec names the component docs and views the item affects (`affects_docs`). Completing the item folds its design into them. A milestone ends with an architecture compliance review.
- **A gate check `docs_updated`.** It passes when every doc the item declares it affects has been changed since the item entered its current stage, judged from the board's history.
- **Docs.** A chapter on living architecture documentation.
