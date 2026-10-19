# Replace serde_yaml: a maintained YAML library, the on-disk format unchanged

## Problem
serde_yaml 0.9 is deprecated, and the C-to-Rust translation under it, unsafe-libyaml, is archived
and unmaintained (RUSTSEC-2024-0449, no safe upgrade). kanbanr reads and writes every board file
with it. FEAT-186 lists it as a deny.toml exception that points at this item.

## Behavior
- Evaluate maintained YAML libraries written in safe Rust (for example serde-saphyr) for serde
  compatibility, error messages, and output formatting.
- Replace serde_yaml in kanbanr-core and kanbanr-cli, keeping the on-disk format byte-for-byte for
  existing boards (a round-trip test over this board and the fixtures).
- Remove the deny.toml exception.

## Out of scope
Changing the board's file format.

## Design

### Summary
serde_yaml is replaced by **serde-saphyr ~2.0**. It is maintained, and the crate and its parser
(granit-parser) both forbid `unsafe`; two transitive dependencies, encoding_rs and smallvec, still
contain some. It sits behind one module, `kanbanr_core::yaml`, so its options are set in exactly
one place.

Because its output is not byte-identical to serde_yaml's (double quotes where serde_yaml used
single), a revision can no longer be a hash of YAML text. `content_rev` becomes a hash of
**canonical JSON**.

Existing boards migrate once, in one commit, to **schema 4**:
- Every stored revision (approvals, sign-offs, test `checked_rev`, process provenance) is re-pinned
  to the canonical hash of the content it was recorded against.
- That content is read **from the board's own git history**, at the commit that recorded it, with
  the new parser. No old serializer is needed.
- So whatever was current stays current, and whatever had lapsed stays lapsed.
- Every file is rewritten in the new format in that same commit.

### Components and files
- `api/Cargo.toml`: `serde-saphyr = { version = "~2.0", default-features = false, features =
  ["serialize", "deserialize"] }`; serde_yaml is removed; `rust-version = "1.89"`; the CI and
  release toolchain pins are updated.
- `api/crates/kanbanr-core/src/yaml.rs` (new):
  ```rust
  pub fn from_str<T: DeserializeOwned>(s: &str) -> Result<T>;   // strict_booleans: true, duplicate_keys: LastWins
  pub fn to_string<T: Serialize>(v: &T) -> Result<String>;      // yaml_12: true, no_lang_directive: true, folded_wrap_chars: usize::MAX
  pub type Value = serde_json::Value;
  ```
  `strict_booleans` and `LastWins` match serde_yaml's reading. The serializer options give no `---`,
  `key:\n- a` sequences, `|`/`|-` blocks, and no folding.
- `models.rs`: `Extra = BTreeMap<String, serde_json::Value>`.
- `models.rs` and `config.rs`: `content_rev()` hashes `canonical_json(&bare)`, via a new
  `hash::canonical_json`. That is compact JSON, struct fields in declaration order, maps sorted
  (they're all BTreeMaps).
- `error.rs`:
  ```rust
  #[error(transparent)] YamlDe(#[from] serde_saphyr::Error)
  #[error(transparent)] YamlSer(#[from] serde_saphyr::SerializeError)
  ```
  Errors render on one line, with snippets off.
- `project.rs`: the marker's `Value::Mapping` match moves to the new Value.
- Every `serde_yaml::from_str`/`to_string` call (21 and 17 in production code) becomes
  `yaml::from_str`/`yaml::to_string`. After FEAT-176 there are none in the CLI.
- `migrate.rs` (new): `migrate_to_v4(store) -> Result<MigrationReport>`.
- `store.rs`: a board below schema 4 is refused with "run `kanbanr migrate`". `kanbanr migrate`
  runs the migration under the write lock, as one commit: "migrate board to schema 4: canonical
  revisions, files rewritten".
- `deny.toml`: the exception is removed. Docs: stability.md (schema 4, "revisions are canonical"),
  CHANGELOG and upgrade notes.

### Migration algorithm
For each feature:
1. **Approval events and the current approval.** Find the board commit that introduced the event:
   the first commit, oldest first, whose version of the feature file contains an approval with the
   same `at`. Parse the file at that commit, take its definition, and set
   `rev = canonical content_rev(that definition)`.
2. **Sign-offs.** The same, keyed by `at` and `id`. Withdrawals keep their empty `rev`.
3. **Test `checked_rev`.** These are project revisions (code commits), not content hashes, so they
   don't change.
4. **Process provenance** (`config.process.rev`). Take the canonical `WorkflowFile::content_rev` of
   the project's workflow at the commit that applied it: the first commit whose config.yaml has that
   provenance.
5. **Saved processes.** Nothing stored is a rev; the version stays.

If an entry's commit can't be found (no git, a shallow clone, hand-edited history):
- its `rev` is set to `"unverified"`, which never matches, so the item reads as lapsed;
- it is counted in the report;
- doctor names those items: "approval of FEAT-012 could not be verified during the schema-4
  migration; approve again".

**How it is verified:** the old hasher can't be run once serde_yaml is gone, so correctness is
proved against a board an earlier binary made.
- v0.1.7 builds a fixture board (`api/tests/fixtures/v017/`) holding every approval state.
- The fixture records the state v0.1.7 reports for each item.
- The migration test asserts each item has the same state afterwards.

### Data safety
- **Unknown keys.** A key's value passes through serde_json::Value. serde-saphyr reads `0777` as a
  float and `1_000` as 1000, which changes such values (issue #225). The round-trip test over this
  board and the v0.1.7 fixtures asserts canonical JSON equality before and after, so any drift
  fails the build. Today no board has such values.
- **Stricter reads.** The 64-level depth budget is far above any board; the round-trip test covers
  it. Duplicate keys: LastWins, as serde_yaml did.
- **The commit.** The migration is one commit, and nothing is pushed by kanbanr unless the board's
  push policy says so. `git revert` restores the old files, but not the old binary's ability to read
  them, because schema 4 is refused by ≤ 0.1.x.

### Test plan
| Req | Test |
|---|---|
| R-1 | make ci: `cargo deny` and `cargo audit`, with the exception removed |
| R-2 | `yaml::tests::board_files_round_trip`: every YAML file of this board (copied in the test) and the v0.1.7 fixtures, read and written, with canonical JSON equal |
| R-3 | `models::tests::content_rev_is_writer_independent`: the same definition from differently formatted YAML gives the same rev |
| R-4 | `migration_keeps_current_approvals_current`: v0.1.7 fixture board with current, lapsed, withdrawn and ratified approvals, and current and lapsed sign-offs, in git; after migration each state equals the recorded expectation; exactly one commit |
| R-5 | `migration_without_history_lapses_and_reports` |
| R-6 | `a_migrated_board_is_too_new_for_older_readers`: schema_version 4 and `SchemaTooNew` for a reader at 3 |

### Implementation tasks
1. **Fixtures first.** With the v0.1.7 binary, build `api/tests/fixtures/v017/board` covering the
   state matrix: a git repo, plus `expected-states.json`. Depends on: none.
2. **yaml.rs.** Add the dependency; swap every call site; errors; the Extra type. Test: R-2 on
   fixtures, and every existing test passing. Depends on FEAT-176 task 11.
3. **Canonical revs.** `hash::canonical_json`; both `content_rev`s. Test: R-3. Depends on 2.
4. **Migration.** migrate.rs, the history walk, the report; doctor reports unverified items; store
   opens through the migration; schema 4. Tests: R-4, R-5, R-6. Depends on 3.
5. **Toolchain and policy.** MSRV 1.89 in Cargo, CI and release; deny.toml exception removed.
   Test: R-1 (make ci). Depends on 2.
6. **Docs.** stability.md; upgrade notes; CHANGELOG with the docs sync. Depends on 4.
7. **This board.** Run `kanbanr migrate` on a copy of kanbanr's own board and check every item's
   approval state is unchanged (`kanbanr review --pending --json` and `check`, before and after).
   Then migrate the real board. Depends on 4.

### Decisions
- **serde-saphyr**, not serde_norway (user's choice, 19 Oct 2026): pure safe Rust over
  byte-identical output.
- Revisions move to canonical JSON. Migration uses board history, so no old serializer is shipped.

### Open questions
- **Q1.** If a board can't be verified from history, should those approvals lapse, so they are
  re-approved?
  - Recommended: yes, lapse and report them. The alternative, trusting them, would let an
    unverifiable approval stand.
- **Q2.** Should the migration run automatically on the first command, or only by `kanbanr migrate`
  while every other command refuses with a hint?
  - Recommended: **explicit** `kanbanr migrate`. It prints the report and makes the one commit. A
    one-time rewrite of every file should be a deliberate act, not a side effect of `kanbanr board`.

### Affects docs
docs/src/project/stability.md, docs/src/releases/ (upgrade notes), CONTRIBUTING.md (yaml module).
