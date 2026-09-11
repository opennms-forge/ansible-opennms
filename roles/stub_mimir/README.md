# stub_mimir

POC / test stub that deploys Grafana Mimir for OpenNMS time-series storage.

> **Not for production.** Use a dedicated Mimir cluster role or the Grafana Cloud offering for real deployments.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## What this role owns, and what it delegates

The Mimir lifecycle is delegated to [`indigo423.grafana.mimir`](https://galaxy.ansible.com/ui/repo/published/indigo423/grafana/): the package, `/etc/mimir/config.yml` (validated with `mimir -modules` before it lands), the restart on change, the start, and the wait for `/ready`.
This role runs before it and hands it the configuration as dicts.

What stays here is what a generic Mimir role does not know:

- the systemd drop-in that takes `mimir.service` out of the start rate limit, written **before** the package is installed (see below);
- the cluster shape, derived from `mimir_cluster_group` membership: members, KV store, replication factor, memberlist join list;
- the explicit address in every ring and in the query-frontend (see below);
- `multitenancy_enabled: false`, so OpenNMS can push with no tenant header, and the per-tenant limits sized for a benchmark;
- the two assertions: a cluster needs shared object storage, and an address must be available.

The fork's template has no named section for `multitenancy_enabled`, `store_gateway`, `compactor` or `frontend`; those travel in its `mimir_config_extra` passthrough, which is why the collection requires `indigo423.grafana` 7.1.0 or newer.

## Variables

See [`defaults/main.yml`](defaults/main.yml).

**Version.** This role declares no `mimir_version`; the fork's pin applies.
Set `mimir_version` in inventory to override it, the name is the same in both roles.

**Renamed and removed.** Setting any of these fails the run with a message naming the replacement:

| Was | Now |
|---|---|
| `mimir_http_port` | `mimir_http_listen_port` (the fork's name, same value) |
| `mimir_data_dir` | `mimir_working_path` (the fork's name, same path) |
| `mimir_arch` | removed; the fork derives it from facts |
| `mimir_pkg_url` | removed; a mirror sets the fork's `mimir_download_url_deb` |

`mimir_startup_retries` and `mimir_startup_delay` keep their names and defaults and are passed into the fork's `mimir_ready_retries` and `mimir_ready_delay`, whose own defaults allow only 40 seconds.

`mimir_restart_sec` (default `5`) is the interval systemd waits between restarts of `mimir.service`.
It exists because of the unit override described below.

Two things the fork's role does differently from what this role used to do, both accepted: the working directory is created `0755` rather than `0750`, and the rendered configuration also carries `target: all,alertmanager,overrides-exporter` and the ruler and alertmanager paths the fork always writes.

## Checking the derivations

`make check-render` renders the dicts this role assembles, from `templates/_check-render-dicts.yml.j2`, against a single-node and a cluster fixture.
That template is never deployed; the configuration file is rendered by the fork from those dicts and is the fork's test to keep.

## Ring addressing

Mimir resolves its own advertised address by detecting interfaces that carry a private (RFC 1918) address, falling back to the literal list `[eth0, en0]` when it finds none.
On a host addressed only out of a non-private range — `192.0.2.0/24`, say — the detection finds nothing, the fallback matches no predictable interface name, and Mimir exits with `no useable address found for interfaces [eth0 en0]`.

The role takes that guess away by writing the address explicitly into every ring, into memberlist, and into the query-frontend and alertmanager.
Memberlist gets it on a single node too: the fork runs Mimir with the alertmanager module enabled, which initialises the memberlist KV service even with in-memory rings, and that service resolves its own address the same way.
It is chosen in this order:

| Precedence | Source |
|---|---|
| 1 | `mimir_instance_addr`, set directly |
| 2 | `lab_mgmt_ip`, from the benchmark lab's inventory |
| 3 | the host's default-route address (`ansible_default_ipv4.address`) |

`lab_mgmt_ip` keeps precedence over the derived value deliberately: the benchmark beds carry Mimir's peer traffic on a subnet other than the default route, so the derived address would name the wrong NIC there.

If none of the three yields a value the role **fails**, rather than rendering a configuration whose startup depends on interface detection.
In practice that means a play with `gather_facts: false` must set `mimir_instance_addr` itself.

An address is written for single-node deployments too.
In-memory rings do not exempt them: the ring lifecycler needs an address to register itself whatever the KV store is, which was measured on a single-node host after removing its only private-range address.

## Unit override

The role installs a systemd drop-in at `/etc/systemd/system/mimir.service.d/override.conf`, before the fork's role installs the package, setting `StartLimitIntervalSec=0` and `RestartSec`.

The Mimir package starts `mimir.service` from its `postinst`, on the effectively empty `/etc/mimir/config.yml` it ships.
With no configuration, Mimir's ring lifecycler detects interfaces carrying a private (RFC 1918) address and falls back to the literal list `[eth0, en0]` when it finds none.
On a host addressed only out of a non-private range, that fallback matches no predictable interface name and Mimir exits.
The vendor unit declares `Restart=always` with no start-limit overrides, so systemd's default of five starts in ten seconds is exhausted in about two seconds and the unit is locked out — before the role has written anything.
Whether the deploy then failed was a race against that ten-second window, which made it look like an intermittent configuration fault rather than an ordering one.

`StartLimitIntervalSec=0` removes the lockout.
`RestartSec` is set alongside it because `Restart=always` with no rate limit would otherwise leave a genuinely broken Mimir restarting at systemd's 100 ms default.

Two consequences worth knowing:

- `no useable address found for interfaces [eth0 en0]` appears in the journal once per package install on a host with no private-range address, from the postinst's start attempt. It is expected and harmless; the role's own start runs on the rendered configuration. A host that does have a private-range address never logs it, because the install-time start succeeds outright.
- Deleting the drop-in and running `systemctl daemon-reload` restores Grafana's stock unit behaviour, including the lockout.

## Example

```yaml
- hosts: mimir
  roles:
    - indigo423.opennms.stub_mimir
```

## License

GPL-3.0-or-later
