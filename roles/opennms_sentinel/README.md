# opennms_sentinel

Deploys and configures OpenNMS Sentinel for distributed workload scaling and flow aggregation.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Package version pinning

This role writes an APT preferences file pinning the OpenNMS packages it installs.

**A routine `apt upgrade` will never move OpenNMS across a major release.** While the configured `opennms_version` is still carried by the repository, `apt upgrade` will not change the installed versions at all. That is deliberate: OpenNMS upgrades need a planned maintenance window.

Once the repository supersedes that exact version, `apt upgrade` may move OpenNMS to a newer patch *of the same major*. The repository serves one point release per dist, so this happens on the next OpenNMS point release — it is not a remote possibility. It is the deliberate cost of a pin that does not expire: a lone exact-version pin stops matching anything the moment its version is withdrawn, and a preferences file whose only entry has expired behaves exactly like no file at all, including permitting a jump to a different major.

The pin is therefore written in three tiers, most specific first:

| Tier | Matches | Priority | Effect |
|---|---|---|---|
| `version <opennms_version>-*` | the configured release, any Debian revision | 1001 | preferred; above 1000 so a deliberate downgrade is performed rather than ignored |
| `version <major>.*` | the same major | 900 | the fallback once the configured release is withdrawn |
| `release o=OpenNMS` | every other major | -1 | never selected automatically |

Tier 1 ends in `-*`, not a bare `*`: the pin is an fnmatch glob over the whole version string, so `36.0.1*` would also match `36.0.10` through `36.0.19` and — at priority 1001 — apt would apply that as a forced upgrade.

Order is load-bearing: APT applies the **first** matching entry, not the highest-priority one. `apt-cache policy <package>` reports the effective priority per available version and is the way to read the result.

The `-1` tier is not a lock. An explicit `apt-get install <package>=<version>` installs through it, which is why this role's own versioned install is unaffected.

To upgrade deliberately, change `opennms_version` and re-run the role. The pin is rewritten before the packages are installed, so the new version is permitted in the same run; there is no separate unpin step.

| Variable | Purpose |
|---|---|
| `opennms_pinned_packages` | The OpenNMS packages covered by the pin. |
| `opennms_apt_preferences_file` | Where the preferences file is written. |
| `opennms_pin_origin` | The repository's published `Origin` field, which the exclusion tier keys on. Not a hostname, so a mirror does not silently disable it. |

`rrdtool`, `jrrd2` and `iplike` are deliberately **not** pinned, though for different reasons. `rrdtool` is an ordinary Debian package and pinning it would block security updates to protect something that is not OpenNMS — the wrong trade. `jrrd2` and `iplike` are published only by `debian.opennms.org` and exist in no Debian suite, so there is no security stream to preserve for them; they are excluded because they are not OpenNMS itself. Whether they should be pinned anyway is an open question.

The APT source also targets an explicit per-major dist (`opennms-36`) rather than the floating `stable` alias, so a major-version jump cannot happen even if the pin is removed. See [`opennms_repositories`](../opennms_repositories/README.md).

### Unattended upgrades

`unattended-upgrades` is not a wrapper around `apt upgrade`.
It applies its own origin allowlist and its own package blacklist, and only part of its version selection consults APT policy.
Its behaviour against this pin was therefore measured rather than inferred, on Ubuntu 24.04 with `unattended-upgrades` 2.9.1.

**A cross-major move never happens.** With the preferences file present, no OpenNMS package was selected for a major upgrade, including on a host whose `Unattended-Upgrade::Origins-Pattern` had been deliberately widened to admit `o=OpenNMS`. `unattended-upgrades` defers to APT policy when it picks a version, so the other major sitting at `-1` is never chosen. Measured in isolation, the `-1` tier produces that result on its own, but it is not a file to deploy on its own: without tiers 1 and 2 the package has no installation candidate at all and deliberate installs fail.

**On a stock host, the pin is not what protects you.** Ubuntu's default `Unattended-Upgrade::Allowed-Origins` admits Ubuntu origins only, so a default host never considers `o=OpenNMS` packages and the pin is never reached. That protection belongs to the distribution's configuration, not to this collection, and it ends the moment an operator adds an origin pattern of their own.

**Moves within the major do happen, unattended.** There are two, and neither is bounded by an operator being present. Once the configured `opennms_version` is withdrawn from the repository, tier 2 lets an unattended host move to a newer patch of the same major. Separately, because tier 1 matches any Debian revision of the configured release, a new revision of the exact version you pinned (`36.0.3-1` to `36.0.3-2`) is selected at priority 1001 while tier 1 is still live. Either way OpenNMS moves and the service restarts on its own schedule. Under an interactive `apt upgrade` that cost is visible to whoever typed the command. Here it is not, and the first sign of it is usually a gap in the monitoring.

If that is not an acceptable trade, add the pinned packages to `unattended-upgrades`' own blacklist. This was measured to stop it:

```
// /etc/apt/apt.conf.d/51-opennms-blacklist
Unattended-Upgrade::Package-Blacklist {
    "<package>$";
};
```

One `$`-anchored entry per package in this role's `opennms_pinned_packages`, plus those of any other OpenNMS role applied to the same host. The blacklist is a gate separate from APT pinning, so it applies whatever the preferences file says, and it covers both of the moves above. This collection does not write that file.

Not measured: Debian's stock origin set, and `unattended-upgrades` releases other than 2.9.1. If you run something else, the property to check is whether its candidate selection defers to APT policy.

## Variables

See [`defaults/main.yml`](defaults/main.yml).

## Credentials

This role refuses to run while `opennms_datasource_db_password` is the sentinel default `__SET_VIA_VAULT__`. Bootstrap real credentials once with:

```bash
ansible-playbook -i <your inventory> indigo423.opennms.init_secrets
```

See the [collection README](../../README.md#-first-time-setup-bootstrap-database-credentials) for the full vault workflow.

## Example

```yaml
- hosts: opennms_sentinel
  roles:
    - indigo423.opennms.opennms_sentinel
```

## License

GPL-3.0-or-later
