# timesync

Verifies the host clock is synchronised before an OpenNMS component is deployed on it.

Included by `opennms_core`, `opennms_minion` and `opennms_sentinel`, so it runs for the full-stack playbook, the targeted `hzn-*-deployment.yml` playbooks, and standalone Galaxy consumers alike.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Why this exists

Clock skew between OpenNMS components is not cosmetic:

- **Kafka RPC requests carry a TTL.** If Core and Minion clocks disagree by more than it, every RPC expires — a hard functional break, not degradation.
- **Flow records carry timestamps.** Sentinel indexes them into Elasticsearch by time, so skew puts flows in the wrong buckets or outside ingest windows.
- **Collectors write time-series points.** A skewed clock writes points in the future, which RRD and Mimir both handle badly.

## What it checks, and what it does not

The role asserts that `timedatectl show --property=NTPSynchronized` reports `yes`.

It deliberately does **not** check whether an NTP client is installed or running. Those are different questions:

| Property | Question | Hypervisor-synced VM |
|---|---|---|
| `NTP` | is an NTP *client* enabled? | `no` |
| `NTPSynchronized` | is the clock *synchronised*? | `yes` |

A VM whose clock is kept by its hypervisor reports `NTP=no` with `NTPSynchronized=yes`. That is a correct, healthy state and the common case for this collection, so a check on `NTP` would fail most of a normal fleet.

**Limitation worth knowing:** `NTPSynchronized` reflects that the clock *has been* synchronised, not its current offset. A host synchronised once and drifting since can still report `yes`. It is the best portable signal available — there is no implementation-independent way to read the actual offset, because `timedatectl timesync-status` requires `systemd-timesyncd` and `chronyc tracking` requires chrony. A check that only worked on hosts running a specific daemon would be silently vacuous everywhere else, which is worse than being honest about this limit.

The role also distinguishes *"the clock is not synchronised"* from *"the check could not run"*. A check that cannot run must never be mistaken for one that passed.

## Variables

| Variable | Default | Purpose |
|---|---|---|
| `timesync_required` | `true` | Fail the deployment when the clock is not synchronised. |
| `timesync_install_chrony` | `false` | Install and enable chrony. |
| `timesync_retries` | `6` | Retries before failing. |
| `timesync_delay` | `10` | Seconds between retries. |

### Why chrony is off by default

Installing chrony masks `systemd-timesyncd` and takes over timekeeping. On a host whose clock is already kept correctly — by the hypervisor, by a corporate NTP setup, or by timesyncd — that replaces something working with chrony pointed at `pool.ntp.org`, which an air-gapped or firewalled network may not reach. Enable it for hosts that genuinely have no synchronisation at all.

Note that chrony refuses to run in a container: its unit carries `ConditionVirtualization=|!container`, because a container cannot own the system clock. Opting in there is a request that cannot be honoured, and the role fails rather than reporting success over a service systemd skipped.

### The retry window

NTP can take a minute or two to converge after boot, so a deployment run immediately after provisioning may see an unsynchronised clock that would settle on its own. The role retries before failing, so transient non-convergence is not reported as misconfiguration.

### Overriding the check

`timesync_required: false` lets a deployment proceed on a host whose clock is not synchronised — for a lab, an air-gapped rig with a deliberate offset, or a host where `timedatectl` is unavailable.

This is an exception to make knowingly. The check fails only when the clock genuinely is not synchronised, so overriding it is a statement about a specific environment rather than a way past a control that cries wolf.

## Example

```yaml
- hosts: minion
  roles:
    - indigo423.opennms.timesync
```

Usually you do not need to declare it: the component roles include it themselves.

## License

GPL-3.0-or-later
