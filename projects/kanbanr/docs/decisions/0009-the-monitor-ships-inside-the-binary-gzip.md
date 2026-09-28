---
id: ADR-0009
status: accepted
date: 2026-09-28
deciders:
- Venkatraman B
affects:
- FEAT-084
- FEAT-024
driven_by:
- FEAT-084/R-5
- FEAT-084/R-1
quality:
- Performance Efficiency
- Interaction Capability
zachman:
- How
- Where
layer: physical
---

# The monitor ships inside the binary, gzipped

## Context

The project's stated constraint is *one binary, installable without a toolchain beyond cargo*. It
was only ever true of the CLI. `kanbanr serve` served whatever `--ui-dir` pointed at and nothing was
embedded, so the monitor needed Node and a build; the release tarballs carried the executable alone.
Downloading one gave a working API, a blank page, and no explanation — the project's recurring
failure shape, an absence reported as silence.

The forces:

- **The person installing is not the person building.** Conflating them is how the gap arose: the
  repository always had `web/dist` to hand, so nobody met the state a stranger starts in.
- **Size is a real cost** but a measurable one: `web/dist` is 3.4 MB raw, 0.9 MB gzipped, against a
  12 MB binary.
- **Embedding couples the builds.** The web assets must exist before the Rust build, so `cargo
  build` from a clean checkout no longer produces a working monitor by itself.
- **Developing the SPA needs the opposite** — the dist just built, not one baked in at compile time.

## Decision

We will compile the built SPA **into the binary**, gzipped, and decompress it once at startup. With
no `--ui-dir`, `serve` serves that copy; with one, the directory still wins.

A build with no `web/dist` **succeeds and embeds nothing**, and the daemon reports the absence at
startup, naming both remedies. A contributor has no reason to have Node, and a build that fails on a
missing generated directory teaches people to avoid the build; a build that silently produces a
blank page is worse than either.

Every packaging path builds the SPA first — the release workflow, the Dockerfile, and `make
install-cli` — so no deployment can hide a broken embed behind a stale `--ui-dir`.

## Alternatives considered

- **`build.rs` runs `npm run build`.** Always correct, and it puts Node back in the build path for
  everyone compiling from source — the toolchain this is meant to remove. Rejected: it moves the
  cost onto contributors to spare users, when the two can simply be separated.
- **Commit `web/dist`.** No Node anywhere, including a `cargo install` from crates.io. Rejected: a
  generated artifact in the repository, a diff nobody can review, and ~0.9 MB of churn in git
  history per UI change.
- **Serve the gzipped bytes on the wire** with `Content-Encoding`, skipping the startup
  decompression. Rejected as a false economy: the monitor binds localhost, so there is nothing to
  gain on the wire, and it would put content-negotiation into the serving path for a saving of
  3.4 MB of resident memory.
- **Leave it as it is and document the extra step.** Rejected because it was already the situation,
  and the documentation said the opposite.

## Consequences

**Positive.** A downloaded binary is the whole product. The install shrinks to one line, the release
tarball becomes self-sufficient, and the Docker image now exercises the same embedded path a release
binary takes rather than being the one deployment where a stale `--ui-dir` could mask a broken embed.

**Negative.** `cargo install --path` from a clean checkout embeds nothing unless the SPA was built
first, which is why `make install-cli` depends on `web`. A `cargo install kanbanr-cli` from
crates.io has no `web/dist` at all and will produce a monitor-less binary that says so — the
installer and the container image are the paths we support for users. The binary is ~8% larger.

**Trade-off.** Performance Efficiency is spent — a larger artifact, and one decompression at startup
— to buy Interaction Capability: the monitor is simply there.

## Compliance

- `view_daemon::the_monitor_is_served_from_the_binary_with_no_ui_dir` asserts both halves: served
  with no `--ui-dir`, overridden by an explicit one.
- `release.yml` fails a build whose binary is too small to contain the monitor **or** large enough
  to suggest the assets went in uncompressed — the two bounds together assert "present, and
  compressed" (FEAT-084/R-5).
- `release.yml`'s `verify-install` runs the published one-liner in clean containers and asserts the
  monitor is actually served, so the claim is checked from the outside as a stranger would meet it.
- A build with no assets was run deliberately: the binary returned to 12 MB and the daemon printed
  what was missing and how to supply it (FEAT-084/R-3).
