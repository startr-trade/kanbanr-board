# FEAT-179 draft (unapplied): skill and docs text

Apply on the FEAT-179 branch once the item is approved: `git apply`, using the diff below.

```diff
diff --git a/docs/src/using/processes.md b/docs/src/using/processes.md
index 02660c7..2d0191f 100644
--- a/docs/src/using/processes.md
+++ b/docs/src/using/processes.md
@@ -147,6 +147,29 @@ what a later stage will. Each time the definition grows, its approval lapses and
 Each approval records the status it was given in, so the history reads "approved at Business
 Arch, again at System Design".
 
+## The design stage: a build-ready design in the spec
+
+At a design stage, the item's **spec** carries the technical design at implementation level, in a
+`## Design` section. It covers:
+- components, modules and files;
+- public interfaces with signatures and responsibilities;
+- data model and formats, algorithms and control flow;
+- concurrency and failure handling;
+- configuration and defaults, and dependencies;
+- security and performance budgets;
+- a test plan that maps each requirement to its tests;
+- compatibility, ADR links and open questions.
+
+The definition's `how` and `where` lines summarise it. To have a person review the design before
+build, add a sign-off to the build stage's gate:
+
+```yaml
+gates:
+  Implementation:
+    requires: [tests_named, approved]
+    signoffs: [design-review]
+```
+
 ## A worked example: PDCA
 
 ```bash
diff --git a/skill/kanbanr/SKILL.md b/skill/kanbanr/SKILL.md
index 9bd9a62..080a6e2 100755
--- a/skill/kanbanr/SKILL.md
+++ b/skill/kanbanr/SKILL.md
@@ -341,6 +341,31 @@ than one next stage is possible, ask which. Head the plan with the stage's own `
 quality it must reach", "when it happens". If the definition does not yet address it, ask (with
 options, e.g. a latency target, or "no target"), rather than noting its absence afterwards.
 
+### The design stage: the spec carries the build-ready design
+
+When an item reaches a stage whose purpose is *how and where* (System Design, Design, or the
+equivalent in the project's process), its **spec** gains a `## Design` section written at
+implementation level. A reviewer or another session should be able to build from it without
+guessing:
+- components, modules and files;
+- public interfaces with signatures, and what each must do;
+- the data model and on-disk or wire formats;
+- algorithms and edge cases, and control flow (a diagram where it helps);
+- concurrency, transactions and failure handling;
+- configuration and its defaults (with how each default was chosen);
+- dependencies;
+- security and privacy;
+- performance budgets that name their benchmark;
+- a test plan mapping each requirement to its tests;
+- compatibility and migration;
+- links to ADRs, and open questions stated as questions.
+
+The definition's `how` and `where` lines are one-line summaries of this section, never a
+substitute for it. A section that does not apply says "n/a" and why. A spec that stays
+non-technical at this stage leaves implementation decisions unreviewed, which is the failure the
+gate exists to prevent. A project that wants a person to review the design before build adds
+`signoffs: [design-review]` to its build stage's gate.
+
 ### A new item: scope it in plan mode
 
 When the user asks for work, **enter plan mode** before writing anything. Read the charter and the
```
