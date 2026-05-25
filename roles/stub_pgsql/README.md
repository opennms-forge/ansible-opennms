# stub_pgsql

POC / test stub that deploys PostgreSQL with the OpenNMS database and user provisioned.

> **Not for production.** Use a dedicated PostgreSQL operator, managed service, or a cluster role with backup/HA for real deployments.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Variables

See [`defaults/main.yml`](defaults/main.yml).

## Example

```yaml
- hosts: postgresql
  roles:
    - indigo423.opennms.stub_pgsql
```

## License

GPL-3.0-or-later
