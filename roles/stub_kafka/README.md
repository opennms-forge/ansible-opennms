# stub_kafka

POC / test stub that deploys Apache Kafka 4.x in KRaft mode for OpenNMS IPC.

> **Not for production.** Use a dedicated Kafka operator or cluster role for real deployments.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Variables

See [`defaults/main.yml`](defaults/main.yml).

## Example

```yaml
- hosts: kafka
  roles:
    - indigo423.opennms.stub_kafka
```

## License

GPL-3.0-or-later
