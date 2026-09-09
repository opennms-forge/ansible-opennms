# pyroscope_agent

Installs a pinned [Grafana Pyroscope Java agent](https://github.com/grafana/pyroscope-java) jar for an OpenNMS Horizon component to load.

Included by `opennms_core`, `opennms_minion` and `opennms_sentinel`.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Why this exists

Continuous profiling is only useful across a whole deployment if every component reports comparable data, and the OpenNMS packages do not provide that:

- **Core** bundles an agent, but an old one. Horizon 36 builds against pyroscope `0.13.1` (`<pyroscopeVersion>` in the OpenNMS pom) and its launcher loads it from `$OPENNMS_HOME/agent/pyroscope-agent.jar` when `PYROSCOPE_AGENT_ENABLED` is set.
- **Minion and Sentinel** ship no agent at all. Their packages contain no pyroscope jar and their launchers have no `PYROSCOPE_*` handling.

One pinned version installed by this role gives all three the same agent build.

## What it does, and what it does not

It downloads the jar, verifies its checksum, and puts it where the caller says. That is all.

It does **no** JVM wiring and knows nothing about services, because the three components load an agent in three different ways: Core through its own `PYROSCOPE_AGENT_ENABLED` launcher branch, Minion and Sentinel through `EXTRA_JAVA_OPTS` in their sysconfig file. Keeping that knowledge in the component roles means this role has one job and one failure mode.

Installing the jar does not enable profiling anywhere. See the component roles for their own toggles.

## Variables

| Variable | Default | Purpose |
|---|---|---|
| `pyroscope_agent_version` | `2.9.2` | Release to install. |
| `pyroscope_agent_url` | GitHub release asset | Download URL for the jar. |
| `pyroscope_agent_sha256` | digest of 2.9.2 | Checksum, in `get_url`'s `sha256:<digest>` form. |
| `pyroscope_agent_jar` | *(none)* | Absolute destination path, including filename. Asserted, not defaulted. |
| `pyroscope_agent_notify` | `[]` | Handlers to fire when the jar changes. |

The jar is installed `root:root 0644`, as the OpenNMS packages ship their own agent jars. There is deliberately no owner knob: a jar is not a secret, every component's JVM has to read it, and a service-owned `0640` jar breaks the moment the caller's user does not match the JVM's.

The destination directory is created only when missing, never enforced. Core and Sentinel both get an `agent` directory from their package — `opennms-common` 36.0.3 owns `/opt/opennms/agent`, and the postinst chowns it to the service user — so enforcing an owner would mean fighting dpkg over a directory this role only needs to be traversable.

### Why the destination has no default

Core's path is not ours to choose: `bin/opennms` hardcodes `$OPENNMS_HOME/agent/pyroscope-agent.jar`. Minion and Sentinel mirror that layout inside their own homes. Any default would therefore be wrong for two of the three callers, so the role fails loudly instead of installing the jar somewhere nothing reads it.

### Why a version bump needs a new checksum

Upstream publishes no `.sha256` asset next to the jar, so the digest in `defaults/main.yml` was taken from the downloaded artefact. Renovate cannot compute it, and `renovate.json` therefore tags its bump PRs with a note to update it. A stale digest fails the run rather than installing an unverified jar.

## Example

```yaml
- name: Install the Pyroscope Java agent
  ansible.builtin.include_role:
    name: pyroscope_agent
  vars:
    pyroscope_agent_jar: /opt/minion/agent/pyroscope-agent.jar
    pyroscope_agent_notify:
      - Restart minion
```

Usually you do not need to declare it: the component roles include it themselves.

## License

GPL-3.0-or-later
