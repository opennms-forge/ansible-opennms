![Alt](https://repobeats.axiom.co/api/embed/f81f303e61554ad2e9f66b54cc8e847e593984f8.svg "Repobeats analytics image")

# 🚀 Deployment of OpenNMS with Ansible ✨

Encoding your infrastructure using Ansible is widely adopted.
This repository provides the roles to deploy OpenNMS Horizon components such as:

* OpenNMS Horizon core system
* OpenNMS Minion for monitoring isolated network segments
* OpenNMS Sentinel for scaling workloads in the storage backend

I have started this project recently.
It is in an early stage and not ready for production use yet.

🕹️ What you can do as it is right now:

* Install Horizon Core, Minion, Sentinel with PostgreSQL and Kafka on a single or distributed node setup
* We have stub roles for the PostgreSQL database and Kafka. If you run PostgreSQL and Kafka in production, you need appropriate Ansible roles to manage that.
* Minion, Horizon can be configured using Kafka
* Roles are tested with the latest Ubuntu LTS cloud image

🦄 What doesn't work yet and would be cool if it would :)

* Flows with Elasticsearch, we can use a simple stub role to deploy a single node Elasticsearch instance and configure NetFlow integration for it
* Sentinel configuration for Flow persistence with Kafka
* Backup, Restore, Upgrade OpenNMS Horizon
* Supporting a RHEL-based operating system

## 📦 Install from Ansible Galaxy

The collection is published as [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/).

```bash
ansible-galaxy collection install indigo423.opennms
```

Or pin a specific version via `requirements.yml`:

```yaml
collections:
  - name: indigo423.opennms
    version: "0.3.2"
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

Each component role pulls in `openjdk`, `opennms_repositories`, and `opennms_icmp` via `include_role`, so those don't need to be declared explicitly. Per-role docs live in `roles/<name>/README.md`; configurable variables in `roles/<name>/defaults/main.yml`. See [`RELEASING.md`](RELEASING.md) for the publish flow.

### 🧪 Non-production testing

For evaluation and CI the collection ships stub roles that stand up the services OpenNMS talks to. **None of these are production-grade** — they're convenient for a working stack on a single sandbox host.

- `indigo423.opennms.stub_pgsql` — PostgreSQL with the OpenNMS database and user provisioned.
- `indigo423.opennms.stub_kafka` — Apache Kafka 4.x in KRaft mode for OpenNMS IPC.
- `indigo423.opennms.stub_elasticsearch` — single-node Elasticsearch for flow data.
- `indigo423.opennms.stub_mimir` — Grafana Mimir for time-series storage.
- For Grafana, install the upstream [`grafana.grafana`](https://galaxy.ansible.com/ui/repo/published/grafana/grafana/) collection and run `indigo423.opennms.grafana_provisioning` afterwards to enable the OpenNMS plugin. There is no `stub_grafana` — that role was replaced by the external collection.

For real deployments, plug in your own PostgreSQL, Kafka, Elasticsearch, and Grafana roles instead of the stubs.

## 🎯 Scope

* Gives users the possibility to deploy the components following best-practices
* Given the current contribution and resources, adding OS variants is not such a high priority right now

We are open and welcome constructive contributions.

## 🗺 Design principle

* Only allow configuration of system configuration files that can't be modified from the web user interface or external APIs
* function > variation, better having a smaller crowd with happy people using Debian/Ubuntu as a base OS, than a larger unhappy crowd with support for many other operating systems

## 👋 Say hello

You are very welcome to join us to make this repo a better place.
You can find us at:

* Public OpenNMS [Mattermost Chat](https://chat.opennms.com/opennms/channels/opennms-discussion)
* If you have longer discussions to share ideas use our [OpenNMS Discourse](https://opennms.discourse.group) and tag your post with `sig-ansible`
* If you want to get an idea of what we are working on, have a look at the public [Project board](https://github.com/orgs/opennms-forge/projects/4)
