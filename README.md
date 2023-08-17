# 🚀 Deployment of OpenNMS with Ansible ✨

Encoding your infrastructure using Ansible is widely adopted.
This repository provides the roles to deploy OpenNMS Horizon components such as:

* OpenNMS Horizon core system
* OpenNMS Minion for monitoring isolated network segments
* OpenNMS Sentinel for scaling workloads in the storage backend

I have started this project recently and is in an early stage and not ready for production use yet.

## 🎯 Scope

* Gives users the possibility to deploy the components following best-practices
* Ubuntu LTS is the base OS for now
* Given the current contribution and resources, adding OS variants is not in scope for now.
We are open and welcome constructive contribution.

## 🗺 Design principle

* Only allow configuration of system configuration files which can't be modified from the web user interface or external API's
* function > variation, better having a smaller crowd with happy people using Debian/Ubuntu as a base OS, than a larger unhappy crowd with support for many other operating systems

## 👋 Say hello

You are are very welcome to join us to make this repo a better place.
You can find us in:

* Public OpenNMS [Mattermost Chat](https://chat.opennms.com/opennms/channels/opennms-discussion)
* If you have longer discussions to share ideas use our [OpenNMS Discourse](https://opennms.discourse.group) and tag your post with `sig-ansible`
* If you want to get an idea what we are working on, have a look at the public [Project board](https://github.com/orgs/opennms-forge/projects/3)
