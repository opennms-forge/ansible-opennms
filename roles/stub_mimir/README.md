# stub_mimir

POC / test stub that deploys Grafana Mimir for OpenNMS time-series storage.

> **Not for production.** Use a dedicated Mimir cluster role or the Grafana Cloud offering for real deployments.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Variables

See [`defaults/main.yml`](defaults/main.yml).

`mimir_restart_sec` (default `5`) is the interval systemd waits between restarts of `mimir.service`.
It exists because of the unit override described below.

## Ring addressing

Mimir resolves its own advertised address by detecting interfaces that carry a private (RFC 1918) address, falling back to the literal list `[eth0, en0]` when it finds none.
On a host addressed only out of a non-private range — `192.0.2.0/24`, say — the detection finds nothing, the fallback matches no predictable interface name, and Mimir exits with `no useable address found for interfaces [eth0 en0]`.

The role takes that guess away by writing the address explicitly into every ring, into memberlist, and into the query-frontend and alertmanager.
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

The role installs a systemd drop-in at `/etc/systemd/system/mimir.service.d/override.conf`, before installing the package, setting `StartLimitIntervalSec=0` and `RestartSec`.

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
