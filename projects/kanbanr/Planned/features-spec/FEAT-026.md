# Cross-project dependencies

Allow `depends_on` entries of the form `<project>:<code>` (bare code = same project). Add a `graph.rs` global resolver that loads N projects and runs cycle/existence checks across them (generalize `validate.rs::validate_dag`). Route `set_feature_attrs`/milestone validators through it for qualified deps.

See `docs/proposals/enterprise-scale.md` §2.A.