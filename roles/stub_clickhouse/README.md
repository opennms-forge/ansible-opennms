# stub_clickhouse

Benchmark **stub** role: installs a single-node ClickHouse from the upstream apt
repository and runs it as a systemd service on `:8123` (HTTP) and `:9000`
(native). Intended as the flow-storage backend for `akvorado`, which creates and
migrates its own schema. Not a production-grade ClickHouse deployment.

## What it does

- Adds the ClickHouse apt repository (`packages.clickhouse.com/deb stable`).
- Installs `clickhouse-common-static`, `clickhouse-server` and `clickhouse-client`,
  all pinned to the same `clickhouse_version` — the server refuses to start
  against a mismatched `clickhouse-common-static`.
- Drops `/etc/clickhouse-server/config.d/10-lab-listen.xml` to set the listen
  address, ports and data path. Using `config.d` rather than editing `config.xml`
  means a package upgrade cannot silently revert the listen address.

## Not production

- Listens on `0.0.0.0` so a separate Akvorado host can reach it. Acceptable only
  because the lab sits on a private subnet.
- Keeps the packaged `default` user with no password and applies no resource
  limits, quotas or TLS.

## Variables

| Variable | Default | Purpose |
|---|---|---|
| `clickhouse_version` | `26.7.1.1315` | Exact package version, applied to all three packages |
| `clickhouse_http_port` | `8123` | HTTP interface |
| `clickhouse_tcp_port` | `9000` | Native protocol |
| `clickhouse_data_dir` | `/var/lib/clickhouse` | Storage path |
| `clickhouse_listen_host` | `0.0.0.0` | Listen address |
| `clickhouse_arch` | `amd64` | Repository architecture |
| `clickhouse_apt_key_url` | ClickHouse `repomd.xml.key` | Repository signing key (served from the `rpm/lts` path, not `deb`) |

## Example

```yaml
- name: Manage ClickHouse
  hosts: clickhouse
  become: true
  roles:
    - indigo423.opennms.common
    - indigo423.opennms.stub_clickhouse
```
