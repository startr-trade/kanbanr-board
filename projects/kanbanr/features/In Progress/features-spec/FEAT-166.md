# Working with Claude describes what the walkthroughs actually showed

## Problem
The *Working with Claude* chapter was written before the FEAT-159 walkthroughs. They showed things
it does not say: why "let's review" asks questions rather than opening plan mode; that one request
can carry an item through several stages in one plan; that a change which restores a definition to
text already approved brings that approval back rather than asking again; and how a custom process
file changed what was asked (When, at its shaping stage).

## Behavior
- The chapter gains a short "What it looked like" section from the walkthroughs: a review answered
  Approve / Change it, the change that restored an earlier approval, one request spanning two
  stages, and the custom process asking When where TOGAF did not.
- It says when plan mode is used (writing or growing a definition) and when a question is (deciding
  on a definition that exists), and why.

## Out of scope
New behaviour; this describes what shipped in v0.1.5.
