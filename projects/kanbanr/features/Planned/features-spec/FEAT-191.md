# Git drift check

`kanbanr git doctor`, also run by `kanbanr doctor` when the git model is in use, reports:
- items in the integrate role whose branch is not merged into the line of integration;
- commits on a line of integration whose item is not at integrate or later;
- item branches whose item is finished or parked;
- branches that name no item;
- release branches whose fixes have not been merged forward.
