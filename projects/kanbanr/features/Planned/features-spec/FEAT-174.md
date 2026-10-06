# Defect: new advisories in KaTeX (via mermaid) and rustls (screenshot tool)

## Problem
make ci on 6 Oct 2026 failed two supply-chain checks on advisories published since the last run:
- GHSA-238p-pmpm-9mq7 (low): KaTeX 0.11.0–0.18.1, prototype pollution bypassing trust
  restrictions. The monitor gets KaTeX 0.16.47 through mermaid 11.17.2; no mermaid release (12.1.0
  included) accepts the fixed KaTeX 0.19.0. `npm audit` fails, and Trivy flags web/package-lock.json.
- GHSA-2mjx-qc3c-rqvc (medium): rustls < 0.23.45, in tools/screenshots/Cargo.lock (0.23.40). The
  shipped binary's lock already has 0.23.45.
Both would fail CI on GitHub for main too.

## Behavior
- web/package.json overrides KaTeX to 0.19.0 under mermaid; the monitor's diagrams still render
  (the Workflow page and a docs diagram, checked in a headless browser); `npm audit` is clean.
- tools/screenshots takes rustls 0.23.45 or later (`cargo update -p rustls`).
- Remove the override when mermaid accepts a fixed KaTeX.

## Out of scope
Upgrading mermaid to 12.
