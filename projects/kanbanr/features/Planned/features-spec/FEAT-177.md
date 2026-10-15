# Versioned read-API contract for the monitor

The monitor's read routes are currently an internal detail of the bundled UI. The editor extension and other tools that read the board would benefit from a documented, stable contract.

Scope:
- Publish an OpenAPI description of the read-only routes.
- Version it, so a breaking change means a new version.
- Test the server against the description.
- Write routes, where they are enabled, stay out of the public contract.
