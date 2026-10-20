# Versioned read-API contract for the monitor

The monitor's read routes are currently an internal detail of the bundled UI. The editor extension and other tools that read the board would benefit from a documented, stable contract.

Scope:
- Publish an OpenAPI description of the read-only routes.
- Version it, so a breaking change means a new version.
- Test the server against the description.
- Write routes, where they are enabled, stay out of the public contract.

## Design

### Summary
The daemon answers about 37 read routes today. The HTTP API page documents nine of them, and
several send text labelled `application/json`. This item does four things:
- publishes **OpenAPI 3.1, v1** for a defined set of read routes, the **public** set, generated
  from the Rust response types;
- serves it at `/api/openapi.json`;
- renders it in the docs;
- tests every public route against it, on a fixture board.

Routes outside the public set keep working but are marked **internal**. Write routes stay out
entirely. A breaking change to a public route means v2, under `/api/v2/`.

### Components and files
- `api/crates/kanbanr-core/Cargo.toml`: optional `schemars = "1"` behind a `schema` feature.
- Response types in core gain `#[cfg_attr(feature = "schema", derive(schemars::JsonSchema))]`.
- Untyped `json!` responses become named structs:
  - `ProjectSummary` (made public);
  - `review::ReviewEntry`;
  - `readiness::ReadinessView` / `ProjectReadiness`;
  - `library::ProcessStatus`;
  - `ProcessListing`;
  - `server::Meta`.
- `api/crates/kanbanr-core/src/openapi.rs` (feature `schema`): the route table and the document
  builder.
- `api/crates/kanbanr-server/src/routes.rs`: correct content types for text routes, 404 for an
  unknown read path, and `GET /api/openapi.json`.
- `api/crates/kanbanr-server/tests/contract.rs` (new): the contract test.
- `docs/src/reference/openapi.json` (generated, committed), a rewritten
  `docs/src/reference/http-api.md`, and `docs/src/project/stability.md` (the read API means the
  public v1 routes).
- `scripts/ci_local.py` and `.github/workflows/ci.yml`: "The published OpenAPI matches the code".

### The public v1 set
These are the routes the monitor uses, plus the obvious reads:

| Group | Routes |
|---|---|
| Meta and health | `/api/meta`, `/healthz`, `/api/openapi.json` |
| Projects | `/api/projects`, `/api/projects/{p}` |
| Project views | `/charter`, `/readiness`, `/features/{code}/readiness`, `/review`, `/releases`, `/sprints`, `/sprints/{code}`, `/adrs`, `/lessons`, `/process` |
| Diagrams | `/workflow?format=mermaid` (text/plain), `/gantt` (text/plain) |
| Docs | `/docs`, `/docs/content?path=` (text/markdown), `/docs/raw?path=` (bytes) |
| Activity | `/activity` |
| Export | `/features/{code}/export` (markdown or `?format=json`) |
| Portfolio | `/api/portfolio`, `/rollups`, `/board` |
| Live updates | `/events`, `/api/events` (`text/event-stream`, event `changed`, data: project id or `*`) |

The project views are all under `/api/projects/{p}`. **Internal** (served, not covered): doctor,
query, graph, critical-path, ready/blocked, impact, trace, zachman, retro, report, mirror,
claude-block, processes, and the project-wide export. Open question Q1 is whether some of these
belong in v1.

### Interfaces
```rust
// openapi.rs (feature "schema")
pub struct RouteDoc { pub path: &'static str, pub summary: &'static str, pub params: &'static [Param],
    pub response: Response }
pub enum Response { Json(fn(&mut SchemaGenerator) -> Schema), Text(&'static str /*mime*/), Bytes, Sse }
pub fn public_routes() -> Vec<RouteDoc>;
/// The OpenAPI 3.1 document for v1, deterministic (sorted keys) so it can be committed and diffed.
pub fn document() -> serde_json::Value;
```
A small binary, `cargo run -p kanbanr-core --features schema --example openapi`, writes
`docs/src/reference/openapi.json`. The server serves the same bytes, embedded with `include_str!`.

### Behaviour changes on the wire
These are corrections, needed for the contract to be true:
- Mermaid and DOT routes send `text/plain; charset=utf-8`; the project export sends
  `text/markdown` unless `?format=json`.
- An unknown GET path under `/api` returns **404** with a plain-text body (it was 400
  "unsupported operation").
- Errors stay `text/plain` with the documented status mapping (404 / 409 / 400 / 500), now listed in
  the document.

### Test plan
- **R-1: `server::contract_matches_openapi`.**
  - The test builds a fixture board through the CLI (projects, items with definitions, sign-offs, a
    release, a sprint, an ADR, a doc) and starts `kanbanr serve` on a free port, using the existing
    view_daemon.rs helpers.
  - For every public route it checks two things:
    - the status and content type match the document;
    - JSON bodies validate against the schema, using the `jsonschema` crate (dev-dependency, MIT).
  - It also checks that the committed `openapi.json` equals `document()`, so it can't drift.
- Also: the monitor's `api.ts` types and the schema are compared field by field by a check script,
  `web/scripts/check-api-types.mjs`, which reads `openapi.json`, for the routes `api.ts` calls.

### Dependencies
- `schemars 1.x` (MIT), optional in core; it's already in Cargo.lock through a dev dependency.
- `jsonschema` (MIT), dev-only in kanbanr-server.
- deny.toml licence check: permissive.

### Implementation tasks
1. **Typed responses.** Replace each `json!` response on a public route with a named struct in
   core (fields identical to today's JSON). Make `ProjectSummary` public. Tests: the existing
   dispatch tests still pass, plus a JSON equality test per route against today's output. Depends
   on: none.
2. **schemars.** Add the `schema` feature and `cfg_attr` derives on every type reachable from a
   public route (models, config, readiness, releases, sprints, adr, lessons, charter, portfolio,
   docs, activity, library, export). Test: `cargo build --features schema`. Depends on 1.
3. **openapi.rs.** Write `public_routes`, `document`, the example binary, and the committed
   `openapi.json`. Test: `openapi::tests::document_is_deterministic`. Depends on 2.
4. **Server.** routes.rs: content types, unknown-path 404, `/api/openapi.json`. Tests: update
   view_daemon.rs expectations (400 to 404). Depends on 3.
5. **Contract test.** kanbanr-server/tests/contract.rs: R-1 and the drift check. Depends on 4.
6. **Monitor types.** `web/scripts/check-api-types.mjs`, wired into `check:ui` (or its own npm
   script) and into ci_local.py and ci.yml. Depends on 3.
7. **Docs.** Rewrite http-api.md (public and internal, versioning, errors, SSE, CORS); render the
   OpenAPI (mdBook include plus a route table generated from the document); update stability.md
   and the CHANGELOG with the docs sync. Depends on 3.

### Decisions (19 Oct 2026: every recommended answer accepted)
- **Q1.** Which routes are public in v1?
  - Decided: the set above, which covers what the monitor uses, the editor extension's needs,
    and the obvious reads.
  - Alternative: all ~37 read routes.
- **Q2.** How should future versions work?
  - Decided: v1 stays at `/api/...`, the paths in use today. A breaking v2 would be added under
    `/api/v2/...`, with v1 kept for a deprecation period, per the stability policy.
- **Q3.** Should an unknown read path return 404 instead of 400?
  - Decided: yes. It's a bug fix, and 1.0 hasn't shipped.

- **Decided during the build (20 Oct 2026):**
  - `/projects/{p}/gates` (FEAT-199) and `/releases/{v}/cut-preview` (FEAT-185) join the public v1
    set: the monitor uses both, which is the public set's rule.
  - `info.version` is the API version, `"1"`, so the committed document does not change on every
    release; the 404 body keeps the wording "unsupported operation: GET /path".
  - Accepted deviations: the contract test builds its fixture through `kanbanr_core::dispatch` (what
    the CLI's local mode writes through) and runs the daemon in-process, because the server crate's
    tests cannot reach the CLI binary; `dispatch_routes_data_operations` now expects `NoSuchRoute`
    (the core side of the 400→404 change), with its message checked unchanged.
  - The review queue's entries are the typed `ReviewEntry`, including FEAT-185's `release_choices`.

### Affects docs
docs/src/reference/http-api.md, docs/src/reference/openapi.json (new), docs/src/project/stability.md,
docs/src/architecture/overview.md.
