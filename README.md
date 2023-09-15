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
* If you want to get an idea of what we are working on, have a look at the public [Project board](https://github.com/orgs/opennms-forge/projects/3)
