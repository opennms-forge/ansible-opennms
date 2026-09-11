# 🚀 Deployment of OpenNMS with Ansible ✨

[![CI](https://github.com/opennms-forge/ansible-opennms/actions/workflows/ci.yml/badge.svg)](https://github.com/opennms-forge/ansible-opennms/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/opennms-forge/ansible-opennms)](https://github.com/opennms-forge/ansible-opennms/releases/latest)
[![Ansible Galaxy](https://img.shields.io/ansible/collection/v/indigo423/opennms)](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/)
[![License](https://img.shields.io/github/license/opennms-forge/ansible-opennms)](LICENSE)

An Ansible collection that deploys OpenNMS Horizon on Debian and Ubuntu: Core, Minion and Sentinel, plus the system-level configuration that wires them to PostgreSQL, Kafka, Elasticsearch and a Prometheus remote_write store.

The roles configure only what cannot be set from the OpenNMS web UI or its APIs. The collection drives lab deployments and the OpenNMS benchmark rigs; it is still `v0.x` and not yet production-ready, and breaking changes land in minor releases and are called out in the release notes.

🕹️ What it does today:

* Installs Horizon Core, Minion and Sentinel at a pinned version, on one host or spread across several, with the APT sources, JVM tuning, Kafka IPC, database initialisation and firewall rules each one needs
* Ships a reference distributed topology and a colocated test rig as inventories
* Provides stub roles for PostgreSQL, Kafka, Elasticsearch, Mimir, VictoriaMetrics and Pyroscope so a complete stack comes up on a sandbox host. None of them is production-grade
* Generates and vaults database credentials on first use instead of shipping defaults
* Is tested against the current Ubuntu LTS cloud image

🦄 What it does not do yet:

* Back up, restore or upgrade an existing OpenNMS Horizon installation
* Support RHEL-based operating systems

![Repobeats analytics](https://repobeats.axiom.co/api/embed/f81f303e61554ad2e9f66b54cc8e847e593984f8.svg "Repobeats analytics image")

## 📦 Install from Ansible Galaxy

The collection is published as [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/).

```bash
ansible-galaxy collection install indigo423.opennms
```

Or pin a specific version via `requirements.yml`:

```yaml
collections:
  - name: indigo423.opennms
    version: "0.11.0"
```

Reference roles by their fully-qualified name (`indigo423.opennms.<role>`). The three production OpenNMS components each get their own play:

```yaml
- name: Horizon Core
  hosts: core
  become: true
  roles:
    - indigo423.opennms.common
    - indigo423.opennms.opennms_core

- name: Horizon Minion
  hosts: minion
  become: true
  roles:
    - indigo423.opennms.common
    - indigo423.opennms.opennms_minion

- name: Horizon Sentinel
  hosts: sentinel
  become: true
  roles:
    - indigo423.opennms.common
    - indigo423.opennms.opennms_sentinel
```

Each component role pulls in `openjdk`, `opennms_repositories`, `opennms_icmp` and `timesync` via `include_role`, so those don't need to be declared explicitly. Per-role docs live in `roles/<name>/README.md`; configurable variables in `roles/<name>/defaults/main.yml`. See [`RELEASING.md`](RELEASING.md) for the publish flow.

> **`timesync` can fail a deployment.** Unlike the other auto-included roles, it verifies the host clock is synchronised and stops the play when it is not — clock skew between components breaks Kafka RPC expiry, flow timestamps and time-series data. Set `timesync_required: false` to proceed anyway. See [`roles/timesync/README.md`](roles/timesync/README.md).

### 🧪 Non-production testing

For evaluation and CI the collection ships stub roles that stand up the services OpenNMS talks to. **None of these are production-grade** — they're convenient for a working stack on a single sandbox host.

- `indigo423.opennms.stub_pgsql` — PostgreSQL with the OpenNMS database and user provisioned.
- `indigo423.opennms.stub_kafka` — Apache Kafka 4.x in KRaft mode for OpenNMS IPC.
- `indigo423.opennms.stub_elasticsearch` — single-node Elasticsearch for flow data.
- `indigo423.opennms.stub_mimir` — Grafana Mimir for time-series storage. Installs through `indigo423.grafana.mimir` and adds what OpenNMS needs on top.
- For Grafana, install the [`indigo423.grafana`](https://galaxy.ansible.com/ui/repo/published/indigo423/grafana/) collection, a fork of `grafana.grafana`, and run `indigo423.opennms.grafana_provisioning` afterwards to enable the OpenNMS plugin. There is no `stub_grafana` — that role was replaced by the external collection.

For real deployments, plug in your own PostgreSQL, Kafka, Elasticsearch, and Grafana roles instead of the stubs.

## 🗺 Shipped inventories

Four inventories ship with the source repository.

| File | What it is | What it expects of you |
|---|---|---|
| `inventory/opennms-stack.yml` | **The reference topology.** Database, Kafka broker, Core and Minion on four separate hosts, with every endpoint and reachability value filled in. Deploys unedited once the addresses are yours. | Replace the four `ansible_host` addresses; narrow `postgres_hba_permissions_v4` to your network. |
| `inventory/simple-stack.yml` | A test rig that colocates every service on one host. Every endpoint stays at `localhost`, so it needs no name resolution. A colocated Minion has no segment to isolate, so this is not a deployment pattern. | Replace the one `ansible_host` address, and set a Grafana admin password (`grafana_ini.security.admin_password`) or drop the `grafana` group. |
| `inventory/minion.yml` | A Minion on its own, for adding a site to a Core that already exists. | Replace the address and point the Minion's Kafka bootstrap servers at your broker. |
| `inventory/smoke-orbstack.yml` | A local single-machine smoke test against an OrbStack machine. | Nothing, if you have OrbStack; it is not meant as an example. |

Endpoints are declared in the inventory, next to the hosts they name, rather than derived inside the roles.
Each role keeps a literal default, so a role installed on its own from Galaxy behaves the same whether or not an inventory group of a given name exists.
Cluster *shape* is the opposite case and is derived by the roles from group membership, because the group is the only thing that knows which hosts are members.

Each dependency endpoint has one variable that carries it:

| Dependency | Consumed by | Variable | Role default |
|---|---|---|---|
| PostgreSQL | `opennms_core`, `opennms_sentinel` | `opennms_datasource_db_host` (plus `_port`, `_name`) | `localhost` |
| Kafka | `opennms_core` | `opennms_properties_message_broker["org.opennms.core.ipc.kafka.bootstrap.servers"]` | `localhost:9092` |
| Kafka | `opennms_minion` | `opennms_minion_kafka["bootstrap.servers"]` | `localhost:9092` |
| Kafka | `opennms_sentinel` | `opennms_sentinel_kafka["bootstrap.servers"]` | derived from the `message_broker` group |
| Elasticsearch | `opennms_core` or `opennms_sentinel` | `opennms_elastic_flows.elasticUrl` | unset — flows off |
| Mimir / VictoriaMetrics | `opennms_core` | `opennms_remotewrite.write_url`, `.read_url` | `http://localhost:8080/…`, disabled |

Two server-side settings decide whether those endpoints work at all, and both live with the service rather than with its client:
`postgres_listen_addresses` and `postgres_hba_permissions_v4` on the database host, and `kafka_server_properties["advertised.listeners"]` on the broker.
The broker's is an *advertise* address — the one it hands back to a client, which then reconnects to it — so leaving it at `localhost` sends every remote client back to itself.

## 🔐 First-time setup: bootstrap database credentials

The collection ships no plaintext database passwords. Before your first deployment, run the bootstrap playbook against your inventory to generate strong random credentials and store them in an Ansible Vault file:

```bash
ansible-playbook -i <path-to-your-inventory-file> indigo423.opennms.init_secrets
```

Pass a single inventory **file** (not a directory). For multi-inventory setups, run the bootstrap once per inventory, or pass `-e secrets_dest_dir=<path>` to choose where the vault lands explicitly.

The bootstrap:

- Writes a vault password file at `~/.config/ansible-opennms/vault-pass` (mode `0600`). **This file is the master key — back it up to a password manager.** Losing it leaves your encrypted vault unrecoverable.
- Generates random 32-character passwords for `opennms_datasource_db_password` and `postgres_password`.
- Writes them to `<inventory_dir>/group_vars/opennms_stack/vault.yml` (encrypted) and `vars.yml` (references). Commit both files to your inventory.
- Prints the recommended `ansible.cfg` snippet at completion. Add this line under `[defaults]` in your project's `ansible.cfg`, your `~/.ansible.cfg`, OR set it via the `ANSIBLE_VAULT_PASSWORD_FILE` env var:

  ```ini
  [defaults]
  vault_password_file = ~/.config/ansible-opennms/vault-pass
  ```

After this one-time setup, every `ansible-playbook` invocation resolves the vault password automatically — no `--ask-vault-pass` flag required.

### Migration

- **Already overriding credentials in your inventory?** No action required. Your overrides take precedence over the role defaults (which are now sentinel strings that fail the play if not overridden).
- **Relied on the shipped defaults (`p4a55word!`/`oth3rP455w0rd!`)?** Run the bootstrap once. The next playbook run will rotate PostgreSQL via `ALTER USER` and re-populate the OpenNMS Secure Credential Vault.
- **Source-repo developers:** `group_vars/` moved to `inventory/group_vars/`. Re-run the bootstrap if you had committed values in the old location.

### Rotation

Re-run the bootstrap with `-e force_rotate=true` to regenerate the credential values (the vault password file is preserved):

```bash
ansible-playbook -i <inventory> indigo423.opennms.init_secrets -e force_rotate=true
```

Then re-run the deployment playbook to propagate the new values to every consumer:

- `stub_pgsql` (or your own PostgreSQL role) — `ALTER USER` runs against the admin and application roles.
- `opennms_core` — `scvcli set postgres` and `scvcli set postgres-admin` rewrite SCV.
- `opennms_sentinel` — the distributed datasource config file is rewritten.
- The Grafana data source (provisioned via the upstream collection) — re-provisioned with the new value.

### Recovery from a lost vault password file

If `~/.config/ansible-opennms/vault-pass` is gone and you have no backup, the encrypted vault is unrecoverable. Run the bootstrap with `-e force_reinit=true` to regenerate everything:

```bash
ansible-playbook -i <inventory> indigo423.opennms.init_secrets -e force_reinit=true
```

This destroys the existing `vault.yml`. After it completes, you must also reset the PostgreSQL admin password before re-running the deployment, because the database still holds the now-lost password:

- For `stub_pgsql` on a host you control: `sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '<new postgres_password from vault>';"`. Read the new value via `ansible-vault view --vault-password-file ~/.config/ansible-opennms/vault-pass <vault.yml path>`.
- For external PostgreSQL: ask your DBA to reset the admin password to match the new vault value, or accept a database wipe.

## 🎯 Scope

* Gives users the possibility to deploy the components following best-practices
* Given the current contribution and resources, adding OS variants is not such a high priority right now

We are open and welcome constructive contributions. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to get a change merged — commits need a DCO sign-off (`git commit -s`), and AI-assisted work needs an `Assisted-by:` trailer. Questions go where [SUPPORT.md](SUPPORT.md) says; everyone taking part is bound by the [Code of Conduct](CODE_OF_CONDUCT.md).

Found a security issue? Please don't open a public issue — see [SECURITY.md](SECURITY.md).

## 🗺 Design principle

* Only allow configuration of system configuration files that can't be modified from the web user interface or external APIs
* function > variation, better having a smaller crowd with happy people using Debian/Ubuntu as a base OS, than a larger unhappy crowd with support for many other operating systems

## 👋 Say hello

You are very welcome to join us to make this repo a better place.
You can find us at:

* Public OpenNMS [Mattermost Chat](https://chat.opennms.com/opennms/channels/opennms-discussion)
* If you have longer discussions to share ideas use our [OpenNMS Discourse](https://opennms.discourse.group) and tag your post with `sig-ansible`
* If you want to get an idea of what we are working on, have a look at the public [Project board](https://github.com/orgs/opennms-forge/projects/4)

## 📄 License

GPL-3.0-or-later — see [LICENSE](LICENSE).
