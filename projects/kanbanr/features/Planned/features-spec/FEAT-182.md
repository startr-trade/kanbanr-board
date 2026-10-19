# Sign-offs: withdraw, and offer only the next stage's

Two problems were found in use.

1. **No way to withdraw.** A sign-off given by mistake cannot be withdrawn. Approvals have `unapprove --reason`; sign-offs have no equivalent.
2. **Offered too early.** When a workflow lets an item skip stages (for example Implementation → Operations), the review page offers the later stage's sign-off while the item is still being built. A person can then record `release` before there is anything to release.

Scope:
- `kanbanr signoff <CODE> <NAME> --withdraw --reason "…"`. The withdrawal is recorded as an event; the earlier sign-off is kept as history and stops counting.
- A Withdraw button in the monitor next to a recorded sign-off.
- The review queue offers a sign-off only for the immediate next stage in workflow order, not for every stage reachable in one transition.

## Found in use (2026-10-16): offered before it means anything
A sign-off is offered as soon as its stage is next, even when the stage's other conditions are far from met. One example is `docs-folded` before Migration, offered the moment an item enters Implementation, before any code or documentation exists. A person reviewing the queue then signs what is in front of them, and the sign-off records agreement to work that has not happened yet.

Proposal for this item: offer a sign-off in the review queue only once the gate's `requires` are met (for example, tests green), and let a sign-off name the todo task it depends on so it is offered after that task is completed. This needs a new requirement and a re-approval of the definition.

## Design

### Summary
A withdrawal is a new entry appended to `definition.signoffs`: the history is append-only, as for
approvals. The latest entry per name decides. The review queue offers sign-offs from the
**immediate** next stage only, and only once that stage's other requirements are met (R-4,
proposed). `check`, `doctor` and the board cards keep listing every reachable stage, because the skill
asks "which stage?" from that list.

### Components and files
- `api/crates/kanbanr-core/src/models.rs`: `Signoff` gains `verdict` and `reason`; `signoff_current`
  and a new `signoff_latest`.
- `api/crates/kanbanr-core/src/store.rs`: `withdraw_signoff`; `unapprove_feature` refuses a blank
  reason (consistency, see open question Q1).
- `api/crates/kanbanr-core/src/readiness.rs`: `signoff_gaps` reports a withdrawal;
  `immediate_next_gate`; `NextGate` splits `requires_gaps` from sign-off gaps.
- `api/crates/kanbanr-core/src/dispatch.rs`: route `POST .../signoff/:name/withdraw`; its commit
  message; the review route uses `immediate_next_gate`.
- `api/crates/kanbanr-core/src/eventing.rs`: `SignoffRecorded`, `SignoffWithdrawn` events.
- `api/crates/kanbanr-core/src/export.rs`: the brief renders a withdrawn sign-off.
- `api/crates/kanbanr-cli/src/main.rs`: `signoff --withdraw --reason`.
- `web/src/types.ts`, `web/src/api.ts`, `web/src/pages/FeaturePage.tsx`: a Sign-offs section with
  Withdraw.
- `skill/kanbanr/SKILL.md`, `docs/src/using/processes.md`, `docs/src/reference/cli.md`, `CHANGELOG.md`.

### Data model
```rust
// models.rs — Signoff
/// `given` (default, omitted on disk) or `withdrawn`.
#[serde(default, skip_serializing_if = "SignoffVerdict::is_given")]
pub verdict: SignoffVerdict,
/// Why it was withdrawn; required for a withdrawal, empty otherwise.
#[serde(default, skip_serializing_if = "String::is_empty")]
pub reason: String,

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SignoffVerdict { #[default] Given, Withdrawn }
impl SignoffVerdict { pub fn is_given(&self) -> bool { *self == Self::Given } }
```
A withdrawal entry is `{id, by, at, rev: "", verdict: withdrawn, reason, status}`. **`rev` is empty
on purpose.** An older kanbanr keeps `verdict` and `reason` in `extra`, but it judges currency by
`rev`, so it sees this latest entry as lapsed and stops counting the sign-off. Old and new binaries
then agree, with no schema bump.

```rust
// models.rs — FeatureDefinition
/// The latest entry for sign-off `id`, given or withdrawn.
pub fn signoff_latest(&self, id: &str) -> Option<&Signoff>;
/// Current: the latest entry is a given one recorded against the definition as it stands.
pub fn signoff_current(&self, id: &str) -> Option<&Signoff>;   // + filter verdict == Given
```

### Behaviour
- `Store::withdraw_signoff(&self, id: &str, code: &str, name: &str, by: &str, reason: &str) ->
  Result<FeatureItem>`:
  - refuses (`CoreError::Unsupported`) when the reason is blank after trimming: "a withdrawal needs
    a reason";
  - refuses when `by` is blank (same message as `signoff_feature`);
  - refuses when the latest entry for `name` is missing ("no sign-off 'x' on CODE to withdraw") or
    already withdrawn ("sign-off 'x' on CODE is already withdrawn");
  - allows withdrawing a lapsed sign-off (it records that the earlier agreement was wrong; see Q2);
  - appends the entry and persists it exactly as `signoff_feature` does (`updated_at`,
    `persist_features`, `flush`).
- No `--rev` guard: a withdrawal is about the person's agreement, not about the content shown,
  matching `unapprove`.
- `readiness::signoff_gaps`: when the latest entry is withdrawn, the gap reads "sign-off 'x' was
  withdrawn: <reason> — `kanbanr signoff CODE x` to give it again".
- `readiness::immediate_next_gate(project, charter: Option<&Charter>, f, ctx) -> Option<NextGate>`:
  the result of `next_gates` with the **lowest position in `config.statuses`**. Ties cannot occur,
  because positions are unique.
- `NextGate` gains `requires_gaps: Vec<Gap>`, the gaps from `requires` only, with no sign-off gaps.
  `gaps` stays as it is for compatibility, because `check --json` exposes it.
- Review route (`dispatch.rs`, `GET /projects/:p/review`): `signoffs_needed` comes from
  `immediate_next_gate(..)`, and only when its `requires_gaps` has no `Level::Error` gap (R-4). An
  item whose only open decision is a sign-off not yet offered drops out of the queue.
- Route `POST /projects/:p/features/:code/signoff/:name/withdraw` with body `{by, reason}`. It is
  matched **before** the generic signoff route. Commit message: "withdraw sign-off <name> on
  <CODE>: <reason>".
- Events: `SignoffRecorded` ("{by} signed off {name} on {CODE}") and `SignoffWithdrawn` ("{by}
  withdrew sign-off {name} on {CODE} — {reason}"), from `definition.signoffs.last()`.
- CLI: `kanbanr signoff <CODE> <NAME> --withdraw --reason "<why>" [--by]`. clap makes `--reason`
  required with `--withdraw` and conflict with `--note`/`--doc`/`--rev`. Output: "CODE: sign-off
  'name' withdrawn by WHO".
- Monitor, FeaturePage: a **Sign-offs** section listing the latest entry per name (current, lapsed,
  or withdrawn with its reason) and the full history under a toggle. With writes on: a Withdraw
  button with a reason box, disabled while the reason is blank, the same pattern as Withdraw
  approval. The ReviewPage is unchanged.
- Brief (`export.rs`): a withdrawn sign-off reads "withdrawn by X: reason".

### Failure handling
Every refusal changes nothing. The store validates before appending, and the batch path has no
signoff op. A daemon started without writes answers the withdraw route with 405, which the
monitor shows as its read-only message.

### Compatibility
- On disk: two optional keys, which older readers keep in `extra`; currency agrees across versions
  (see Data model).
- `check --json`'s `next[].gaps` is unchanged; `requires_gaps` is added.
- The review queue offers fewer sign-offs (by intent). The session hook's count follows it.

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `signoff_withdraw_stops_counting` (the history keeps both entries, the gate refuses again, an older-reader simulation sees it as lapsed) | core lib.rs |
| R-2 | `signoff_withdraw_requires_reason` (blank and whitespace refused, nothing appended) | core lib.rs |
| R-3 | `review_offers_only_next_stage_signoffs` (TOGAF: at Implementation, `release` is not offered) | core lib.rs |
| R-4 | `review_offers_signoff_only_when_requires_met` (proposed requirement) | core lib.rs |
Also: an eventing test for both events, a CLI round trip in local_mode.rs, and a daemon withdraw in
view_daemon.rs.

### Implementation tasks
1. **Model.** models.rs: add `SignoffVerdict`, the `verdict` and `reason` fields, and
   `signoff_latest`; change `signoff_current`. Tests: model unit test for currency with a withdrawn
   latest entry. Depends on: none.
2. **Store.** store.rs: `withdraw_signoff` as specified; `unapprove_feature` refuses a blank reason
   (if Q1 is yes). Tests: R-1, R-2. Depends on 1.
3. **Readiness.** readiness.rs: the withdrawn gap text, `NextGate.requires_gaps`,
   `immediate_next_gate`. Tests: unit tests for `immediate_next_gate` on TOGAF and PDCA. Depends
   on 1.
4. **Dispatch.** dispatch.rs: the withdraw route and its commit-message arm; the review route uses
   `immediate_next_gate` and the R-4 filter. Tests: R-3, R-4. Depends on 2, 3.
5. **Events.** eventing.rs: the two kinds and `compute_events` arms. Test:
   `signoff_events_are_recorded`. Depends on 4.
6. **Brief.** export.rs: render withdrawn. Test: brief snapshot assertion. Depends on 1.
7. **CLI.** main.rs: `Signoff` gains `withdraw: bool` and `reason: Option<String>` (clap
   `requires`/`conflicts_with`); the handler posts to the withdraw route. Test: local_mode.rs
   `cli_signoff_withdraw_round_trip`. Depends on 4.
8. **Monitor.** types.ts (`Signoff`, `FeatureDefinition.signoffs`, `ApprovalEvent.verdict` adds
   `ratified`); api.ts `withdrawSignoff(project, code, name, by, reason)`; FeaturePage Sign-offs
   section. Checks: `npm run build`, `check:ui`, and a view_daemon.rs withdraw test. Depends on 4.
9. **Docs and skill.** SKILL.md "Waiting decisions" and the command reference; processes.md
   Sign-offs; cli.md; CHANGELOG with the docs sync. Depends on 7.

### Decisions (19 Oct 2026: every recommended answer accepted)
- **Q1.** Should `unapprove` also refuse a blank reason? Today only the monitor enforces it.
  Decided: yes.
- **Q2.** Can a lapsed sign-off be withdrawn? Decided: yes; it records that the earlier
  agreement was wrong.
- **Q3 (needs a new requirement, R-4).** Offer a sign-off only once the stage's other requirements
  are met? Decided: yes. Naming a todo task that a sign-off waits for is left out: a process
  cannot name an item's task.

### Affects docs
docs/src/using/processes.md (Sign-offs), docs/src/reference/cli.md, skill/kanbanr/SKILL.md (Waiting
decisions).
