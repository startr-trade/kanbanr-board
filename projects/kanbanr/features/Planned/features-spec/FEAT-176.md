# Refactor: domain logic lives in kanbanr-core; front ends are thin wrappers

kanbanr-cli carries a large share of the code (about 12k lines, against about 25k in kanbanr-core). Some of it is behaviour rather than argument parsing and output formatting. Every front end (CLI, monitor server, editor extension, any future one) should get identical behaviour from one library, and each should be packageable on its own.

Scope:
- Move domain behaviour from kanbanr-cli into kanbanr-core's public API. kanbanr-cli keeps argument parsing, output rendering and process concerns only.
- Keep kanbanr-server equally thin.
- Add an architecture test that fails when a front-end crate implements domain logic, measured by imports of core internals or of parser and validation code outside the public API.
