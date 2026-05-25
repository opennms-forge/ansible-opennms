# stub_mimir

POC / test stub that deploys Grafana Mimir for OpenNMS time-series storage.

> **Not for production.** Use a dedicated Mimir cluster role or the Grafana Cloud offering for real deployments.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Variables

See [`defaults/main.yml`](defaults/main.yml).

## Example

```yaml
- hosts: mimir
  roles:
    - indigo423.opennms.stub_mimir
```

## License

GPL-3.0-or-later
