# Security Policy

## Reporting a vulnerability

**Please do not open a public issue for a security vulnerability.**

Use GitHub's private vulnerability reporting, which is enabled on this repository:

👉 [Report a vulnerability](https://github.com/opennms-forge/ansible-opennms/security/advisories/new)

That creates a private advisory visible only to the maintainers. From there we can discuss the report, prepare a fix, and coordinate disclosure without the details being public first.

Expect an acknowledgement within a week. This is a small project maintained in spare time — if you have heard nothing after that, a nudge is welcome.

Please include enough to reproduce: the collection version, the target distribution, the roles involved, and what an attacker gains.

## Scope

This repository is an Ansible collection. It configures software it does not ship.

**In scope** — anything this collection does wrong:

- A role installing a package repository key without verifying it, or verifying the wrong property.
- Credentials written to a world-readable path, logged, or committed as a default.
- A download that is not pinned or not verified, or one that could be substituted.
- A role granting broader privileges, permissions, or firewall exposure than the task requires.
- Template output that lets an inventory value inject configuration it should not.

**Out of scope** — report these to the relevant upstream project:

- Vulnerabilities in OpenNMS Horizon, PostgreSQL, Kafka, Elasticsearch, Grafana, Mimir or VictoriaMetrics themselves. This collection only installs them.
- Findings that require an attacker to already control the Ansible control node or hold root on the target. At that point the deployment is over.
- The `stub_*` roles being unsuitable for production. They are explicitly POC and testing scaffolding, documented as such, and are not hardened. A report that a stub is not production-grade is a known limitation, not a vulnerability — though a stub doing something *actively unsafe* still is.

## Supported versions

Only the latest release receives fixes. There are no maintenance branches, and older versions are not backported to. If you are on an older version, upgrading is the fix.

| Version | Supported |
|---------|-----------|
| latest release | ✅ |
| anything older | ❌ |

## Dependency vulnerabilities

Dependency updates are automated with Renovate, and GitHub Actions are pinned to commit SHAs. If you spot a vulnerable pinned dependency that automation has missed, a normal public issue is fine — a known-published CVE in a pinned version is not sensitive information.
