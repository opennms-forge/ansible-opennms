# prom_jmx_exporter

Installs a pinned [Prometheus JMX exporter](https://github.com/prometheus/jmx_exporter) Java agent and its config for an OpenNMS Horizon component to load.

Included by `opennms_core`, `opennms_minion` and `opennms_sentinel` when their `opennms_<component>_jmx_exporter_port` is set.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## What it does, and what it does not

It downloads the jar, verifies its checksum, renders the config, and puts both where the caller says.

It does **no** JVM wiring and knows nothing about services. Core loads the agent through `ADDITIONAL_MANAGER_OPTIONS` in `opennms.conf`. Minion and Sentinel load it through `EXTRA_JAVA_OPTS` in their sysconfig file. That knowledge stays in the component roles.

## Variables

| Variable | Default | Purpose |
|---|---|---|
| `prom_jmx_exporter_version` | `1.7.0` | Release to install. |
| `prom_jmx_exporter_url` | GitHub release asset | Download URL for the jar. |
| `prom_jmx_exporter_sha256` | digest of 1.7.0 | Checksum, in `get_url`'s `sha256:<digest>` form. |
| `prom_jmx_exporter_config` | OpenNMS bean list | Settings rendered into the exporter config. |
| `prom_jmx_exporter_jar` | *(none)* | Absolute destination of the jar. Asserted, not defaulted. |
| `prom_jmx_exporter_config_file` | *(none)* | Absolute destination of the config. Asserted, not defaulted. |
| `prom_jmx_exporter_notify` | `[]` | Handlers to fire when the jar or config changes. |

One config serves all three components. A bean pattern that matches nothing on a component exports nothing there.

Both files are installed `root:root 0644`. Neither is a secret, and each component's JVM runs as its own user. The destination directories are created `root:root 0755` only when missing, because Core's package owns `$OPENNMS_HOME/agent`.

A version bump needs a new `prom_jmx_exporter_sha256`. Upstream publishes a `jmx_prometheus_javaagent-<version>.jar.sha256` asset, and `renovate.json` notes it in the bump PR.

## Example

```yaml
- name: Install the JMX Prometheus exporter
  ansible.builtin.include_role:
    name: prom_jmx_exporter
  vars:
    prom_jmx_exporter_jar: /opt/minion/agent/jmx_prometheus_javaagent.jar
    prom_jmx_exporter_config_file: /opt/minion/agent/jmx-prometheus-exporter.yaml
    prom_jmx_exporter_notify:
      - Restart minion
```

Usually you do not need to declare it: the component roles include it themselves.

## License

GPL-3.0-or-later
