# Defect: timestamps are compared as text, so "created before the charter" can be wrong

## Problem
CI failed on macOS after v0.1.5's push: `an_override_is_recorded_in_history` found no gate warning,
because the gate treated the item as created *before* the charter was adopted and exempted it.
Timestamps are written as RFC 3339 with the fractional seconds' trailing zeros dropped, so their
length varies, and comparing them as strings is wrong when they share a second:
`…:05.12Z` sorts after `…:05.1234Z`, although .12 is earlier. macOS clocks have microsecond
resolution and produce trailing zeros often; Linux and Windows rarely do, which is why only the
macOS leg failed.

The same comparison decides whether the method applies to an item (store gate check, the
completion evidence check, two doctor checks), which items a retrospective counts, and which items
the issue mirror syncs. An item created in the same second as the charter could escape its gates.

## Behavior
- Every comparison of two timestamps compares instants, not text: one helper parses both, falling
  back to the old text comparison only for a value that is not a timestamp.
- A test compares timestamps whose fractional parts differ in length, in both orders.

## Out of scope
Changing the stored timestamp format.
