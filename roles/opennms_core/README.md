# opennms_core

Deploys and configures OpenNMS Horizon Core: server packages, webapp, database initialization, Kafka IPC, JVM tuning, JMX Prometheus exporter, and firewall rules (UFW on Debian and Ubuntu, firewalld on EL 10 when it is running).

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Package version pinning

On Debian and Ubuntu, this role writes an APT preferences file pinning the OpenNMS packages it installs.
EL 10 uses DNF versionlock instead; see [EL 10](#el-10).

**A routine `apt upgrade` will never move OpenNMS across a major release.** While the configured `opennms_version` is still carried by the repository, `apt upgrade` will not change the installed versions at all. That is deliberate: OpenNMS upgrades need a planned maintenance window.

Once the repository supersedes that exact version, `apt upgrade` may move OpenNMS to a newer patch *of the same major*. The repository serves one point release per dist, so this happens on the next OpenNMS point release — it is not a remote possibility. It is the deliberate cost of a pin that does not expire: a lone exact-version pin stops matching anything the moment its version is withdrawn, and a preferences file whose only entry has expired behaves exactly like no file at all, including permitting a jump to a different major.

The pin is therefore written in three tiers, most specific first:

| Tier | Matches | Priority | Effect |
|---|---|---|---|
| `version <opennms_version>-*` | the configured release, any Debian revision | 1001 | preferred; above 1000 so a deliberate downgrade is performed rather than ignored |
| `version <major>.*` | the same major | 900 | the fallback once the configured release is withdrawn |
| `release o=OpenNMS` | every other major | -1 | never selected automatically |

Tier 1 ends in `-*`, not a bare `*`: the pin is an fnmatch glob over the whole version string, so `36.0.1*` would also match `36.0.10` through `36.0.19` and — at priority 1001 — apt would apply that as a forced upgrade.

Order is load-bearing: APT applies the **first** matching entry, not the highest-priority one. `apt-cache policy <package>` reports the effective priority per available version and is the way to read the result.

The `-1` tier is not a lock. An explicit `apt-get install <package>=<version>` installs through it, which is why this role's own versioned install is unaffected.

To upgrade deliberately, change `opennms_version` and re-run the role. The pin is rewritten before the packages are installed, so the new version is permitted in the same run; there is no separate unpin step.

| Variable | Purpose |
|---|---|
| `opennms_core_pinned_packages` | The OpenNMS packages covered by the pin. Named for the role, so setting it for a host that runs several OpenNMS roles reaches this one only. Every entry must be a package whose versions track `opennms_version`: all three tiers key on it and the last gives every other version from the OpenNMS origin priority -1, so adding `jrrd2` or `iplike` leaves them with no installation candidate rather than a pin. |
| `opennms_pin_origin` | The repository's published `Origin` field, which the exclusion tier keys on. Not a hostname, so a mirror does not silently disable it. |

`rrdtool`, `jrrd2` and `iplike` are deliberately **not** pinned, though for different reasons. `rrdtool` is an ordinary Debian package and pinning it would block security updates to protect something that is not OpenNMS — the wrong trade. `jrrd2` and `iplike` are published only by `debian.opennms.org` and exist in no Debian suite, so there is no security stream to preserve for them; they are excluded because they are not OpenNMS itself. Whether they should be pinned anyway is an open question.

The APT source also targets an explicit per-major dist (`opennms-36`) rather than the floating `stable` alias, so a major-version jump cannot happen even if the pin is removed. See [`opennms_repositories`](../opennms_repositories/README.md).

### Unattended upgrades

`unattended-upgrades` is not a wrapper around `apt upgrade`.
It applies its own origin allowlist and its own package blacklist, and only part of its version selection consults APT policy.
Its behaviour against this pin was therefore measured rather than inferred, on Ubuntu 24.04 with `unattended-upgrades` 2.9.1 and Debian 13 with 2.12.

**A cross-major move never happens.** With the preferences file present, no OpenNMS package was selected for a major upgrade, including on a host whose origin allowlist had been deliberately widened to admit `o=OpenNMS`. `unattended-upgrades` defers to APT policy when it picks a version, so the other major sitting at `-1` is never chosen.

**On a stock host, the pin is not what protects you.** Both Ubuntu's and Debian's default allowlists admit only their own origins, so a default host never considers `o=OpenNMS` packages and the pin is never reached. That protection belongs to the distribution's configuration, not to this collection, and it ends the moment an operator adds an origin pattern of their own.

**Two within-major moves are prevented by default.** The preferences file cannot express *prefer exactly this version, and if it is gone, do nothing*: a `-1` on everything would say it, but it leaves the package with no installation candidate and breaks a deliberate install. So two of its tiers admit a version an unattended host will move to, and both were measured moving:

| Path | When it fires |
|---|---|
| tier 1 at 1001 | a new Debian revision of the configured version ships, because the tier matches `<version>-*`. The exact version you pinned moves and the service restarts, on a day nothing here changed |
| tier 2 at 900 | the configured version is withdrawn from the repository and a newer patch of the same major is available |

Each installing role therefore also writes `/etc/apt/apt.conf.d/51-opennms-<role>-blacklist`, adding its `opennms_core_pinned_packages` to `Unattended-Upgrade::Package-Blacklist`. That is a gate separate from candidate selection, so it stops both moves without touching what APT will install when asked directly.
Both file paths are fixed per role and are not settable from inventory. They were `defaults/` variables sharing one name across the three OpenNMS roles, so a single `group_vars` entry pointed all of them at one file and the last role to run decided its contents. Measured on a colocated host: one override, three roles, one file. They now derive from an `opennms_component` constant in each role's `vars/`, where an inventory cannot reach them, because a per-role path is the whole mechanism that keeps the roles from overwriting each other.

To add a package to this role's pin, set `opennms_core_pinned_packages` to the list you want, including the packages already there. Pick only packages whose versions track `opennms_version`; anything on its own version line, such as `jrrd2` or `iplike`, is caught by the negative tier and ends up with no installation candidate.


| Variable | Purpose |
|---|---|
| `opennms_unattended_upgrade_blacklist` | Whether to write the blacklist. Default `true`. Setting it `false` removes the file and re-exposes **both** moves above. |

Several OpenNMS roles on one host each write their own file, at the per-role default paths. APT accumulates list entries across `apt.conf.d` rather than letting the last definition win, so the effective blacklist is the union of their package lists.

If you previously followed this section's earlier advice and hand-wrote `/etc/apt/apt.conf.d/51-opennms-blacklist`, remove it. The roles do not manage that path, so it survives `opennms_unattended_upgrade_blacklist: false` and would keep blacklisting after you opted out.

**The cost.** An OpenNMS patch that is also a security fix will not land unattended. To take it, change `opennms_version` and re-run: the blacklist gates `unattended-upgrades` and not APT, so a deliberate `apt-get install <package>=<version>` and this role's own versioned install both go through it untouched.

Turning the blacklist off does not affect the cross-major protection. That is the preferences file's `-1` tier, and it was measured to govern `unattended-upgrades` on its own.

Not measured: `unattended-upgrades` releases other than the two named above. If you run something else, the property to check is whether its candidate selection defers to APT policy.

### EL 10

On EL 10 the role holds its packages with the DNF versionlock plugin.
It owns one marked block in `/etc/dnf/plugins/versionlock.list`, with one `<name>-0:<opennms_version>-*` entry per package in `opennms_core_rpm_pinned_packages`.
Other roles on the same host keep their own blocks.
The block is rewritten before the packages are installed, so changing `opennms_version` and re-running moves the packages in the same run.

A lock admits exactly the configured version.
There is no same-major fallback like the APT tier 2.
Once the repository drops the configured version, the installed packages stay where they are and a fresh install fails at the install task.

`dnf upgrade` and `dnf-automatic` both honour the lock, so EL 10 needs no unattended-upgrades blacklist.
`opennms_unattended_upgrade_blacklist` and `opennms_pin_origin` have no effect there.

The RPMs are split differently from the Debian packages.
`opennms-core` carries what Debian ships as `opennms-common` and `opennms-server`, so the role locks `opennms_core_rpm_pinned_packages` rather than `opennms_core_pinned_packages`.

When firewalld is running, the role opens the ports in `opennms_core_firewall_ports` in the default zone, permanently and in the running configuration.
It manages no other zone.
If the interface OpenNMS listens on sits in a different zone, open the ports there yourself.

`perl-XML-Twig` is not installed on EL 10, because only EPEL ships it.
`bin/provision.pl` and `bin/daemon-stats.pl` need it.
Install it from EPEL if you use those scripts.

## Host firewall

The role opens the ports in `opennms_core_firewall_ports` with UFW on Debian and Ubuntu when UFW is installed, and with firewalld on EL 10 when it is running.
The default is the HTTPS port `8443/tcp` when HTTPS is on, `10162/udp` (traps) and `9999/udp` (single-port flows).
The plaintext web port (`opennms_web_http_port`) is added only when `opennms_web_http_host` is not a loopback address.
On a loopback bind the role removes the old plaintext rule, so an upgraded host stops exposing 8980.
It keeps the rule when you list the port in `opennms_core_firewall_ports`.
With `opennms_web_https_enabled: false` it removes the HTTPS rule the same way.
When `opennms_core_jmx_exporter_port` is set, the default list opens it as TCP.
Setting the list replaces it entirely, the web ports included.
Apart from those two removals, rules are only added: removing an entry does not remove its rule.

## Variables

See [`defaults/main.yml`](defaults/main.yml) for the full list. The most relevant variables for tuning datasource and service behavior are documented below.

### Datasource configuration

Connection parameters are exported as environment variables in `/opt/opennms/etc/opennms.conf`. OpenNMS Horizon 36's pristine `opennms-datasources.xml` resolves these via the chain:

```
${scv:<key>:<field> | env:<VAR> | <literal default>}
       |                  |              |
       |                  |              `- baked into the pristine XML
       |                  `- exported by Ansible via opennms.conf
       `- populated by scvcli set (this role)
```

Credentials flow through the Secure Credential Vault (SCV) — populated by `scvcli set --from-stdin postgres ...` and `scvcli set --from-stdin postgres-admin ...` in `10-database-setup.yml`; the password travels on stdin, so values that start with `-` (which `scvcli` would otherwise parse as an option) are stored verbatim. `--from-stdin` needs Horizon 36.0.2 or later, and the role fails before installing anything when `opennms_version` is older. Host, port, and dbname flow through env vars in `opennms.conf`. SSL and connection-pool tunables are left to the pristine XML's literal defaults unless you explicitly set them.

| Legacy variable | Env var rendered |
|---|---|
| `opennms_datasource_db_host` | `POSTGRES_HOST` |
| `opennms_datasource_db_port` | `POSTGRES_PORT` |
| `opennms_datasource_db_name` | `OPENNMS_DBNAME` |

For everything else — SSL mode, connection-pool sizes, or any env var the pristine `opennms-datasources.xml` resolves via `${env:...}` — set `opennms_env`. Entries are **merged on top of** the role's built-in env defaults; keys you don't set keep their defaults:

```yaml
opennms_env:
  POSTGRES_HOST: db.example.com               # override host
  POSTGRES_SSL_MODE: require                  # tighten SSL
  OPENNMS_DATABASE_CONNECTION_MAXPOOL: 100    # raise the main pool ceiling
```

The pristine Horizon 36 `opennms-datasources.xml` defaults are: `POSTGRES_SSL_MODE=prefer`, `POSTGRES_SSL_FACTORY=org.postgresql.ssl.LibPQFactory`, `OPENNMS_DATABASE_CONNECTION_IDLETIMEOUT=600`, `LOGINTIMEOUT=3`, `MINPOOL=25`, `MAXPOOL=50`, `MAXSIZE=50`.

### JVM tunables and profiling

`opennms_jvm_conf` carries the entries `bin/opennms` reads as shell variables rather than environment variables — heap sizing, extra JVM options, and the Pyroscope launcher toggle. Entries are **merged on top of** the role's built-in defaults, exactly like `opennms_env`, so setting one key leaves the others alone:

```yaml
opennms_jvm_conf:
  JAVA_INITIAL_HEAP_SIZE: 2048
  JAVA_HEAP_SIZE: 4096
  PYROSCOPE_AGENT_ENABLED: 1   # profiling on; app name and server keep their defaults
```

The built-in defaults are the three profiling keys: `PYROSCOPE_AGENT_ENABLED: 0`, `PYROSCOPE_APPLICATION_NAME: Horizon-Core`, `PYROSCOPE_SERVER_ADDRESS: http://localhost:4040`. See [`pyroscope_agent`](../pyroscope_agent/README.md) for the agent itself.

**Only those three profiling keys belong here.** Entries in this dict are rendered *without* `export`, so they stay shell-local to `bin/opennms`, which then exports the application name and server address by name on its own. Any further agent setting — `PYROSCOPE_UPLOAD_INTERVAL`, `PYROSCOPE_AUTH_TOKEN`, `PYROSCOPE_HTTP_HEADERS` — has to go in `opennms_env` instead, or the agent never sees it. Do not restate the three above there: the template refuses to render a key defined in two of the three dicts.

### JMX Prometheus exporter

Off by default.
Set the port the exporter should listen on:

```yaml
opennms_core_jmx_exporter_port: 9299
```

The role installs the pinned [`prom_jmx_exporter`](../prom_jmx_exporter/README.md) jar and config in `/opt/opennms/agent`, appends its `-javaagent` option to `ADDITIONAL_MANAGER_OPTIONS` in `opennms.conf`, and restarts OpenNMS.
Metrics are then at `http://<core>:9299/metrics`.
Any `ADDITIONAL_MANAGER_OPTIONS` you set in `opennms_jvm_conf` are kept, and the exporter option follows them.
Setting the port back to `0` removes the option and restarts OpenNMS once.
The jar stays on disk, unloaded.
On a host that also runs Minion or Sentinel, give each component its own port.

Do not load the exporter through `opennms_jvm_conf` yourself.
A `-javaagent` option for `jmx_prometheus_javaagent` in `ADDITIONAL_MANAGER_OPTIONS` fails the run, and so do the removed `prom_jmx_exporter_owner`, `prom_jmx_exporter_group` and `prom_jmx_exporter_home`.

### Service toggles

Daemons can be enabled/disabled via `opennms_services`. Each key is a `CORE_SERVICE_<NAME>_ENABLED` env var consumed by the pristine `service-configuration.xml`:

```yaml
opennms_services:
  CORE_SERVICE_TELEMETRYD_ENABLED: false   # disable when Sentinel handles flows
  CORE_SERVICE_SYSLOGD_ENABLED: true       # enable syslog ingestion on Core
```

Empty by default; upstream defaults apply for every unmodified service. `Manager` and `Eventd` are not toggleable.

### Web UI and TLS

The role serves the web UI over HTTPS on port 8443 and binds plaintext HTTP on port 8980 to `127.0.0.1`.
Only a local reverse proxy or the role's own readiness check reaches the plaintext port.
Without a certificate of your own, the role generates a self-signed one.
Browsers warn about it until you trust it or supply your own.

| Variable | Default | Purpose |
|---|---|---|
| `opennms_web_https_enabled` | `true` | Serve HTTPS. `false` leaves only the plaintext listener. |
| `opennms_web_https_host` | `0.0.0.0` | HTTPS bind address. |
| `opennms_web_https_port` | `8443` | HTTPS port. |
| `opennms_web_http_host` | `127.0.0.1` | Plaintext bind address. A non-loopback address makes it reachable from the network. |
| `opennms_web_http_port` | `8980` | Plaintext port. |
| `opennms_web_base_url` | `https://%x%c/` | `opennms.web.base-url`. `http://%x%c/` when HTTPS is off. |
| `opennms_tls_dir` | `{{ opennms_home }}/etc/tls` | Directory for the generated files. |
| `opennms_tls_cert_path` | empty | PEM certificate on the target host. Setting it switches to your own certificate. |
| `opennms_tls_key_path` | empty | PEM private key on the target host. Required with the certificate. |
| `opennms_tls_chain_path` | empty | Optional PEM chain added to the keystore. |
| `opennms_tls_keystore_password` | empty | Empty generates a random password on the first run and keeps it in `keystore.pass`. |
| `opennms_tls_selfsigned_common_name` | `ansible_fqdn` | Subject common name. |
| `opennms_tls_selfsigned_subject_alt_names` | empty | Replaces the default list when set. The default is the FQDN, the short hostname, the default IPv4 address, `localhost` and `127.0.0.1`. Entries read `DNS:name` or `IP:address`. |
| `opennms_tls_selfsigned_key_type` | `ECC` | `ECC` (P-256) or `RSA`. |
| `opennms_tls_selfsigned_days` | `825` | Validity in days. |
| `opennms_tls_selfsigned_renew_days` | `30` | The role regenerates the certificate when fewer days remain. |
| `opennms_tls_selfsigned_organization`, `_organizational_unit`, `_country` | empty | Optional subject fields. |

The generated files live in `opennms_tls_dir`, which is `0700` and owned by `opennms`.
They are `jetty-selfsigned.key`, `jetty-selfsigned.crt`, `jetty.p12` and `keystore.pass`.
The role keeps the self-signed certificate between runs.
It regenerates it when a self-signed setting changes or when fewer than `opennms_tls_selfsigned_renew_days` days remain.
Renewal happens only when the role runs.
There is no timer.

The role renders `etc/jetty.xml` from `{{ opennms_home }}/etc/examples/jetty.xml` with the HTTPS block uncommented.
The file carries the text "HTTPS enabled by indigo423.opennms.opennms_core".
A change to the keystore or to `jetty.xml` restarts OpenNMS, because Jetty does not reload keystores.
The role sets no HSTS header.

#### Your own certificate

Put the PEM files on the target host and point the role at them.

```yaml
opennms_tls_cert_path: /etc/ssl/opennms/fullchain.pem
opennms_tls_key_path: /etc/ssl/opennms/privkey.pem
# opennms_tls_chain_path: /etc/ssl/opennms/chain.pem
```

The role only reads these files and never writes to them.
It builds `jetty.p12` from them and fails when the key does not match the certificate.

#### Let's Encrypt

The role does not request or renew certificates.
There are two routes.

- Run a reverse proxy such as Caddy or nginx with certbot in front of `127.0.0.1:8980`, and set `opennms_web_https_enabled: false`.
  Set `opennms_web_base_url` to the public URL the proxy serves.
- Let certbot or acme.sh write PEM files to the paths above, and add a deploy hook that reruns this role.
  The rerun rebuilds the keystore and restarts OpenNMS.

#### Grafana

The sample `onms_hzn_base_url: http://localhost:8980` keeps working when Grafana runs on the same host, because the plaintext port stays on loopback.
A Grafana on another host uses `https://<core>:8443`.
It must trust the certificate or skip verification, because the role does not distribute a self-signed certificate.

#### Limits

- IPv6 literals other than `::` and `::1` are not supported as bind addresses, because the readiness waits probe the configured address.
- The role handles HTTPS for the Core web UI only, not Minion, Sentinel or the Karaf shell.

### Startup readiness

The web ports are `opennms_web_http_port` and, when HTTPS is on, `opennms_web_https_port`.
After starting `opennms.service`, the role first polls `/opennms/login.jsp` on the plaintext and HTTPS listeners until each returns 200, then runs `bin/opennms -v status` until it exits 0.
The second gate matters because Jetty answers before Manager has started every service.
The status command signals the JVM, which writes one line per enabled service to `logs/status-check.txt`, and exits 0 only when every line reads `running`.
It is retried only while it reports a partially started Core (exit 160).
A stopped JVM, a stale pid file or no answer to the signal within 30 seconds fails the role at once.
Each status poll can take up to 31 seconds on top of the delay, so the second gate's worst case is longer than the first's.

| Variable | Purpose |
|---|---|
| `opennms_startup_retries` | Polls before failing, per gate. Default `30`. |
| `opennms_startup_delay` | Seconds between polls. Default `10`. |
| `skip_startup` | Leave Core stopped and skip both gates. Default `false`. |

### Prometheus remote_write plugin

`opennms_remotewrite` switches on the [`opennms-prometheus-remotewrite-plugin`](https://github.com/OpenNMS-Plugins/opennms-prometheus-remotewrite-plugin) and renders its PID file, `etc/org.opennms.plugins.tss.prometheus.cfg`. Setting the dict **replaces** the role default, so restate `write_url` and `read_url` when you override it.

```yaml
opennms_remotewrite:
  enabled: true
  write_url: http://mimir.example.com:8080/api/v1/push
  read_url: http://mimir.example.com:8080/prometheus/api/v1
  organization_id: ""
  batching_enabled: true      # store() no longer waits on HTTP; keeps per-series order
```

From plugin 2.2.0, writes are synchronous by default: a writer thread waits up to `callTimeoutInMs` for the backend. The keys below tune that write path and need plugin 2.2.0 or later; an older plugin ignores them. Each one is optional and renders only when set; an unset or empty key takes the plugin default. See the [plugin README](https://github.com/OpenNMS-Plugins/opennms-prometheus-remotewrite-plugin/blob/v2.2.0/README.md) for what each property does.

| Key | Plugin property |
|---|---|
| `async_writes` | `asyncWrites` |
| `call_timeout_ms` | `callTimeoutInMs` |
| `batching_enabled` | `batchingEnabled` |
| `batch_shards` | `batchShards` |
| `batch_max_samples` | `batchMaxSamples` |
| `batch_linger_ms` | `batchLingerMs` |
| `batch_shard_capacity` | `batchShardCapacity` |
| `batch_max_retries` | `batchMaxRetries` |
| `batch_retry_backoff_ms` | `batchRetryBackoffMs` |
| `batch_enqueue_timeout_ms` | `batchEnqueueTimeoutMs` |
| `external_tags_enabled` | `externalTagsEnabled` |
| `external_tags_cache_size` | `externalTagsCacheSize` |
| `external_tags_queue_size` | `externalTagsQueueSize` |
| `external_tags_threads` | `externalTagsThreads` |
| `external_tags_preload` | `externalTagsPreload` |

`async_writes: true` also stops blocking the writer threads, but unbatched asynchronous writes reach the backend out of order. Mimir rejects out-of-order samples unless its out-of-order window is set, so prefer `batching_enabled` there.

The role fails the run on a key that is in neither table, so a misspelling cannot silently leave the plugin on its default.

## Example

```yaml
- hosts: opennms_core
  roles:
    - indigo423.opennms.opennms_core
```

## Migration from earlier role versions

### Web UI on HTTPS

Earlier versions served plaintext on 0.0.0.0:8980.
The current version serves HTTPS on 8443 and binds plaintext to 127.0.0.1.
Clients that used `http://<core>:8980` must switch to `https://<core>:8443`, and a firewall rule or load balancer that pointed at 8980 needs the new port.
To restore the old behaviour, set `opennms_web_http_host: 0.0.0.0` and, if you do not want HTTPS, `opennms_web_https_enabled: false`.
The role also needs the `community.crypto` collection.
Run `make deps` or `ansible-galaxy collection install -r requirements.yml`.

Two guards stop the run before anything is installed.

- `opennms_properties_webapp` holds a key the role now renders from variables.
  The guarded keys are `opennms.web.base-url`, `org.opennms.netmgt.jetty.host`, `org.opennms.netmgt.jetty.port` and every `org.opennms.netmgt.jetty.https-*` key.
  The failure message names the variable to use instead.
  Move each value to `opennms_web_base_url`, `opennms_web_http_host`, `opennms_web_http_port`, `opennms_web_https_host`, `opennms_web_https_port`, `opennms_web_https_enabled` or `opennms_tls_*`, and delete the key.
  The dict now defaults to `{}` and takes the remaining Jetty keys such as `org.opennms.netmgt.jetty.ajp-port`, so you no longer copy the whole default dict.
- `{{ opennms_home }}/etc/jetty.xml` has changes the role did not make, and the role would replace it to enable HTTPS.
  A file identical to `etc/examples/jetty.xml`, or one that carries the marker text, is taken over.
  To let the role replace your file, delete it or add "HTTPS enabled by indigo423.opennms.opennms_core" to it.
  The role then renders its own `etc/examples/jetty.xml` over it.
  To keep your file, set `opennms_web_https_enabled: false`.
  Add `opennms_web_http_host: 0.0.0.0` to expose plaintext 8980.

### JMX Prometheus exporter

Earlier versions always installed the exporter in `/opt/prom-jmx-exporter`, and you loaded it with `-javaagent` in `opennms_jvm_conf.ADDITIONAL_MANAGER_OPTIONS`.
Remove that option and set `opennms_core_jmx_exporter_port` to the port you used, usually 9299.
The old `/opt/prom-jmx-exporter` directory is no longer read and can be deleted.

### Datasources

Earlier versions of this role rendered `/opt/opennms/etc/opennms-datasources.xml` from a Jinja template. The current version instead trusts the pristine XML shipped by the `opennms-server` deb package and drives runtime values through env vars and SCV.

On the first run after upgrading:

- If the on-disk `opennms-datasources.xml` contains the marker comment `This is an Ansible managed template` (left by the previous version), the role copies the pristine file from `/usr/share/opennms/etc-pristine/opennms-datasources.xml` over it and triggers a restart.
- If the file does not contain that marker, the role treats it as user-customized and leaves it untouched. A debug message notes the divergence; overrides via `opennms.conf` env vars still apply where the file uses `${env:...}` placeholders.

If the role's signature-match incorrectly classifies a customized file (e.g., you intentionally kept the original template's header comment), the migration is non-destructive: `ansible.builtin.copy` runs with `backup: true`, leaving the pre-overwrite content at `/opt/opennms/etc/opennms-datasources.xml.NNNNN.YYYY-MM-DD@HH:MM:SS~`. Restore from there if needed.

To force a manual migration of a user-customized file, first run `apt-get install --reinstall opennms-server` (which restores the pristine copy), then re-run the role.

## Credentials

This role refuses to run while `opennms_datasource_db_password` or `postgres_password` is the sentinel default `__SET_VIA_VAULT__` (`tasks/00-credentials-check.yml`). Bootstrap real credentials once with:

```bash
ansible-playbook -i <your inventory> indigo423.opennms.init_secrets
```

See the [collection README](../../README.md#-first-time-setup-bootstrap-database-credentials) for the full vault workflow, including master-key responsibility, rotation (`force_rotate=true`), and recovery (`force_reinit=true`).

## License

GPL-3.0-or-later
