# Monitor UI as a standalone static bundle, published per release

The monitor UI is embedded in the binary, which is right for local use. It should also be available as a plain static bundle, published with each release, with a configurable API base URL. Then it can be served by any static web host and pointed at a monitor's read API: for example, read-only access for collaborators and reviewers, who should not have to run anything.

Scope:
- A release artifact containing the built UI bundle.
- A runtime setting for the API base URL.
- No server-side rendering.
- The embedded copy stays the default for local use.

## Design

### Summary
Each release attaches `kanbanr-monitor-<tag>.tar.gz`: the built monitor, with relative asset paths,
plus a `config.json` the host edits. The monitor reads that file at startup:
- `apiBase`: where the read API is;
- `routing`: `hash` for a plain static host, which needs no rewrite rule;
- `readOnly`: hides the decision buttons.

The binary's embedded copy keeps today's behaviour: same origin, `/api`, history routing, buttons
when the daemon allows writes. The daemon already sends permissive CORS, so a monitor on another
origin can read it and receive SSE.

### Components and files
- `web/vite.config.ts`: `base: "./"` (relative asset URLs; the embedded server keeps serving
  `/assets/*`).
- `web/public/config.json` (new, shipped defaults): `{"apiBase": "/api", "routing": "browser",
  "readOnly": false}`.
- `web/src/runtimeConfig.ts` (new): `loadConfig(): Promise<RuntimeConfig>`,
  `apiUrl(path: string): string`, `isReadOnly(): boolean`, `routing()`.
- `web/src/api.ts`: every URL goes through `apiUrl("/projects/…")`, with no literal `/api` left.
  `EventSource` URLs too.
- `web/src/main.tsx`: awaits `loadConfig()`, then builds `createHashRouter` or `createBrowserRouter`.
- Decision buttons (ReviewPage, FeaturePage) are hidden when `isReadOnly()`.
- FEAT-181's board-reference links go through the router's `useHref`, so they work in hash mode.
- `.github/workflows/release.yml`: a new job, `monitor`, builds `web/dist` once, packs it as
  `kanbanr-monitor-<tag>.tar.gz` with `config.json` set to the standalone defaults
  (`{"apiBase": "http://localhost:8080/api", "routing": "hash", "readOnly": true}`), and stages it
  as artifact `dist-monitor`. The `release` job attaches it, and `SHA256SUMS` covers it.
- `scripts/check-monitor-bundle.sh` (new): verifies an archive. It must contain `index.html`, which
  references only relative `./assets/…`; `config.json`, which parses and has `apiBase`; and assets.
  The release job runs it, and ci_local.py runs it as a LOCAL step.
- `api/crates/kanbanr-server/src/lib.rs`: under `--ui-dir`, serve any file that exists in the dir,
  not only `/assets`. This fixes the favicon falling back to index.html.
- Docs: `docs/src/using/the-monitor.md` gets "Hosting the monitor elsewhere": unpack, edit
  `config.json`, serve; a reverse-proxy or CORS note; read-only by default.

### Behaviour
- `loadConfig` fetches `./config.json` relative to `document.baseURI`. If it's missing or invalid,
  it uses the defaults; the embedded binary's copy is the shipped default file. `apiBase` has any
  trailing slash removed.
- In hash routing, routes look like `#/p/<project>/feature/<CODE>`. Board links are generated
  through the router, so a hard-coded `/p/…` string inside markdown or HTML is rewritten by the
  FEAT-181 renderer to its hash equivalent.
- In read-only mode, a decision shows the matching CLI command, as today's read-only daemon does.
- The bundle is built once per release, not per binary leg. Its contents match what the binaries
  embed: the same commit, and `npm ci` from the same lockfile.

### Security
The bundle has no secrets. With `readOnly` it never calls a write route. Pointing a public site at a
daemon is the host's decision: the docs say the daemon is read-only unless started with
`--allow-writes`, and that it binds to localhost by default.

### Test plan
| Req | Test | Where |
|---|---|---|
| R-1 | `release::ui_bundle_attached`: `scripts/check-monitor-bundle.sh` on the packed archive (LOCAL in make ci); the release job runs it before staging, and a release-page asset check after publishing (manual on the first release) | scripts, release.yml |
| R-2 | `web::api_base_url_configurable`: `web/scripts/check-api-base.mjs` imports `runtimeConfig.ts`/`api.ts` with `apiBase` set to `https://example.test/x/api` and asserts every URL builder (including `EventSource` URLs) starts with it; it also fails if any source file other than runtimeConfig.ts contains a literal `"/api` | web/scripts |
Also: view_daemon.rs `the_monitor_is_served_from_the_binary_with_no_ui_dir` still passes with
`base: "./"`, which needs the SPA fallback for deep links with relative assets. A favicon test
under `--ui-dir`.

### Compatibility
Embedded behaviour is unchanged for users. With relative asset paths, a deep link such as
`/p/x/feature/Y` loads `./assets/…` relative to the page, so the base must resolve correctly.
`index.html` therefore gets `<base href="/">` in the embedded build, injected by the server when it
serves `index.html`, and a standalone bundle has no `<base>`. **Q2** asks whether that approach is
acceptable.

### Implementation tasks
1. **Runtime config.** runtimeConfig.ts; public/config.json; main.tsx awaits config and picks the
   router. Check: build. Depends on: none.
2. **api.ts.** Route all URLs through `apiUrl`; hide buttons when read-only. Test: R-2 check
   script. Depends on 1.
3. **Relative build and base.** vite `base: "./"`; the server injects `<base href="/">` into the
   index.html it serves (both modes); `--ui-dir` serves any existing file. Tests: view_daemon.rs
   deep-link and favicon tests. Depends on 1.
4. **Bundle script.** scripts/check-monitor-bundle.sh, plus a `make monitor-bundle` target that
   packs `web/dist` with standalone config.json. Test: R-1 locally. Depends on 3.
5. **Release job.** release.yml `monitor` job; the `release` job downloads `dist-monitor`;
   ci_local.py PLAN entries (Build: LOCAL, Pack: LOCAL, Check: LOCAL). Test: make ci. Depends on 4.
6. **Docs.** the-monitor.md hosting section; release-notes mention; CHANGELOG with the docs sync.
   Depends on 5.

### Decisions (19 Oct 2026: every recommended answer accepted)
- **Q1.** Should the standalone bundle default to read-only, with buttons hidden?
  - Decided: yes. Reviewers view; decisions happen in Claude Code or with the writes-enabled
    local monitor.
- **Q2.** How should deep links resolve relative assets?
  - Decided: inject `<base href="/">` server-side for the embedded copy.
  - Alternative: keep absolute assets in the embedded build and do a second relative build only
    for the bundle. That doubles the web build and can drift.

### Affects docs
docs/src/using/the-monitor.md, docs/src/reference/http-api.md (CORS note).
