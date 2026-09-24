# Feature definition block: six dimensions, requirements, tests

## Problem
Work items carry what/who/when but no why, no requirements, and no statement of how they will be verified.

## Behavior
- `Option<FeatureDefinition>` inline in `FeatureMeta` with `skip_serializing_if`, so existing yaml loads and re-serializes byte-identically; added in `FeatureItem`, `meta()`, `from_meta()` plus the two literal sites.
- Fields: `statement`, `goals[]`, `zachman{what,how,where,when,who,why}` (one line each), `design_doc`, `requirements[{id, kind, text, iso25010, scenario, tests[{name, kind, state, checked_rev}]}]`.
- Defect-shaped items additionally carry `violates`, `root_cause`, `introduced_by`, `escaped`, `severity`.
- `store::set_feature_definition{,_on}` on a dedicated path; `definition` on `feature.add`/`feature.edit`; `PUT /projects/{p}/features/{code}/definition`; `kanbanr feature define --file|--clear|--template --kind <kind>`.
- Tests nest under requirements, so traceability is structural.

## Out of scope
EARS validation and doctor checks (FEAT-049); rendering (FEAT-050).
