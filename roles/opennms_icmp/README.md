# opennms_icmp

Installs `jicmp` / `jicmp6` native libraries used by OpenNMS Horizon components for ICMP monitoring.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Variables

See [`defaults/main.yml`](defaults/main.yml).

## Example

```yaml
- hosts: all
  roles:
    - indigo423.opennms.opennms_icmp
```

## License

GPL-3.0-or-later
