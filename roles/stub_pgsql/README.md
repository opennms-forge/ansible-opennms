# stub_pgsql

POC / test stub that deploys PostgreSQL with the OpenNMS database and user provisioned.

> **Not for production.** Use a dedicated PostgreSQL operator, managed service, or a cluster role with backup/HA for real deployments.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## EL 10

On EL 10 the role installs PostgreSQL from the PGDG yum repository and runs `postgresql-<version>-setup initdb` once, into an empty data directory.
Configuration and data live under `/var/lib/pgsql/<version>/data`, and the unit is `postgresql-<version>`.

PGDG signs its RPMs and metadata with `PGDG-RPM-GPG-KEY-RHEL`, verified by fingerprint through `pgsql_rpm_key_fingerprints`.
That key covers x86_64.
PGDG signs aarch64 with `PGDG-RPM-GPG-KEY-AARCH64-RHEL` (`B031F89FC983E98262906B6E177B343BB9738825`), which you set through `pgsql_rpm_key_url` and `pgsql_rpm_key_fingerprints`.

OpenNMS publishes no `iplike-pgsql18` for EL 10, so the role installs no C iplike there.
The OpenNMS installer then creates its PL/pgSQL iplike during `install -dis`.
It answers the same queries, more slowly for IP-range filters.

## Variables

See [`defaults/main.yml`](defaults/main.yml).

## Credentials

This role refuses to run while `postgres_password` or `opennms_datasource_db_password` is the sentinel default `__SET_VIA_VAULT__`. Bootstrap real credentials once with:

```bash
ansible-playbook -i <your inventory> indigo423.opennms.init_secrets
```

See the [collection README](../../README.md#-first-time-setup-bootstrap-database-credentials) for the full vault workflow.

## Example

```yaml
- hosts: postgresql
  roles:
    - indigo423.opennms.stub_pgsql
```

## License

GPL-3.0-or-later
