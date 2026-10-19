# make ci's board check lets a person's verdicts through

## Why
[FEAT-195](/p/kanbanr/feature/FEAT-195) made `make ci` fail when the real board changes during a
run. On 19 Oct 2026 that failed four runs in a row, every time because the user approved or signed
off items in the monitor while CI ran. Tests can no longer reach the board (the fence), so a
person's verdict during a run is expected, not a sign of a leak. Decided 19 Oct 2026: ignore
verdict commits; any other change still fails the run.

## Design

### Components and files
- `scripts/ci_local.py`: `board_state()` records the board HEAD and `git status --porcelain`
  separately; a new `verdict_only(board, before, after) -> list[str] | None` returns the new
  commits' subjects when every one is a verdict, else None.

### Behaviour
- After the run: working tree status unchanged, and either HEAD unchanged, or every commit in
  `before..after` is a **verdict**:
  - its subject starts with one of `approve definition of `, `ratify `, `withdraw the approval of `,
    `sign off `, `withdraw sign-off `;
  - and it touches only `projects/*/features/**`, `projects/*/activity/**` and
    `projects/*/events/**` (`git diff-tree --no-commit-id --name-only -r <sha>`).
- Then the check passes and prints "the real board took N verdict(s) during the run: …".
- Anything else fails exactly as before, listing the commits that are not verdicts.

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `manual: make ci passes with a sign-off made mid-run, and fails with a non-verdict commit mid-run` | review |
| R-1 | `scripts/tests/test_ci_local.py::test_verdict_only` (a scratch git repo: verdict commits accepted; a verdict subject touching config.yaml refused; a non-verdict subject refused) | python unittest, run by make ci |

### Implementation tasks
1. `verdict_only` and its use in `main()`; the message. Depends on: none.
2. `scripts/tests/test_ci_local.py` with `test_verdict_only`; make ci runs it (a step in
   `ci_local.py` before the workflow steps). Depends on 1.
3. CHANGELOG "Changed" line, contributing note, docs sync. Depends on 2.

### Affects docs
docs/src/project/contributing.md (a code-repo file, not a board doc).
