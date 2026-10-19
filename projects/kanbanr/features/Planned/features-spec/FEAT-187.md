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
