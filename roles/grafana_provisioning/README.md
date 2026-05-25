# grafana_provisioning

Drops the OpenNMS Grafana app plugin provisioning file so the plugin installed by the `grafana.grafana` collection is enabled.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Variables

See [`defaults/main.yml`](defaults/main.yml).

## Example

```yaml
- hosts: all
  roles:
    - indigo423.opennms.grafana_provisioning
```

## License

GPL-3.0-or-later
