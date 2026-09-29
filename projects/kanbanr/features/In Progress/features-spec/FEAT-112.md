## Problem

"What is this item missing?" is answered five times — `check_report` in the CLI, doctor, `check --file`, `query::has_gap`, and the monitor's client-side chips — and they have drifted (doctor has no green-test check, check has no ISO checks, the review queue and check have no adoption cutoff).

## Behavior

A core `readiness.rs` evaluates a closed vocabulary of checks against an item and returns gaps with a level. check, finish, doctor, `check --file`, query and a new `GET …/features/{code}/readiness` endpoint all use it; the monitor reads the endpoint. Behaviour-preserving for today's rules, pinned by a golden test.

See the design doc `design/process-as-configuration.md`.

## Out of scope

- Declaring which checks apply where (FEAT for gates).