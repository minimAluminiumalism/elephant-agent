# CLI App

This surface is the primary proving ground for the Elephant Agent thesis.

## Own Here

- chat and wake UX
- elephant management UX
- recall, understanding, and runtime inspection UX
- skills, tools, providers, and models management
- local operator workflows
- the `v1.0.0` interactive stack choice: `prompt_toolkit + rich`
- the direct conversational shell model for the project-ready release

## Do Not Own Here

- State, Episode, Loop, Step, and Fact ownership policy
- Personal Model formation policy
- provider auth logic
- removed product-facing reset-era system-layer terms or planning semantics

The CLI should call into the kernel and render state clearly; it should not fork core behavior.

For `v1.0.0`, prefer:

- `prompt_toolkit` for input, key handling, history, completions, and the
  interactive event loop
- `rich` for structured rendering and operator-facing output
- a direct transcript-first shell over a dashboard-style terminal layout
- progressive disclosure instead of always-visible command browsers and
  persistent side panels
- a minimal required shortcut surface; no core flow should depend on memorizing
  product-specific key chords

Do not introduce `Textual` as a competing primary interaction stack during the
project-ready train.
