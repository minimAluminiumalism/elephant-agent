# Models Package

This package owns provider-neutral model integration.

## Own Here

- model provider contracts
- provider metadata
- fallback and failure classification
- chat and summarization adapter interfaces
- hosted or provider-neutral embedding result shapes used by model adapters

## Do Not Own Here

- the shared local `elephant-embed` provider registry or service contracts
- planning logic
- memory policy
- app-specific transport code
