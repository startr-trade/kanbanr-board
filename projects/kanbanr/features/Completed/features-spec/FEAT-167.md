# Defect: the editor tests race on one shared download folder

## Problem
CI on macOS (commit 5eaf0db) failed in `self_update_installs_only_where_the_extension_already_is`
with "No such file or directory" from `install_with(...).unwrap()`. `install_into` writes the
checked `.vsix` into `kanbanr-vsix-<pid>` and removes that folder when it is done. Two calls in
one process share the folder, so the two editor tests, running in parallel, can delete it under
each other: one removes it between the other's `create_dir_all` and `write`. Reproduced locally:
7 failures in 200 runs of `editor::` tests.

Separate `kanbanr editor install` processes have different pids, so users are not affected; the
fault is a red CI run that means nothing.

## Behavior
Each `install_into` call downloads into a folder of its own (pid plus a per-process counter), and
removes only that.

## Out of scope
Any change to how editors are found or the download is checked.
