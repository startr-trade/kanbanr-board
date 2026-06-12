# Getting started

```bash
make install                 # build + install the `kanbanr` binary and the Claude skill
kanbanr init my-app --author "You" --email you@example.com
kanbanr milestone add --name Foundations --code MS-001
kanbanr feature add --title "Login flow" --milestone MS-001 --spec "# Login"
kanbanr serve --ui-dir web/dist   # optional read-only monitor on http://localhost:8080
```

Then, in Claude: say **"start using kanbanr for this project"** and it adopts the board as the
single system of record.
