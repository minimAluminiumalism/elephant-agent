# Dashboard App

This surface owns the local inspection console UI.

## Own Here

- Vite/React dashboard screens and navigation
- dashboard-only presentation state
- API client code for local inspection endpoints
- frontend build and typecheck wiring

## Do Not Own Here

- API route behavior
- kernel, storage, or Personal Model policy
- background learning execution
- provider or credential logic

Keep the dashboard an inspection surface over API/package contracts. Do not
fork runtime truth into frontend-only state.
