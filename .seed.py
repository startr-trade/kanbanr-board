import json, subprocess, sys, os
env = dict(os.environ, KANBANR_DATA_DIR="/path/to/kanbanr/data", KANBANR_PROJECT="kanbanr")
ops=[]
def ms(ref,name,code,desc,deps): ops.append({"op":"milestone.add","ref":ref,"name":name,"code":code,"description":desc,"depends_on":deps})
def add(ref,title,mscode,kind,prio,labels,spec): ops.append({"op":"feature.add","ref":ref,"title":title,"milestone":mscode,"kind":kind,"priority":prio,"labels":labels,"spec":spec})

DOC="`docs/proposals/enterprise-scale.md`"

ms("m5","P3 — Enterprise-Scale Coordination","MS-005",
   "Multi-project, cross-project dependencies, derived ready/blocked, portfolio rollups, and safe concurrent use. Full design: "+DOC+".",
   ["MS-003"])

# --- Phase 1 ---
add("xdeps","Cross-project dependencies (qualified refs + global graph)","MS-005","feature","high",["enterprise","dependencies","phase-1"],
"# Cross-project dependencies\n\nAllow `depends_on` entries of the form `<project>:<code>` (bare code = same project). Add a `graph.rs` global resolver that loads N projects and runs cycle/existence checks across them (generalize `validate.rs::validate_dag`). Route `set_feature_attrs`/milestone validators through it for qualified deps.\n\nSee "+DOC+" §2.A.")

add("derived","Derived dependency state (ready/blocked/graph/impact)","MS-005","feature","high",["enterprise","dependencies","phase-1"],
"# Derived dependency state\n\nCompute blocked/ready from the global graph; add `kanbanr ready`, `blocked`, `graph`, `impact <id>` (and surface 'what's unblocked now' in the web view). Pure read-side.\n\nSee "+DOC+" §2.B.")

add("batch1","Batch: load project once (perf)","MS-005","refactor","high",["enterprise","performance","phase-1"],
"# Batch loads project once\n\n`store.rs::apply_batch` currently reloads the whole project per sub-op (a K-op bundle ≈ K+ full loads). Refactor to load one mutable `Project`, apply all ops in-memory, validate once, persist only changed files.\n\nSee "+DOC+" §2.D.1.")

add("wlock","Concurrency: write lock","MS-005","feature","high",["enterprise","concurrency","phase-1"],
"# Write lock\n\nEvery mutation commits+pushes with no lock (`backend.rs:86-98`), so two sessions diverge. Take an OS advisory file lock around mutate->commit (per data-dir or per-project) to serialize concurrent writers.\n\nSee "+DOC+" §2.E.1.")

# --- Phase 2 ---
add("portfolio","Portfolio/Program hierarchy + cross-project board & rollups","MS-005","feature","medium",["enterprise","portfolio","phase-2"],
"# Portfolio / Program hierarchy\n\nAdditive `workspace.yaml` declaring programs and member projects (projects stay put — it's an index). Cross-project board/schedule/roadmap + progress rollups (milestone% -> project% -> program% -> portfolio%). Add `--portfolio`/`--all-projects`.\n\nSee "+DOC+" §2.C.")

add("owner","Ownership: assignee/team fields + by-owner views","MS-005","feature","medium",["enterprise","phase-2"],
"# Ownership\n\nAdd optional `assignee`/`owner` + `team` to `FeatureItem` (`#[serde(default)]`, backward-compatible). Optional `people.yaml`/`teams.yaml`. Enables by-owner/by-team and WIP/workload views.\n\nSee "+DOC+" §2.F.")

add("query","Query: rich filters + full-text + cross-project","MS-005","feature","medium",["enterprise","phase-2"],
"# Query\n\n`kanbanr query` filtering by label/owner/team/kind/priority/due-range/dep-state (ready|blocked) + full-text over titles/specs, with `--all-projects`. Add reporting: aging/at-risk, burndown from created_at/updated_at + activity log.\n\nSee "+DOC+" §2.F.")

add("store2","Store scale: lazy specs + per-project index","MS-005","refactor","medium",["enterprise","performance","phase-2"],
"# Store scale\n\nSplit metadata load from spec load — `read_features` eagerly reads every spec `.md`; board/list/graph don't need them. Add a rebuildable per-project `index.yaml` (code -> status/milestone/labels/owner/deps) so listing + the global graph read one file per project.\n\nSee "+DOC+" §2.D.2-3.")

# --- Phase 3 ---
add("daemon","Single-writer daemon + debounced push","MS-005","feature","medium",["enterprise","concurrency","phase-3"],
"# Single-writer daemon\n\nPromote `kanbanr-server` (dispatch is already method+path+body; auth via security.yaml/JWT) to accept writes over a local socket/HTTP, hold projects in memory, serialize all mutations; sessions/agents become thin clients. Move `git::sync_all` (push) off the hot path — debounce/idle or `kanbanr sync`.\n\nSee "+DOC+" §2.E.2-3.")

add("critpath","Critical path, impact & scheduling/dates","MS-005","feature","low",["enterprise","phase-3"],
"# Critical path + scheduling\n\nOptional start/target dates + effort on features; dependency-aware date propagation; `critical-path` and downstream `impact` across the portfolio graph.\n\nSee "+DOC+" §2.B / §3 Phase 3.")

add("events","Eventing / notifications on state change","MS-005","feature","low",["enterprise","phase-3"],
"# Eventing\n\nEmit on state change (esp. a dep reaching Completed -> dependents become ready) via webhook/hook so cross-team handoffs notify. Builds on the existing activity changelog.\n\nSee "+DOC+" §2.F.")

add("integrity","Schema versioning, access scope & doctor","MS-005","feature","low",["enterprise","integrity","phase-3"],
"# Versioning, access scope, doctor\n\nAdd `schema_version` + migration step. Decide multi-team access: monorepo + daemon-auth vs per-project git repos/submodules. `kanbanr doctor` validates the portfolio-wide graph (dangling cross-project refs, orphans).\n\nSee "+DOC+" §2.A.4 / §2.G.")

p=subprocess.run(["kanbanr","batch","--project","kanbanr","--message","Add P3 Enterprise-Scale Coordination milestone + phased feature items (see docs/proposals/enterprise-scale.md)"],
                 input=json.dumps({"operations":ops}),text=True,capture_output=True,env=env)
sys.stdout.write(p.stdout); sys.stderr.write(p.stderr)
print(f"\n--- {len(ops)} ops; exit={p.returncode} ---")
sys.exit(p.returncode)
