# Dashboard ordering & pagination

Display feature cards on the board in **reverse chronological order** (newest first) within each
status column, and add an **items-per-page** selector (10 / 25 / 50 / All) that applies across all
status columns; each column paginates independently with prev/next controls when it overflows.
Web-only; the page-size choice is remembered (localStorage).