# Defect: new supply-chain advisories (rustls; unsafe-libyaml unmaintained)

## Problem
make ci on 17 Oct 2026 failed its supply-chain checks on advisories published since v0.1.7:
- RUSTSEC-2026-0346 (medium) and RUSTSEC-2026-0348 (low): rustls 0.23.45, fixed in 0.23.46. In
  api/Cargo.lock and tools/screenshots/Cargo.lock. `cargo audit` fails.
- RUSTSEC-2024-0449: unsafe-libyaml 0.2.11 is unmaintained (archived, no release since March 2024,
  "no safe upgrade available"). It comes in through serde_yaml 0.9 (itself deprecated), which
  kanbanr-core and kanbanr-cli use to read and write every board file. `cargo deny` fails.
Both would fail CI on main.

## Behavior
- rustls 0.23.46 or later in both lockfiles.
- unsafe-libyaml: the deny.toml sanctioned exception (a finding with no reachable fix), listed with
  its reason and the item that tracks replacing the YAML library — or the replacement itself, as
  decided.

## Out of scope
Changing the board's on-disk format.
