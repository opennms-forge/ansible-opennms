# stub_kafka

POC / test stub that deploys Apache Kafka 4.x in KRaft mode for OpenNMS IPC.

> **Not for production.** Use a dedicated Kafka operator or cluster role for real deployments.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Variables

See [`defaults/main.yml`](defaults/main.yml).

## Base64 intrinsics

Off by default.
The role sets `KAFKA_OPTS=-XX:-UseBASE64Intrinsics` in the systemd unit.
That is the workaround for CVE-2026-114938, a heap overflow in HotSpot's AVX-512 Base64 decoder on x86-64.
The option is harmless on ARM64 and on CPUs without AVX-512 VBMI.
Once the host runs a fixed JDK (17.0.21.1, 21.0.13.1, 25.0.5.1 or newer), turn the intrinsics back on:

```yaml
kafka_base64_intrinsics: true
```

Changing the value restarts Kafka.

## Example

```yaml
- hosts: kafka
  roles:
    - indigo423.opennms.stub_kafka
```

## License

GPL-3.0-or-later
