## Problem

Estimates exist only in days, and nothing records a project's sprint length or release cadence.

## Behavior

`points` on an item beside `estimate_days`; `estimate_unit: points|days` and `cadence: {sprint_length_days, release}` in the config; an `estimated` check using the project's unit; capacity and velocity in that unit.

See the design doc `design/process-as-configuration.md`.

## Out of scope

- Estimation techniques.