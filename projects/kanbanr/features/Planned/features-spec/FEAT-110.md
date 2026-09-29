## Problem

`kanbanr git status | head -3` (and any command piped into something that stops reading early) ends with `thread 'main' panicked … failed printing to stdout: Broken pipe (os error 32)`. Rust's `println!` panics on EPIPE. Seen twice in this session's runs; in a Claude session the trace lands in the agent's context and reads like a failure of the command, though the command had succeeded.

## Behavior

When stdout is closed by the reader, the CLI exits quietly with the conventional status for a broken pipe, as `git` and `ls` do, and prints no trace.

## Out of scope

- Changing any command's output.