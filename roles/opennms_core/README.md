# opennms_core

Deploys and configures OpenNMS Horizon Core: server packages, webapp, database initialization, Kafka IPC, JVM tuning, JMX Prometheus exporter, and UFW firewall rules.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Variables

See [`defaults/main.yml`](defaults/main.yml).

## Example

```yaml
- hosts: opennms_core
  roles:
    - indigo423.opennms.opennms_core
```

## License

GPL-3.0-or-later
