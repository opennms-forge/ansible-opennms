# akvorado

Benchmark **stub** role: deploys the [Akvorado](https://github.com/akvorado/akvorado)
flow collector via Docker Compose, writing to an **external** ClickHouse rather
than the one bundled in upstream's compose stack. Not a production-grade
Akvorado deployment.

## Approach

Upstream's compose stack is vendored at a pinned tag rather than reimplemented.
That stack is more than a list of containers: the orchestrator acts as a config
service that inlet, outlet and console fetch from at boot, tied together by a
healthcheck dependency graph, and Traefik injects the `Remote-User` header the
console authenticates with. Re-deriving that is more work and more risk than
tracking it.

The role therefore:

1. Unpacks the release tarball to `/opt/akvorado/akvorado-<version>/`.
2. Writes `docker/docker-compose-local.yml` — upstream's documented override
   slot, already in the `COMPOSE_FILE` chain of the shipped `.env`, so `.env`
   itself is left untouched.
3. Replaces `config/akvorado.yaml` to point `clickhousedb.servers` at the
   external node. `inlet.yaml`, `outlet.yaml` and `console.yaml` stay as
   upstream ships them via `!include`.
4. Brings the stack up with `community.docker.docker_compose_v2`.

The bundled `clickhouse` service is parked in an unused profile — upstream's
documented way to disable a service. Because console and outlet declare a
healthcheck dependency on it, their `depends_on` is *replaced* (`!override`)
rather than merged, otherwise Compose pulls the disabled service back in.

## Requirements

- Docker Engine with the Compose v2 plugin on the target host.
- A reachable ClickHouse (see `stub_clickhouse`).

## Variables

| Variable | Default | Purpose |
|---|---|---|
| `akvorado_version` | `2.4.1` | Upstream tag to vendor |
| `akvorado_clickhouse_servers` | `[]` | **Required.** External ClickHouse, e.g. `["ch-benchmark-01:9000"]` |
| `akvorado_kafka_brokers` | `[kafka:9092]` | In-stack Kafka, Akvorado's own inlet → outlet buffer |
| `akvorado_http_port` | `8080` | Host port for the console, published from Traefik |
| `akvorado_networks` | `192.0.2.0/24` → lab | Populates `Src/DstNetName` in the console |
| `akvorado_demo_exporters` | `false` | Enable upstream's synthetic flow exporters |

`akvorado_demo_exporters` exists because the lab's Deployment H has no load
generator — it is how the flow path gets exercised end to end.

## Ports

| Port | Purpose |
|---|---|
| `8080/tcp` | Console (configurable) |
| `2055/udp` | NetFlow |
| `4739/udp` | IPFIX |
| `6343/udp` | sFlow |

## Example

```yaml
- name: Manage Akvorado
  hosts: akvorado
  become: true
  roles:
    - indigo423.opennms.common
    - role: indigo423.opennms.akvorado
      vars:
        akvorado_clickhouse_servers:
          - "ch-benchmark-01:9000"
        akvorado_demo_exporters: true
```
