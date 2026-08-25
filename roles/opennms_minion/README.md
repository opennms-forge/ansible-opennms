# opennms_minion

Deploys and configures the OpenNMS Minion agent for monitoring isolated network segments.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Package version pinning

This role writes an APT preferences file pinning the OpenNMS packages it installs to `opennms_version`.

**A routine `apt upgrade` will not move OpenNMS.** That is deliberate: OpenNMS upgrades need a planned maintenance window, and an unplanned jump — potentially across a major release — is exactly what this prevents.

To upgrade deliberately, change `opennms_version` and re-run the role. The pin is rewritten before the packages are installed, so the new version is permitted in the same run; there is no separate unpin step.

| Variable | Purpose |
|---|---|
| `opennms_pinned_packages` | The OpenNMS packages covered by the pin. |
| `opennms_apt_preferences_file` | Where the preferences file is written. |

`rrdtool`, `jrrd2` and `iplike` are deliberately **not** pinned. They are ordinary system packages, and blocking their security updates to protect something that is not OpenNMS would be the wrong trade.

The APT source also targets an explicit per-major dist (`opennms-36`) rather than the floating `stable` alias, so a major-version jump cannot happen even if the pin is removed. See [`opennms_repositories`](../opennms_repositories/README.md).

## Kafka IPC configuration

`opennms_minion_kafka` is the **common** configuration, rendered to `etc/org.opennms.core.ipc.kafka.cfg`. The sink, rpc and twin modules all use it unless given their own configuration.

To point a module at a different broker, set its dictionary. Each renders its own Karaf PID file, and each is written only when non-empty:

| Variable | Renders |
|---|---|
| `opennms_minion_kafka` | `org.opennms.core.ipc.kafka.cfg` |
| `opennms_minion_kafka_sink` | `org.opennms.core.ipc.sink.kafka.cfg` |
| `opennms_minion_kafka_rpc` | `org.opennms.core.ipc.rpc.kafka.cfg` |
| `opennms_minion_kafka_twin` | `org.opennms.core.ipc.twin.kafka.cfg` |

### A module configuration is complete, not a delta

This is the part that surprises people, and the upstream documentation is misleading about it. The docs say module values *"take precedence over common configuration values"*, which sounds like a key-level override. It is not. OpenNMS selects a **whole file**:

```
module file HAS bootstrap.servers    →  module file used in full, common file ignored
module file LACKS bootstrap.servers  →  module file ignored in full, common file used
```

`OsgiKafkaConfigProvider` reads the module PID and checks for `bootstrap.servers`; if it is absent it discards those properties entirely and falls back to the common PID. So a module file containing only `group.id` has **no effect at all** — the module silently keeps using the common configuration.

Because of that, every module dictionary must repeat `bootstrap.servers` even when it matches the common one. That duplication is a runtime requirement, not a quirk of this role. The role refuses to render a module file without it, rather than let the misconfiguration pass silently:

```
`opennms_minion_kafka_sink` is set but does not define `bootstrap.servers`. …
A module file without it has no effect at all.
```

Note also that module settings cannot be expressed as prefixed keys inside the common dictionary — in Karaf the `.cfg` filename *is* the PID, so `org.opennms.core.ipc.sink.kafka.group.id` placed in the common file is just an oddly-named property that nothing reads.

### Example: sink and rpc on different clusters

```yaml
opennms_minion_kafka:
  "bootstrap.servers": kafka.example.org:9092

opennms_minion_kafka_sink:
  "bootstrap.servers": sink-kafka.example.org:9092   # required, even to repeat
  "group.id": HQ-Minion-Sink

opennms_minion_kafka_rpc:
  "bootstrap.servers": rpc-kafka.example.org:9092
  "group.id": HQ-Minion-RPC
```

Twin is left unset here, so it keeps using the common configuration.

### Going back to the common configuration

Remove the module's variable and re-run. The role deletes that module's `.cfg` file, so the module falls back to the common PID.

Deleting the file matters: a leftover module file still defines `bootstrap.servers`, and OpenNMS would keep selecting it in full — leaving the module pointed at a broker you thought you had removed, with the Ansible run reporting clean.

## Variables

See [`defaults/main.yml`](defaults/main.yml).

## Example

```yaml
- hosts: opennms_minion
  roles:
    - indigo423.opennms.opennms_minion
```

## License

GPL-3.0-or-later
