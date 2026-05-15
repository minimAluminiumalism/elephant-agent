# Release Model

## Current Posture

The repo now has staged release automation around the current runtime surface:

1. `make build-and-test` powers the default push/PR CI contract in `.github/workflows/ci.yml`
2. `make e2e` powers the deterministic e2e matrix in `.github/workflows/deploy-preview.yml`
3. `make release` powers deterministic release certification in `.github/workflows/release-certification.yml`
4. `make design-closure` preserves the stronger operator-managed design-closure certification path
5. `make test-live-provider-smoke` is the optional secret-backed installed
   command smoke for release/design-closure workflow dispatches
6. `.github/workflows/pypi-publish.yml` is the publish path for packaged Python artifacts and release assets

## What Counts As Release-Ready Today

- build-and-test is green on the candidate diff
- deterministic e2e and release certification are green for the candidate surface
- packaged artifacts build cleanly and pass install-surface verification
- the manual live-provider smoke has been run when certifying a configured
  operator provider or installed-command regression
- changelog and user-facing install paths remain understandable
- any remaining gap is recorded in `docs/agent/tech-debt/`

## Future Extension Points

- prerelease channels for unstable runtime surfaces
- automated changelog or release-note generation
- artifact signing or provenance once publish targets are fully locked
