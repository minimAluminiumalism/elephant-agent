# Deploy

This directory reserves packaging and deployment topology assets.

Current planned surfaces:

- `docker/`
- `systemd/`
- `cloud/`

Keep runtime topology, service units, and image-facing assets here instead of
scattering them through app code.

Preview baseline:

- `docker/preview.Dockerfile`
- `docker/docker-compose.preview.yml`
- `systemd/elephant-preview.service`

Operator runtime support baseline:

- `docker/runtime-support.Dockerfile`
- `docker/docker-compose.runtime-support.yml`
- `systemd/elephant-runtime-support.service`

Project-ready CLI install baseline:

- `scripts/install.sh`
- `install.sh`

Supported local operator path:

- run the install script from a checked out repo elephant
- let it create a local launcher that points at this checkout
- land users in the CLI first, then birth, health, elephant, elephant management, and grow
- for host-managed service smoke, use the runtime-support topology to run
  `elephant health` inside a container with a mounted durable runtime root

Secret handling rules:

- keep provider credentials in runtime environment variables or secret-manager
  references only
- do not write API keys or bearer tokens into `config.yaml`, deploy manifests,
  fixtures, support bundles, or generated reports
- use `--secret-env-var <ENV_NAME>` during `elephant born --non-interactive ...`
  so persisted configuration keeps only the env reference
- when collecting diagnostics, capture provider id, base URL, model id, and
  health check status, but never shell history, exported values, or copied env
  files

Support-ready validation path:

```bash
bash scripts/install.sh
elephant born
elephant health
elephant herd new demo
elephant herd
elephant grow --elephant-id demo
```

Containerized operator-runtime smoke:

```bash
docker compose -f deploy/docker/docker-compose.runtime-support.yml run --rm runtime-support health
```

If health reports a missing runtime secret, export the named environment
variable in the active shell or service environment and rerun `elephant health`.

Security diagnostics now also expose:

- per-surface approval bundles for `cli.operator`, `gateway.messaging`, and
  `deploy.support`
- redacted support-bundle metadata with provider ids, models, and secret env-var
  aliases only
- explicit reminders that runtime credentials stay outside exported reports

Supported install matrix:

- macOS or Linux
- POSIX shell with `bash`
- `python3` available on `PATH`, or pass `--python /path/to/python`

Default install layout:

- install root: `${HOME}/.elephant`
- launcher dir: `${HOME}/.local/bin`
- durable herd: `<install-root>/herd`
- runtime config: `<install-root>/config.yaml`
- durable skills: `<install-root>/skills`
- installed skills: `<install-root>/skills/installed`
- authored skills: `<install-root>/skills/authored`

Public remote install:

```bash
curl -fsSL https://elephant.agentic-in.ai/install.sh | bash
```

Stable channel override:

```bash
curl -fsSL https://elephant.agentic-in.ai/install.sh | bash -s -- --channel stable
```

Repo-local install:

```bash
bash scripts/install.sh
```

Developer editable install from a checkout:

```bash
python3 -m pip install -e .
```

The editable install also exposes an `elephant` console script. It defaults to the
same local runtime layout as the shipped launcher and can be redirected with
`ELEPHANT_HOME` or `ELEPHANT_HERD_DIR`.

Upgrade in place:

```bash
bash scripts/install.sh upgrade
```

Published package path:

- package name: `elephant`
- pushes to `main` publish a timestamped dev package
- version tags `v*` can publish a stable package and GitHub release
- the public root installer consumes the published package stream rather than a repo tarball

Run the shipped health path:

```bash
bash scripts/install.sh health
```

Failure recovery:

- rerun `bash scripts/install.sh upgrade` to rewrite the launcher
- pass `--install-root` and `--bin-dir` explicitly when the default paths are
  not appropriate
- use the generated `elephant health` output to confirm provider readiness before
  first real use
- keep long-lived service secrets in a host-level environment file or secret
  store, not inline inside a systemd unit or compose manifest
- when validating the support topology, keep provider env vars in
  `/etc/elephant/elephant-runtime.env` or an equivalent operator-managed environment
  file instead of baking them into the image
