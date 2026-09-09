# stub_pyroscope

Single-node [Grafana Pyroscope](https://github.com/grafana/pyroscope) server, so the profiles the Horizon components emit have somewhere to go.

**POC and test only.** Profiles land on local disk, with no object store, no retention policy and no authentication in front of them.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Why this is in scope

The collection's rule is that a role belongs here when OpenNMS has a wire to the system it deploys. The Core, Minion and Sentinel JVMs push profiles to Pyroscope through the agent the [`pyroscope_agent`](../pyroscope_agent/README.md) role installs, so the wire exists and points here. Without this role the profiling those three roles configure has no endpoint, and the collection can only be half of that story.

## What it does

Installs the release `.deb` — which brings the `pyroscope` user, a systemd unit and a working single-node configuration — then replaces the shipped reference configuration with a managed one and waits for the server to actually serve.

The package's own configuration is a 28 KB fully-commented reference file, i.e. every setting at its default. The managed file therefore writes only what this role owns:

```yaml
target: all

server:
  http_listen_port: 4040
  log_level: info

storage:
  backend: filesystem
```

`target: all` is monolithic mode: every component runs in one process, which is what makes the in-process rings and the local metastore correct.

## Variables

| Variable | Default | Purpose |
|---|---|---|
| `pyroscope_version` | `2.3.1` | Server release. Unrelated to the agent version. |
| `pyroscope_arch` | `amd64` | Package architecture (`amd64` or `arm64`). |
| `pyroscope_pkg_url` | GitHub release asset | Download URL for the `.deb`. |
| `pyroscope_http_port` | `4040` | API and UI port. |
| `pyroscope_log_level` | `info` | Log level. |
| `pyroscope_data_dir` | `/var/lib/pyroscope` | Where profiles are stored. |
| `pyroscope_startup_retries` | `24` | Readiness polls before failing. |
| `pyroscope_startup_delay` | `5` | Seconds between polls. |

### Why the data directory is a WorkingDirectory, not a config key

Pyroscope v2 resolves five separate paths relative to the process working directory: pyroscopedb (`./data`), the metastore's raft log and data (`./data/v2/metastore/{raft,data}`), shared object storage (`./data/v2/shared`) and the embedded Grafana. Moving the data by configuration would mean tracking every one of them and re-checking the list on each release. Moving the directory the process runs in relocates all of them at once and cannot drift, so the role writes a unit drop-in instead.

### Why the role waits for `/ready`

`state: started` reports success as soon as the process exists, but Pyroscope serves nothing for roughly the first 90 seconds of a cold start, because its components report ready in series rather than together:

```
Metastore not ready: 14.999999083s before reporting readiness
Ingester not ready: waiting for 15s after being ready
Segment Writer not ready: waiting for 30s after being ready
```

Measured on 2.3.1. Without the readiness gate the role would report success on a host that cannot yet accept a single profile.

Unlike [`stub_mimir`](../stub_mimir/README.md), no start-rate-limit drop-in is needed: the Mimir package starts on a configuration it cannot run and locks its unit out before Ansible writes anything, while Pyroscope's shipped configuration is valid and starts cleanly.

## Sending profiles to it

Profiling is off by default on all three components. Point them at this host and switch it on:

```yaml
# Core - merged over the role defaults
opennms_jvm_conf:
  PYROSCOPE_AGENT_ENABLED: 1
  PYROSCOPE_SERVER_ADDRESS: http://pyroscope-host:4040

opennms_minion_pyroscope:
  PYROSCOPE_APPLICATION_NAME: Horizon-Minion
  PYROSCOPE_SERVER_ADDRESS: http://pyroscope-host:4040

opennms_sentinel_pyroscope:
  PYROSCOPE_APPLICATION_NAME: Horizon-Sentinel
  PYROSCOPE_SERVER_ADDRESS: http://pyroscope-host:4040
```

To confirm profiles are arriving, ask the server which applications it knows about:

```console
$ curl -sS -X POST http://pyroscope-host:4040/querier.v1.QuerierService/LabelValues \
    -H 'content-type: application/json' -d '{"name":"service_name"}'
{"names":["Horizon-Core", "Horizon-Minion", "pyroscope"]}
```

`pyroscope` in that list is the server profiling itself.

## Example

```yaml
- hosts: pyroscope
  roles:
    - indigo423.opennms.stub_pyroscope
```

## License

GPL-3.0-or-later
