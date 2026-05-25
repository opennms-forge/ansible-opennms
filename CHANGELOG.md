# Changelog

All notable changes to the `indigo423.opennms` collection are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Each entry below is a short index; the corresponding GitHub release contains the full notes including the Component Versions table and upgrade instructions.

## [0.3.1] - 2026-05-25

### Changed
- First release published automatically to Ansible Galaxy as `indigo423.opennms` via the `galaxy-release` workflow introduced in #85. No role or runtime changes from v0.3.0.

## [0.3.0] - 2026-05-25

### Changed
- Bump OpenNMS Horizon from `35.0.5` to `36.0.0` for the `opennms_core`, `opennms_minion`, and `opennms_sentinel` roles.
- Bump OpenJDK from `17` to `21` across all OpenNMS roles (Horizon 36's dpkg postinst fails on JDK 17). The `openjdk` role default also flips to `21`.
- Bump the `grafana.grafana` collection to `6.1.0` and `community.general` to `12.6.0`.

### Fixed
- `opennms_minion`: allow inbound syslog on `10514/udp` (#82).
- `grafana`: pin `grafana_version` to `12.4.3` pending the upstream Grafana 13 plugin-install fix (#81). Tracks https://github.com/grafana/grafana-ansible-collection/issues/497.

## [0.2.0] - 2026-04-17

### Changed
- `grafana`: bump `grafana_version` from `12.4.2` to `13.0.1` (#80) to track the upstream APT repo's current stable.

## [0.1.0] - 2026-04-10

### Added
- Initial release of the collection. Deploys OpenNMS Horizon Core, Minion, and Sentinel on Debian/Ubuntu, with stub roles for PostgreSQL, Kafka, Elasticsearch, and Grafana Mimir.
- Grafana integration via the upstream `grafana.grafana` collection plus an `opennms-opennms-app` provisioning role (replaces the prior `stub_grafana` role).
- `opennms_repositories` migrated to `debian.opennms.org` with non-interactive GPG dearmor.
- Per-role JDK pinning to prevent `include_role` variable bleed.
- Renovate configuration for automated Ansible Galaxy collection updates.
- CI on standard GitHub-hosted runners with SHA-pinned actions and Dependabot.

[0.3.1]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.3.1
[0.3.0]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.3.0
[0.2.0]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.2.0
[0.1.0]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.1.0
