# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ansible collection for deploying OpenNMS Horizon monitoring infrastructure on Debian/Ubuntu systems. Supports single-node and distributed topologies. Not yet production-ready — stub roles (PostgreSQL, Kafka, Elasticsearch, Grafana, Mimir, VictoriaMetrics) are for POC/testing only.

**Design constraint**: Roles only configure system-level files, not settings modifiable via web UI or APIs.

## Git Workflow

**Never push directly to `main`.** All changes must go through a feature branch and Pull Request for review.

```bash
# Create a branch, make changes, then open a PR
git checkout -b <type>/<short-description>
# ... make changes, commit ...
gh pr create
```

## Git Commits

Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/). Format: `<type>[optional scope]: <description>`. Common types: `feat`, `fix`, `docs`, `refactor`, `ci`, `chore`. Breaking changes use `!` after the type (e.g., `feat!:`) or a `BREAKING CHANGE:` footer.

## Linting

```bash
# Install dependencies
pip install -r requirements-dev.txt
make deps

# Run linter
ansible-lint
```

CI runs `.github/workflows/quality-gates.yml`, called by `ci.yml` on every PR and push to main and by `galaxy-release.yml` before publishing: `make lint` (production profile, skipped rules in `.ansible-lint`), `make check-credentials`, `make check-urls`, `make check-render`, plus actionlint and zizmor on the workflows themselves. `make verify` runs the first four locally.

## Running Playbooks

```bash
# Full stack deployment (single host)
ansible-playbook -i inventory/opennms-stack.yml opennms-playbook.yml

# Local test
ansible-playbook -i inventory/opennms-stack.yml site.yml

# Targeted deployments
ansible-playbook -i inventory/opennms-stack.yml hzn-core-db-deployment.yml
ansible-playbook -i inventory/opennms-stack.yml hzn-minion-deployment.yml
ansible-playbook -i inventory/opennms-stack.yml hzn-sentinel-deployment.yml
```

## Architecture

### Roles

**Scope rule.** A role belongs in this collection only if OpenNMS has a wire to
the system it deploys — a database it queries, a broker it publishes to, a store
it writes to. Systems OpenNMS is *measured against* do not belong here, however
convenient it would be to reuse the stub pattern; they belong in the benchmark
repository (`opennms-forge/opennms-benchmark`, under `deployments/roles/`).
Every role below fits one of the three buckets; if a proposed role fits none of
them, that is the signal.

**Core OpenNMS components** (production targets):
- `opennms_repositories` — APT repo and GPG key setup; must run before any package install
- `openjdk` — Installs OpenJDK 21 for OpenNMS components and Kafka
- `common` — Timezone, APT cache update, base system packages
- `timesync` — Verifies the host clock is synchronised; included by the three component roles and fails the play on skew (`timesync_required` to override)
- `opennms_core` — OpenNMS Horizon Core (36.0.4): database init, Kafka config, JVM tuning, firewall rules
- `opennms_minion` — Minion agent for isolated network segments
- `opennms_sentinel` — Flow persistence and aggregation
- `opennms_icmp` — ICMP monitoring configuration
- `pyroscope_agent` — Installs the pinned Grafana Pyroscope Java agent jar; included by the three component roles, which each wire it into their own JVM

**Stub infrastructure roles** (POC/testing only, not production):
- `stub_pgsql` — PostgreSQL 18 with OpenNMS database/user
- `stub_kafka` — Kafka 4.2.0 in KRaft mode; single broker, or a cluster derived from `kafka_cluster_group`
- `stub_elasticsearch` — Elasticsearch for flow data; single node, or a cluster derived from `es_cluster_group`
- `stub_mimir` — Grafana Mimir; single-node monolithic, or distributed via memberlist with shared S3 storage (`mimir_s3_endpoint`). A wrapper: it keeps the start-limit drop-in, the ring addressing and the group-derived cluster shape, and delegates package, config file, restart and readiness to `indigo423.grafana.mimir`
- `stub_victoriametrics` — VictoriaMetrics 1.150.0, single-node
- `stub_pyroscope` — Grafana Pyroscope 2.3.1, single-node monolithic; receives the profiles the Horizon components push via `pyroscope_agent`

Multi-node roles derive their cluster shape from inventory group membership, so
scaling a deployment is the only change needed. A single-member group renders
exactly as it did before clustering was added.

**External collection roles** (replacing stubs where mature alternatives exist):
- `indigo423.grafana.grafana` — Grafana 13.x (replaces `stub_grafana`); a fork of `grafana.grafana` published under the `indigo423` namespace; configured via `inventory/group_vars/grafana/vars.yml`
- `grafana_provisioning` — Drops the `opennms-opennms-app` plugin provisioning file; runs after `indigo423.grafana.grafana` since the collection installs the plugin but does not enable it

### Inventory & Variables

- `inventory/opennms-stack.yml` — The reference topology: database, broker, Core and Minion on four separate hosts, endpoints and reachability values filled in
- `inventory/simple-stack.yml` — Colocated test rig, everything on one host, every endpoint left at `localhost`
- `inventory/minion.yml` — Minion-only deployment
- `inventory/smoke-orbstack.yml` — Local single-machine smoke test against OrbStack
- `inventory/group_vars/opennms_stack/vars.yml` — Stack-wide values only: the vault-backed credentials, plus documentation of the per-feature tunables

Role defaults live in `roles/<role>/defaults/main.yml`.

**Endpoints and cluster shape.** These are different kinds of fact and they are declared in different places, which is deliberate.

*Endpoints* — the database host, Kafka bootstrap servers, `elasticUrl`, the remote_write URLs — are declared in the inventory, in each inventory file's own group `vars:` blocks.
Roles keep literal defaults (`opennms_datasource_db_host: localhost`) and look up no groups, so a role installed standalone from Galaxy has no behaviour that depends on an inventory group's name.
Past the POC case a service endpoint is not a host at all: it is a VIP, a connection pooler or a DNS name, none of which appear in an inventory, so deriving one in a role would be right only for the toy topology.

*Cluster shape* — which hosts form the Kafka quorum, the Elasticsearch seed list, the Mimir memberlist — is derived by the roles from group membership, because the group is definitionally the answer and nothing else knows it.

`opennms_sentinel`'s Kafka bootstrap list predates this split and derives from `sentinel_kafka_group`.
It is the one endpoint that is genuinely a member set, and it is the only part of issue #171's original proposal worth revisiting.

Per-topology values do not go in `inventory/group_vars/`: all four inventories share that directory, so one topology's addresses would leak into another's.

See issue #171 and `openspec/changes/make-distributed-deployments-viable/design.md` for the full reasoning.

### Role Task Layout

`opennms_core` tasks are split by concern:
- `01-packages.yml` — Package installation
- `03-pyroscope-agent.yml` — Installs the pinned Pyroscope agent over the one the package ships; loading stays opt-in via `PYROSCOPE_AGENT_ENABLED`
- `10-database-setup.yml` — PostgreSQL schema init via `community.postgresql`
- `20-config.yml` — Core configuration files
- `21-kafka.yml` — Kafka IPC configuration
- `22-timeseries-plugin.yml` — Prometheus remote_write time-series plugin (opt-in via `opennms_remotewrite.enabled`)
- `50-firewall.yml` — UFW rules

Templates for OpenNMS config go in `roles/opennms_core/templates/etc/opennms.properties.d/`.

### Dependencies

External collections (`requirements.yml`):
- `community.postgresql` v4.2.0 — used by `stub_pgsql` and `opennms_core` for database setup
- `community.general` v13.3.0 — general utilities
- `indigo423.grafana` v7.2.0 — Grafana and Mimir installation (fork of `grafana.grafana`)

## Key Versions

| Component | Version |
|-----------|---------|
| OpenNMS Horizon | 36.0.4 |
| PostgreSQL | 18 |
| Kafka | 4.2.0 (KRaft) |
| OpenJDK | 21 |
| Grafana | 13.2.1 |
| Grafana Mimir | 3.2.1 (inherited from `indigo423.grafana`; override with `mimir_version`) |
| VictoriaMetrics | 1.151.0 |
| Prometheus JMX Exporter | 1.6.0 |
| OpenNMS Prometheus remote_write plugin | 2.1.0 |
| Pyroscope Java agent | 2.9.2 |
| Grafana Pyroscope (server) | 2.3.1 |
