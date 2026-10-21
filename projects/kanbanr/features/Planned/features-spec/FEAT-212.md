# Release stages that act: move main, then tag it

## Why
On 21 Oct 2026 the user set out the release flow they want: the release is merged into main and
pushed, CI runs on that commit, and only then is it tagged. Today the last stage of a release does
both at once: it tags the release tip and fast-forwards main to it, so the tag exists before CI has
seen the commit, and the release workflow then refuses the tag.

The user's request: a release stage should be like an item stage, a status the release enters with
guard rules (as gates are), whose entry does one thing. Entering a stage can merge the release into
main; the final stage (the cut) tags main. Pushing code and tags stays the user's, by hand.

## What it adds (to be designed)
- Release stages declared with conditions and an action, as item gates are, for example:
  - candidate: make `release/<V>` from the line of integration;
  - main: fast-forward main to the release (refused if main has commits the release lacks);
  - production (the cut): tag main, which must be at the release tip and on `origin/main`.
- The Releases page and `release promote` say what each stage will do and what it still needs
  ("push main, then wait for CI").
- The default stages keep today's behaviour.

## Design
_To be written and agreed before build._
