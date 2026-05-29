# Changelog

All notable changes to the `indigo423.opennms` collection are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Each entry below is a short index; the corresponding GitHub release contains the full notes including the Component Versions table and upgrade instructions.

## [0.4.5] - 2026-05-29

### Fixed
- `opennms_core`: keep the `opennms.conf` header on its own line. The leading `{%-` on the first `set` ate the newline after the `######` header, gluing it onto the first `opennms_jvm_conf` key — so `JAVA_HEAP_SIZE` rendered as `######JAVA_HEAP_SIZE="..."` and was silently commented out. With only `JAVA_INITIAL_HEAP_SIZE` (`-Xms`) active and no `-Xmx`, the JVM aborted at startup with `Initial heap size set to a larger value than the maximum heap size` on any host whose default max heap was below the configured initial heap. Dropped the `-` so the header keeps its trailing newline.

## [0.4.4] - 2026-05-29

### Fixed
- `opennms_core`: export the env-var and service entries in `opennms.conf` so they reach the JVM. `bin/install` (`. opennms.conf`) and `bin/opennms` (`__onms_read_conf`) both source the file without auto-export, so the unexported `POSTGRES_HOST`/`POSTGRES_PORT`/`OPENNMS_DBNAME` (and `CORE_SERVICE_*_ENABLED`) entries stayed shell-local and never reached the JVM. The `${env:...}` placeholders in the pristine `opennms-datasources.xml` then fell back to their literals — every deployment with a non-`localhost` database failed at `install -dis` and at runtime with `Connection to localhost:5432 refused`. JVM tunables (`JAVA_HEAP_SIZE`, `ADDITIONAL_MANAGER_OPTIONS`) remain unexported as they are read as shell variables.

## [0.4.3] - 2026-05-29

### Fixed
- `opennms_icmp`: stop defaulting `jicmp_version`/`jicmp6_version` to the stale `3.*` major. On a host that already carries the newer libraries a later Horizon release pulls in (e.g. `4.0.0-1` under Horizon 36), `apt` treated `3.*` as a downgrade and aborted with `E: Packages were downgraded and -y was used without --allow-downgrades`. The defaults now use `*`, which resolves to the configured repo's candidate and stays idempotent. Consumers needing a frozen build can still override these.

## [0.4.2] - 2026-05-28

### Fixed
- `grafana_provisioning`: install `opennms-opennms-app` via `grafana-cli` before dropping the provisioning file that enables it. Previously the role copied a provisioning entry referencing the plugin but never installed it, so `grafana-server` failed to start with `Failed to provision plugins: plugin not installed: "opennms-opennms-app"` whenever the role ran against a fresh host. README and `meta/main.yml` updated to reflect the role's expanded scope.

## [0.4.1] - 2026-05-28

### Fixed
- `opennms_core`: replace `scvcli show` with `scvcli get` in the post-credential verification step. `scvcli` has no `show` subcommand; the supported verbs are `set`, `get`, `get-all`, `list`, `delete`. Every deployment failed immediately after `init_secrets` populated the SCV vault with `Error: "show" is not a valid value for "ACTION"`. `get ALIAS` has the same signature and returns the stored entry, satisfying the existing `failed_when` guard (#93).

## [0.4.0] - 2026-05-28

### Added
- `opennms_core`: drive datasource configuration via env vars in `opennms.conf` instead of mirroring `opennms-datasources.xml`. Signature-based migration restores the deb-shipped pristine XML for hosts whose file still carries the old "Ansible managed template" marker, and leaves user-customized XML untouched. New `opennms_datasource_ssl_mode` (`prefer`) and `opennms_datasource_ssl_factory` (`org.postgresql.ssl.LibPQFactory`) variables match the pristine XML defaults (#90).
- `playbooks/init_secrets.yml`: bootstrap playbook for initial SCV/datasource credentials, including a non-comment placeholder regex (`changeme`, `password123`, etc.) to catch accidentally-committed defaults. Documents `-i` inventory expectations and the `secrets_dest_dir` override for multi-inventory setups (#90).
- Pre-flight `00-credentials-check.yml` tasks for `opennms_core`, `opennms_sentinel`, and `stub_pgsql` — fail-fast SCV credential validation before any service-impacting step runs (#90).
- Role argument validation via `meta/argument_specs.yml` for `opennms_core`, `opennms_sentinel`, and `stub_pgsql` (#90).
- README: "Install from Ansible Galaxy" section covering `ansible-galaxy collection install`, a pinned `requirements.yml` example, and FQCN role references (`indigo423.opennms.<role>`) (#89).

### Changed
- Inventory restructure: `group_vars/grafana/vars.yml` and `group_vars/opennms_stack/vars.yml` moved under `inventory/group_vars/` to match Ansible's expected layout (#90).
- `opennms_core`: render `opennms.conf` from a new `05-opennms-conf.yml` so env vars land on disk before `scvcli set` and `install -dis` run. `opennms.conf.j2` now emits `opennms_env` and `opennms_services` (`CORE_SERVICE_*_ENABLED` toggles) with shell-safe double-quoting and lowercase booleans; fails fast on duplicate keys across the three dicts (#90).
- CI lint workflow expanded (`.github/workflows/ansible-opennms-lint.yml`, +30 lines) (#90).

### Removed
- `opennms_core`: dropped eight inert variables — `opennms_datasource_opennms_admin_*` and `opennms_datasource_opennms_monitor_*`. They were only consumed by the deleted `opennms-datasources.xml.j2`; the pristine Horizon XML hard-codes these pool values without env-var placeholders, so the vars never reached the running config (#90).
- `opennms_core`: deleted `templates/etc/opennms-datasources.xml.j2`. Hosts that had the old template applied are migrated to the pristine deb XML automatically; see Breaking Changes for the customization path (#90).

### Breaking Changes
- New credential pre-flight: the `00-credentials-check.yml` tasks will halt the run if required SCV credentials are missing. Existing inventories must define them before re-running, or use the new `playbooks/init_secrets.yml` to bootstrap.
- Inventory path move: any local override referencing `group_vars/{grafana,opennms_stack}/vars.yml` at the repo root must be updated to `inventory/group_vars/...`.
- Removed variables: if your inventory set `opennms_datasource_opennms_admin_*` or `opennms_datasource_opennms_monitor_*`, those keys are now unknown to `argument_specs.yml` and will fail validation. Delete them — they were never wired up to a runtime config.

## [0.3.2] - 2026-05-25

### Added
- Per-role `meta/main.yml` (galaxy_info: author, GPL-3.0-or-later license, min_ansible_version `2.15`, Debian bookworm/trixie + Ubuntu jammy/noble platforms, galaxy_tags) and `README.md` for all 12 roles (#87). This is the minimum metadata Galaxy's importer requires; v0.3.1 was rejected on upload because it was missing.

### Notes
- First release that actually lands on https://galaxy.ansible.com/ as `indigo423.opennms`. v0.3.1 stays in the GitHub release history as a record of the failed Galaxy publish.

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

[0.4.0]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.4.0
[0.3.2]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.3.2
[0.3.1]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.3.1
[0.3.0]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.3.0
[0.2.0]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.2.0
[0.1.0]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.1.0
