# Monitor UI as a standalone static bundle, published per release

The monitor UI is embedded in the binary, which is right for local use. It should also be available as a plain static bundle, published with each release, with a configurable API base URL. Then it can be served by any static web host and pointed at a monitor's read API: for example, read-only access for collaborators and reviewers, who should not have to run anything.

Scope:
- A release artifact containing the built UI bundle.
- A runtime setting for the API base URL.
- No server-side rendering.
- The embedded copy stays the default for local use.
