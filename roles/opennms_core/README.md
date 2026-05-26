# opennms_core

Deploys and configures OpenNMS Horizon Core: server packages, webapp, database initialization, Kafka IPC, JVM tuning, JMX Prometheus exporter, and UFW firewall rules.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Variables

See [`defaults/main.yml`](defaults/main.yml) for the full list. The most relevant variables for tuning datasource and service behavior are documented below.

### Datasource configuration

Connection parameters are exported as environment variables in `/opt/opennms/etc/opennms.conf`. OpenNMS Horizon 36's pristine `opennms-datasources.xml` resolves these via the chain:

```
${scv:<key>:<field> | env:<VAR> | <literal default>}
       |                  |              |
       |                  |              `- baked into the pristine XML
       |                  `- exported by Ansible via opennms.conf
       `- populated by scvcli set (this role)
```

Credentials flow through the Secure Credential Vault (SCV) — populated by `scvcli set postgres ...` and `scvcli set postgres-admin ...` in `10-database-setup.yml`. Host, port, and dbname flow through env vars in `opennms.conf`. SSL and connection-pool tunables are left to the pristine XML's literal defaults unless you explicitly set them.

| Legacy variable | Env var rendered |
|---|---|
| `opennms_datasource_db_host` | `POSTGRES_HOST` |
| `opennms_datasource_db_port` | `POSTGRES_PORT` |
| `opennms_datasource_db_name` | `OPENNMS_DBNAME` |

For everything else — SSL mode, connection-pool sizes, or any env var the pristine `opennms-datasources.xml` resolves via `${env:...}` — set `opennms_env`. Entries are **merged on top of** the role's built-in env defaults; keys you don't set keep their defaults:

```yaml
opennms_env:
  POSTGRES_HOST: db.example.com               # override host
  POSTGRES_SSL_MODE: require                  # tighten SSL
  OPENNMS_DATABASE_CONNECTION_MAXPOOL: 100    # raise the main pool ceiling
```

The pristine Horizon 36 `opennms-datasources.xml` defaults are: `POSTGRES_SSL_MODE=prefer`, `POSTGRES_SSL_FACTORY=org.postgresql.ssl.LibPQFactory`, `OPENNMS_DATABASE_CONNECTION_IDLETIMEOUT=600`, `LOGINTIMEOUT=3`, `MINPOOL=25`, `MAXPOOL=50`, `MAXSIZE=50`.

### Service toggles

Daemons can be enabled/disabled via `opennms_services`. Each key is a `CORE_SERVICE_<NAME>_ENABLED` env var consumed by the pristine `service-configuration.xml`:

```yaml
opennms_services:
  CORE_SERVICE_TELEMETRYD_ENABLED: false   # disable when Sentinel handles flows
  CORE_SERVICE_SYSLOGD_ENABLED: true       # enable syslog ingestion on Core
```

Empty by default; upstream defaults apply for every unmodified service. `Manager` and `Eventd` are not toggleable.

## Example

```yaml
- hosts: opennms_core
  roles:
    - indigo423.opennms.opennms_core
```

## Migration from earlier role versions

Earlier versions of this role rendered `/opt/opennms/etc/opennms-datasources.xml` from a Jinja template. The current version instead trusts the pristine XML shipped by the `opennms-server` deb package and drives runtime values through env vars and SCV.

On the first run after upgrading:

- If the on-disk `opennms-datasources.xml` contains the marker comment `This is an Ansible managed template` (left by the previous version), the role copies the pristine file from `/usr/share/opennms/etc-pristine/opennms-datasources.xml` over it and triggers a restart.
- If the file does not contain that marker, the role treats it as user-customized and leaves it untouched. A debug message notes the divergence; overrides via `opennms.conf` env vars still apply where the file uses `${env:...}` placeholders.

If the role's signature-match incorrectly classifies a customized file (e.g., you intentionally kept the original template's header comment), the migration is non-destructive: `ansible.builtin.copy` runs with `backup: true`, leaving the pre-overwrite content at `/opt/opennms/etc/opennms-datasources.xml.NNNNN.YYYY-MM-DD@HH:MM:SS~`. Restore from there if needed.

To force a manual migration of a user-customized file, first run `apt-get install --reinstall opennms-server` (which restores the pristine copy), then re-run the role.

## Security notes

The defaults `opennms_datasource_db_password` and `postgres_password` carry plaintext POC-grade values. Override them via Ansible Vault for any deployment beyond local testing.

## License

GPL-3.0-or-later
