# Packages

Shared runtime modules and capability contracts live here.

Current planned modules:

- `contracts/`
- `capabilities/`
- `kernel/`
- `profile/`
- `session/`
- `memory/`
- `evidence/`
- `embeddings/`
- `learning/`
- `context/`
- `models/`
- `auth/`
- `tools/`
- `skills/`
- `gateway_core/`
- `voice/`
- `security/`
- `storage/`
- `telemetry/`

Working rules:

- package boundaries should stay narrower than app boundaries
- prefer contract-first integration over deep imports
- add local `AGENTS.md` files when a package becomes a hotspot with non-obvious rules
