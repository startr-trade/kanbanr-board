# Defect: make ci's monitor test sometimes finds no embedded monitor

## Problem
`the_monitor_is_served_from_the_binary_with_no_ui_dir` failed in `make ci` twice (FEAT-152's and
FEAT-164's first runs, both right after a version change) with a 404 for `/`: the binary under test
had no monitor embedded. Re-running `make ci` passed both times, and it has never failed on GitHub,
where every runner builds `web/dist` before compiling anything. The suspicion is `make ci`'s kept
`api/target`: a binary compiled while `web/dist` was absent (the tree is cleaned between jobs) is
reused when it should be rebuilt. Not yet confirmed.

## Behavior
- Find the sequence that produces a binary without the monitor, and make `make ci` rebuild the
  embed whenever `web/dist` changes or appears.
- The test names the cause when it fails ("the binary carries no monitor"), not a bare 404.

## Out of scope
The release build, which builds `web/dist` first on a fresh runner.
