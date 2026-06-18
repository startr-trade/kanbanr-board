# Store scale

Split metadata load from spec load — `read_features` eagerly reads every spec `.md`; board/list/graph don't need them. Add a rebuildable per-project `index.yaml` (code -> status/milestone/labels/owner/deps) so listing + the global graph read one file per project.

See `docs/proposals/enterprise-scale.md` §2.D.2-3.