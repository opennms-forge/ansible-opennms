# opennms_sentinel

Deploys and configures OpenNMS Sentinel for distributed workload scaling and flow aggregation.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Variables

See [`defaults/main.yml`](defaults/main.yml).

## Example

```yaml
- hosts: opennms_sentinel
  roles:
    - indigo423.opennms.opennms_sentinel
```

## License

GPL-3.0-or-later
