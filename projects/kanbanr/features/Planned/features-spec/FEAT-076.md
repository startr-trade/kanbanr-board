# Defect: the review page is hard to read and its action is hard to find

## Problem
Two faults reported from using the page to approve twelve definitions:

1. **One item runs into the next.** Each brief is a plain `section`, so a queue of items reads as one long column of prose with no boundary between them. There is nothing to collapse, so reviewing the twelfth means scrolling past eleven.
2. **The approve action does not look like an action.** It was given `className="chip"` — the stylesheet's *label* style, used for tags and states — while a `.btn` class already existed for exactly this. A primary action styled as a label is not identifiable as clickable.

The second is the more serious: the approval gate's premise is that agreeing must be cheap, and an action nobody can find is not cheap.

## Behavior
- Each item is a collapsible card with a summary line carrying its code, title and approval state, so the queue reads as a list and one item is plainly separate from the next. Collapsed by default, with the first expanded so the page does not look inert.
- The approve action uses the button style, with a primary variant that is visibly an action, and it sits inside the expanded body — approving should require having read the brief.
- The withdraw action on the feature page gets the same treatment, for the same reason.

## Out of scope
A redesign of the page's typography or the chip vocabulary; this is about separation and affordance only.