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
- **The release prepares itself** (the user, 21 Oct 2026, approving FEAT-211): a release is not
  prepared by a separate feature item made for the purpose. Its own state change does it: for
  example, entering the first stage commits the version bump, the changelog heading and a notes
  draft (from its items) onto `release/<V>`, which kanbanr may write although people may not.
  FEAT-207 and FEAT-211 are the redundancy this removes.

- **One click to cut** (the user, 21 Oct 2026, cutting 0.2.1): today "Promote to production (cut)"
  opens a second panel with a "Cut <V>" button. The cut's button should say what it does ("Cut
  v0.2.1") and show its preview (the commit it will tag, what ships and what carries over) beside
  it, so one click cuts. The stage's conditions (main at the release tip, on `origin/main`) are what
  keep it safe: the button is offered only once they hold, and says what is missing until then.

## As lived with 0.2.1 (21 Oct 2026)
Stages `candidate, production`. Promote to candidate made `release/v0.2.1` from `sprint/SP-001`;
main was fast-forwarded to it by hand; the user pushed main and CI went green; the cut tagged
`0685a5b`, which main already was; the user pushed the tag and the release ran green. The manual
fast-forward, the separate release-prep item (FEAT-211) and the second confirmation click are what
this item removes.

## Design
_To be written and agreed before build._
