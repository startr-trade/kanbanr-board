# Release 1.0.0

## Problem
The 1.0.0 tag is a promise that the stable surface holds. It should be tagged only when there is
reason to believe it: the policy written, every platform's install proven, and a period of real use
in which nothing in that surface had to break.

## Behavior
Tag 1.0.0 when all of these hold, each recorded here with its evidence:
- the stability policy (its item) is done and the installers are verified on every platform (its item);
- at least three weeks have passed since v0.1.2 with no change to a covered surface that would break
  an existing board, script or hook;
- every defect found in that time is fixed or deliberately deferred past 1.0 with a reason;
- someone other than the maintainer has installed it and set up a project, or the maintainer
  explicitly waives that, on the record.
Then: versions to 1.0.0, a dated changelog section, `make ci`, the maintainer tags, the release is
verified.

## Out of scope
New features: they wait for 1.x, except the process library (FEAT-168 to FEAT-171): designing a
process with Claude and saving it on the board or personally. The maintainer chose on 5 Oct 2026
to ship it in 1.0; 1.0 waits for those four items.
