# Feature-Complete Checklist

Use this checklist before calling a change complete:

- the landing surface is explicit and the change does not sprawl across unrelated areas
- the smallest relevant validation gate has passed
- docs changed with the executable contract when the harness changed
- commit history can be split into atomic units with meaningful messages
- repo-visible completed work has been shipped with `make agent-ship ...`, unless publish was explicitly deferred or the diff still needs to be split
- long-horizon follow-ups are captured in `plans/` or `tech-debt/`, not implied in chat
- PR-facing context can be understood without access to hidden conversation state
- for active waves, the main session has decomposed the ready work into the broadest safe parallel set the write scopes allow
- for active waves, each launched lane has an explicit task card, write scope, validation command, and ship path
