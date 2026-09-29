## Problem

The Claude Code PreToolUse guard (`kanbanr git guard`) refused a Bash call that ran a Python heredoc whose *body* contained the words of a git commit (a skill passage documenting `git commit -m "[no-ref] initial commit"`). It answered "This skips the commit hooks", although no commit was being run. The guard tokenises the whole command string, heredoc bodies included. The workaround was to write the script to a file first, which is exactly the kind of friction that teaches people to route around a guardrail (lesson L-3: a guard that matches tokens in prose fires on the text that explains it).

## Behavior

The guard skips heredoc bodies (`<<WORD` … `WORD`, `<<'WORD'`, `<<-WORD`) when looking for a commit invocation; a real `git commit` outside the heredoc in the same command is still checked.

## Out of scope

- Commits run by a script the command executes; the git hooks themselves cover those.