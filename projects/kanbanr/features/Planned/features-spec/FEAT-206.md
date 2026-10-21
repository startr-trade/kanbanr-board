# Two RustSec advisories in the TLS trust chain

## Why
On 19–20 Oct 2026 RustSec published two advisories against crates in kanbanr's lockfile, reached
through `ureq` (the self-update and release-check client):

- [RUSTSEC-2026-0381](https://rustsec.org/advisories/RUSTSEC-2026-0381): `webpki-roots` 1.0.9 still
  bundles a root that lets certificate paths through distrusted emSign intermediates, whose private
  keys are now well known. Fixed in 1.0.10.
- [RUSTSEC-2026-0382](https://rustsec.org/advisories/RUSTSEC-2026-0382): `rustls-webpki` 0.103.15
  may accept those distrusted intermediates. Fixed in 0.103.16.

`cargo deny` and `cargo audit` now fail, on main as on every branch, so CI on GitHub would fail on
the next push. Found by `make ci` on FEAT-203.

## Design

### Change
- `api/Cargo.lock` only: `cargo update -p webpki-roots@1.0.9 -p rustls-webpki`, which moves exactly
  `webpki-roots` 1.0.9 → 1.0.10 and `rustls-webpki` 0.103.15 → 0.103.16 (a dry run confirms no
  other crate moves). No manifest or code change; both are semver-compatible patch releases.
- CHANGELOG "Security" entry naming both advisories.

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `ci.yml supply-chain: cargo deny` and `cargo audit` pass | make ci |
| R-2 | `cargo test --workspace` (the self-update and release-check tests use `ureq`) | make ci |

### Implementation tasks
1. The lockfile update; the changelog entry; make ci. Depends on: none.

### Affects docs
None: no behaviour or interface changes.
