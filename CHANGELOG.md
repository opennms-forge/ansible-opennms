# Changelog

All notable changes to the `indigo423.opennms` collection are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Each entry below is a short index; the corresponding GitHub release contains the full notes including the Component Versions table and upgrade instructions.

## [0.9.0] - 2026-08-25

Repository keys, download URLs and now host clocks are verified before a
deployment proceeds. Two changes alter what an unchanged playbook does on an
unchanged host — `apt upgrade` no longer moves OpenNMS packages, and a host with
an unsynchronised clock now fails the run. Both are deliberate and both have an
escape hatch; see **Changed**.

### Added
- New `timesync` role, included by `opennms_core`, `opennms_minion` and `opennms_sentinel`: verifies the host clock is synchronised before a component is deployed. **A deployment against a host whose clock is not synchronised now fails where it previously proceeded** — set `timesync_required: false` to override. The check asserts `NTPSynchronized` rather than requiring an NTP client, so a VM synchronised by its hypervisor (`NTP=no`, `NTPSynchronized=yes`) passes correctly. Optional chrony installation via `timesync_install_chrony`, off by default so the role never displaces working synchronisation (#31).
- `opennms_minion`: per-module Kafka configuration via `opennms_minion_kafka_sink`, `_rpc` and `_twin`, each rendering its own Karaf PID file, so sink, rpc and twin can target different brokers. Empty by default — a deployment that does not opt in renders exactly as before. Each module dictionary must define `bootstrap.servers`: OpenNMS selects a whole config file rather than merging keys, so a module file without it is ignored entirely and the module silently falls back to the common configuration. The role fails rather than rendering one (#49).

### Changed
- **`apt upgrade` no longer moves OpenNMS packages.** `opennms_core`, `opennms_minion` and `opennms_sentinel` write an APT preferences file pinning the OpenNMS packages to `opennms_version`. To upgrade deliberately, change `opennms_version` and re-run — the pin is rewritten before installation, so the new version is permitted in the same run. `rrdtool`, `jrrd2` and `iplike` are not pinned and still receive security updates (#38).
- `opennms_repositories`: the APT source targets an explicit per-major dist (`opennms-36`) instead of the floating `stable` alias, derived from `opennms_version`. `stable` resolves to `opennms-36` today but has moved before, so a plain `apt upgrade` could have offered a major version jump once it follows `opennms-37`. Also silences apt's `Conflicting distribution` warning (#38).

### Fixed
- `opennms_core`: installing or reconfiguring the JMX Prometheus exporter now restarts OpenNMS. The agent is loaded at JVM start, so a new jar or changed config previously took effect only when someone restarted by hand. The commented `ADDITIONAL_MANAGER_OPTIONS` example that wires the agent in is also corrected — it used shell assignment syntax inside a YAML mapping, paths this role never writes to, and a version six releases stale, so copying it produced a JVM that failed to start (#57).

### Documentation
- Added `CONTRIBUTING.md` (DCO sign-off and the `Assisted-by` AI-assistance policy), `SECURITY.md` (private vulnerability reporting and scope), issue forms and a pull request template, and a License section in the README (#149).

## [0.8.0] - 2026-08-24

Repository signing keys are verified by fingerprint, and composed download URLs
are checked in CI. Two independent defects made v0.7.0 impossible to install on
a fresh host: the OpenNMS key pin no longer matched the bytes upstream serves,
and the JMX exporter URL was composed with a `v` prefix that upstream does not
use. Both are fixed, and the class of defect is closed off rather than patched
case by case.

### Security
- `opennms_repositories`, `stub_pgsql`, `stub_elasticsearch`: verify the repository signing key by **fingerprint** rather than by the key file's SHA-256. A fingerprint is the key's identity, so it survives re-exports and host migrations that change the file's bytes without changing the key; a file hash breaks on those and never establishes which key was trusted. Verification runs between the dearmor and the install, so a rejected key never reaches `/usr/share/keyrings/` (#141, #146).
- `stub_elasticsearch`: previously installed its key with `apt_key` straight from a URL, with no verification at all. This was the collection's last `apt_key` call, a module scheduled for removal in `ansible.builtin` 2.25 (#146).

### Added
- `*_key_fingerprints` in all three repository roles — a list, so a key rotation is an append rather than a swap. Pinned values are documented in each role's README with the evidence corroborating them (#141, #146).
- `make check-urls` and a `download-urls` CI workflow that render every `*_url` variable in role defaults and verify each resolves. `ansible-lint` validates YAML shape and cannot see a 404, which is how all of these shipped green. Runs on push, PR and weekly, since upstream can break the collection with no commit here (#145).
- `es_drift_plugin_url` in `stub_elasticsearch`, moved out of an inline task so the URL check covers it (#145).

### Fixed
- `opennms_core`: the JMX exporter URL added a `v` prefix for versions `>= 1.6.0`, but upstream tags every 1.x release bare, so the default 404'd and every fresh Core deploy failed. Upstream carries a stray `v1.6.0` git tag with no release attached, which is what the conditional was written from (#135, #143).
- `stub_victoriametrics`: Renovate wrote a `v`-prefixed tag into a variable the URL template already prefixed, composing `download/vv1.150.0/…`. The role had been uninstallable since 2026-08-14 (#143).
- `opennms_core`: `opennms_remotewrite_version` gained `extractVersion`, so the next Renovate bump cannot break its URL the same way (#143).
- All three repository roles: the private key working directory is now removed even when verification fails, instead of accumulating on every failed run (#147).

### Changed
- **`victoriametrics_version` now holds a bare version** (`1.150.0`, not `v1.150.0`); the URL template supplies the prefix. A `v`-prefixed override still resolves identically, because the value is normalised where it is consumed (#143).
- `opennms_key_sha256` and `pgsql_key_sha256` default to `null` and are omitted rather than shipping a pinned hash. The fingerprint check is the authoritative control; a shipped hash pin breaks on harmless re-exports. Existing overrides continue to work (#141).
- Upstream: OpenNMS Horizon 36.0.3, VictoriaMetrics 1.150.0, `community.general` 13.3.0.

## [0.7.0] - 2026-07-28

Multi-node support for the stub infrastructure roles and Sentinel. Every role
derives its cluster shape from inventory group membership, so scaling a
deployment is the only change required, and a single-member group renders
exactly as before — `baseline`, `es-nostore`, `vm-cluster-es`, `mimir-single`
and `vm-single` are unaffected.

### Added
- `stub_elasticsearch`: derive discovery from `es_cluster_group` — `discovery.type: single-node` for one member, `discovery.seed_hosts` and `cluster.initial_master_nodes` for two or more. The two forms are mutually exclusive in Elasticsearch, so clustering strips `discovery.type` from whatever `es_configuration` resolves to rather than assuming it is absent (#130).
- `stub_kafka`: form a KRaft cluster from `kafka_cluster_group` — positional `node.id`, full `controller.quorum.voters`, per-broker `advertised.listeners`, and replication scaled to the member count capped at 3. The cluster ID is established once for the cluster and reused from disk on re-runs; previously each host generated its own, so brokers would have formed separate clusters and refused to join with `INCONSISTENT_CLUSTER_ID`. Derived values apply only at two or more members, leaving deliberate single-broker configuration untouched (#131).
- `opennms_sentinel`: default `bootstrap.servers` from `sentinel_kafka_group` instead of `localhost:9092`, which is never correct when Sentinel and Kafka are separate nodes. Controller ids already derive per host, and the shared `group.id` is what makes several Sentinels split the flow workload rather than each processing every record (#132).
- `stub_mimir`: distributed mode — memberlist rings across the member group, replication scaled to the member count, and generic S3 blocks/ruler/alertmanager storage via `mimir_s3_endpoint`, which works against AWS S3, MinIO, RustFS or anything else that speaks S3. Clustered with no endpoint is asserted rather than left to surface as unexplained query gaps, because the filesystem backend is per-node and cannot be shared (#133).

### Fixed
- `stub_elasticsearch`: grant `LimitMEMLOCK` via a systemd drop-in when `bootstrap.memory_lock` is set. Single-node Elasticsearch skips bootstrap checks, so the setting had been inert; a cluster enforces them and refused to start (#130).
- `stub_mimir`: give clustered components an explicit `instance_addr`, and the query-frontend an `address`. Mimir resolves its own address by probing interfaces `[eth0, en0]`, which modern predictable names do not match (#133).
- `galaxy.yml`: exclude gitignored working directories from `build_ignore`, so they no longer reach the published artifact (#123).

### Changed
- CI runs `ansible-lint` on pull requests, with pushes scoped to `main` (#124).

## [0.6.0] - 2026-07-25

### Added
- `opennms_core`: persist metrics to any Prometheus remote_write backend (Mimir, VictoriaMetrics, Cortex, Thanos) via the `opennms-prometheus-remotewrite-plugin`. New `22-timeseries-plugin.yml` downloads the plugin KAR, boots the Karaf feature, and templates the `org.opennms.plugins.tss.prometheus` PID; the time-series strategy is switched to `integration` through the existing `opennms_properties_timeseries` mechanism. Opt-in via `opennms_remotewrite.enabled` (default `false`), with `write_url`/`read_url`/`organization_id` and a Renovate-managed `opennms_remotewrite_version` (`2.1.0`) (#118).
- `stub_victoriametrics`: new stub role deploying single-node VictoriaMetrics (`1.148.0`) as a remote_write backend, with a systemd unit, configurable `victoriametrics_http_port` (8428), `victoriametrics_data_path`, and `victoriametrics_retention` (#119).

### Fixed
- `stub_mimir`: ship a working single-node monolithic config. The role installed the Mimir `.deb` and left its empty default config in place, so Mimir started with `replication_factor: 3` against a single ingester and answered every request with `too many unhealthy instances in the ring` / HTTP 503 — never a usable backend. Now templates `/etc/mimir/config.yml` (the path the deb's unit reads) with in-memory rings, `replication_factor: 1`, and per-component filesystem storage in distinct directories. New `mimir_http_port`/`mimir_data_dir` defaults and a `Restart mimir` handler (#120).
- `opennms_core`, `stub_victoriametrics`: make version bumps actually take effect. The plugin KAR was downloaded to a version-independent filename, so `get_url` skipped the download once the file existed and raising `opennms_remotewrite_version` was a silent no-op; the KAR filename is now versioned and superseded KARs are removed. `stub_victoriametrics` had the same trap in its `creates:` guard — the tarball now unpacks into a version-scoped directory with a symlink into `PATH`, so a bump re-extracts (#121).
- `stub_mimir`: raise the per-tenant limits (`ingestion_rate`, series caps) for the `anonymous` tenant. Mimir's defaults returned HTTP 429 and dropped samples under a 10k-node load, skewing cross-engine comparisons against VictoriaMetrics (#121).
- `stub_mimir`, `stub_victoriametrics`: tag the `Restart mimir` and `Restart victoriametrics` handlers so `--tags`-filtered runs still restart the service after a config change (#121).
- `opennms_core`: tighten the remote_write plugin's cfg/boot/KAR files to `0640` to match sibling managed files, correct a stale header comment, and order the `21-kafka`/`22-timeseries-plugin` includes to match their numeric task-file prefixes (#121).

## [0.5.0] - 2026-07-25

### Added
- `opennms_core`: wait for Core to answer on `http://localhost:8980/opennms/login.jsp` after the systemd unit starts, instead of returning as soon as systemd accepts the start. Core needs minutes to serve and can exit mid-startup, so the play previously reported success on a Core that was already going down. Tunable via `opennms_startup_retries` (30) and `opennms_startup_delay` (10s, ≈5 min total); skipped when `skip_startup` is set (#112).

### Fixed
- `opennms_core`: fail the play when `bin/install -dis` fails. The task ran with `changed_when: rc != 0` and no `failed_when`, so a successful schema migration reported *ok/unchanged* and a **failed** one never failed the play — the role went on to start OpenNMS against a half-migrated database, surfacing later as a 5-minute Liquibase-lock hang and `System.exit(1)` with nothing pointing at the real cause (#111).
- `opennms_core`: clear a stale Liquibase changelog lock before startup. An interrupted `install -dis` or Core start can leave `databasechangeloglock` held, making the next start wait out Liquibase's 5-minute default and then `System.exit(1)` — the deploy hung until someone cleared the lock by hand. The role now resets a stale lock after schema init, guarded by a `DO` block so it is a no-op when the table is absent and idempotent otherwise. Adds `python3-psycopg2` to the Core host for the query (#113).

## [0.4.7] - 2026-07-17

### Changed
- Bump OpenNMS Horizon to `36.0.2` and Prometheus JMX Exporter to `1.6.0`; both are now Renovate-managed so future bumps arrive automatically (#107, #108).
- `stub_kafka`: download Kafka from `archive.apache.org` instead of `dlcdn.apache.org`. The CDN drops superseded releases, so any pinned `kafka_version` starts 404ing as soon as upstream moves on — `4.2.0` was already gone (#109).

### Fixed
- `opennms_repositories`: install `gnupg`. Minimal cloud images ship without it, and every repository-key task needs it; standard server images masked the gap. Installed here rather than in `common` so the targeted `hzn-*-deployment.yml` playbooks and standalone Galaxy consumers are covered too (#109).
- `opennms_core`: run `scvcli` through `bash`. The packaged script reads `java.conf` with the bash-only `$(<file)` expansion under a `#!/bin/sh` shebang, which yields an empty Java path on Debian/Ubuntu where `sh` is dash — breaking vault init with `-jar: not found` (#109).

## [0.4.6] - 2026-05-29

### Fixed
- `opennms_minion`: pin `JAVA_HOME` in `/etc/default/minion`. Unlike `opennms_core` (which runs `runjava -s`), the Minion role never told the service where Java is, so it fell back to karaf's `bin/find-java.sh`, whose max-version cap rejects current JDKs (e.g. 21) and aborted startup with `JAVA_HOME is not valid: No match found!` — `minion.service` failed to start. The role now resolves the installed JDK (`readlink -f /usr/bin/java`) and writes `JAVA_HOME` into the unit's EnvironmentFile, bypassing the broken auto-detection.

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

[0.9.0]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.9.0
[0.8.0]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.8.0
[0.7.0]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.7.0
[0.6.0]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.6.0
[0.5.0]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.5.0
[0.4.7]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.4.7
[0.4.6]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.4.6
[0.4.5]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.4.5
[0.4.4]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.4.4
[0.4.3]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.4.3
[0.4.2]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.4.2
[0.4.1]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.4.1
[0.4.0]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.4.0
[0.3.2]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.3.2
[0.3.1]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.3.1
[0.3.0]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.3.0
[0.2.0]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.2.0
[0.1.0]: https://github.com/opennms-forge/ansible-opennms/releases/tag/v0.1.0
