# grafana_provisioning

Installs the OpenNMS Grafana app plugin (`opennms-opennms-app`) via `grafana-cli` and drops the provisioning file that enables it. Both steps notify a `restart_grafana` handler so a co-located `grafana.grafana.grafana` role picks up the new plugin on its next service restart.

Run this role **after** `grafana.grafana.grafana` (or any equivalent Grafana install role) on the same host — `grafana-cli` and the `/var/lib/grafana/plugins` directory must already exist.

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
