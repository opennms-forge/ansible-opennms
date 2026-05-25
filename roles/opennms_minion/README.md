# opennms_minion

Deploys and configures the OpenNMS Minion agent for monitoring isolated network segments.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

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
