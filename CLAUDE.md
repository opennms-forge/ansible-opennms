# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ansible collection for deploying OpenNMS Horizon monitoring infrastructure on Debian/Ubuntu systems. Supports single-node and distributed topologies. Not yet production-ready — stub roles (PostgreSQL, Kafka, Elasticsearch, Grafana, Mimir) are for POC/testing only.

**Design constraint**: Roles only configure system-level files, not settings modifiable via web UI or APIs.

## Git Commits

Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/). Format: `<type>[optional scope]: <description>`. Common types: `feat`, `fix`, `docs`, `refactor`, `ci`, `chore`. Breaking changes use `!` after the type (e.g., `feat!:`) or a `BREAKING CHANGE:` footer.

## Linting

```bash
# Install dependencies
pip install ansible-core==2.20.4 ansible-lint==26.3.0
ansible-galaxy collection install -r requirements.yml

# Run linter
ansible-lint
```

The CI workflow (`.github/workflows/ansible-opennms-lint.yml`) runs `ansible-lint` against the `production` profile. Skipped rules are in `.ansible-lint`.

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

**Core OpenNMS components** (production targets):
- `opennms_repositories` — APT repo and GPG key setup; must run before any package install
- `opennms_openjdk` — Installs OpenJDK 17 (required by all OpenNMS components)
- `common` — Timezone, APT cache update, base system packages
- `opennms_core` — OpenNMS Horizon Core (35.0.4): database init, Kafka config, JVM tuning, firewall rules
- `opennms_minion` — Minion agent for isolated network segments
- `opennms_sentinel` — Flow persistence and aggregation
- `opennms_icmp` — ICMP monitoring configuration

**Stub infrastructure roles** (POC/testing only, not production):
- `stub_pgsql` — PostgreSQL 15 with OpenNMS database/user
- `stub_kafka` — Kafka 4.2.0 in KRaft mode
- `stub_elasticsearch` — Elasticsearch for flow data
- `stub_grafana` — Grafana 12
- `stub_mimir` — Grafana Mimir 3.0.4

### Inventory & Variables

- `inventory/opennms-stack.yml` — Full stack on a single host
- `inventory/simple-stack.yml` — Simplified topology
- `inventory/minion.yml` — Minion-only deployment
- `group_vars/opennms_stack/vars.yml` — Stack-level overrides (see comments in file for all tunables)

Role defaults live in `roles/<role>/defaults/main.yml`.

### Role Task Layout

`opennms_core` tasks are split by concern:
- `01-packages.yml` — Package installation
- `10-database-setup.yml` — PostgreSQL schema init via `community.postgresql`
- `20-config.yml` — Core configuration files
- `21-kafka.yml` — Kafka IPC configuration
- `50-firewall.yml` — UFW rules

Templates for OpenNMS config go in `roles/opennms_core/templates/etc/opennms.properties.d/`.

### Dependencies

External collections (`requirements.yml`):
- `community.postgresql` v4.2.0 — used by `stub_pgsql` and `opennms_core` for database setup
- `community.general` v12.5.0 — general utilities

## Key Versions

| Component | Version |
|-----------|---------|
| OpenNMS Horizon | 35.0.4 |
| PostgreSQL | 15 |
| Kafka | 4.2.0 (KRaft) |
| OpenJDK | 17 |
| Grafana | 12.x |
| Grafana Mimir | 3.0.4 |
| Prometheus JMX Exporter | 1.5.0 |
