# opennms_minion

Deploys and configures the OpenNMS Minion agent for monitoring isolated network segments.

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
Its behaviour against this pin was therefore measured rather than inferred, on Ubuntu 24.04 with `unattended-upgrades` 2.9.1 and Debian 13 with 2.12.

**A cross-major move never happens.** With the preferences file present, no OpenNMS package was selected for a major upgrade, including on a host whose origin allowlist had been deliberately widened to admit `o=OpenNMS`. `unattended-upgrades` defers to APT policy when it picks a version, so the other major sitting at `-1` is never chosen.

**On a stock host, the pin is not what protects you.** Both Ubuntu's and Debian's default allowlists admit only their own origins, so a default host never considers `o=OpenNMS` packages and the pin is never reached. That protection belongs to the distribution's configuration, not to this collection, and it ends the moment an operator adds an origin pattern of their own.

**Two within-major moves are prevented by default.** The preferences file cannot express *prefer exactly this version, and if it is gone, do nothing*: a `-1` on everything would say it, but it leaves the package with no installation candidate and breaks a deliberate install. So two of its tiers admit a version an unattended host will move to, and both were measured moving:

| Path | When it fires |
|---|---|
| tier 1 at 1001 | a new Debian revision of the configured version ships, because the tier matches `<version>-*`. The exact version you pinned moves and the service restarts, on a day nothing here changed |
| tier 2 at 900 | the configured version is withdrawn from the repository and a newer patch of the same major is available |

Each installing role therefore also writes `/etc/apt/apt.conf.d/51-opennms-<role>-blacklist`, adding its `opennms_pinned_packages` to `Unattended-Upgrade::Package-Blacklist`. That is a gate separate from candidate selection, so it stops both moves without touching what APT will install when asked directly.

| Variable | Purpose |
|---|---|
| `opennms_unattended_upgrade_blacklist` | Whether to write the blacklist. Default `true`. Setting it `false` removes the file and re-exposes **both** moves above. |
| `opennms_unattended_blacklist_file` | Where the drop-in is written. The **default** is named per role, so several OpenNMS roles on one host do not overwrite each other. The variable name is shared across the roles, as `opennms_apt_preferences_file` is, so setting it once in `group_vars` for a multi-role host points every role at one path and the last to run wins. Override it per role or not at all. |

Several OpenNMS roles on one host each write their own file, at the per-role default paths. APT accumulates list entries across `apt.conf.d` rather than letting the last definition win, so the effective blacklist is the union of their package lists.

If you previously followed this section's earlier advice and hand-wrote `/etc/apt/apt.conf.d/51-opennms-blacklist`, remove it. The roles do not manage that path, so it survives `opennms_unattended_upgrade_blacklist: false` and would keep blacklisting after you opted out.

**The cost.** An OpenNMS patch that is also a security fix will not land unattended. To take it, change `opennms_version` and re-run: the blacklist gates `unattended-upgrades` and not APT, so a deliberate `apt-get install <package>=<version>` and this role's own versioned install both go through it untouched.

Turning the blacklist off does not affect the cross-major protection. That is the preferences file's `-1` tier, and it was measured to govern `unattended-upgrades` on its own.

Not measured: `unattended-upgrades` releases other than the two named above. If you run something else, the property to check is whether its candidate selection defers to APT policy.

## Kafka IPC configuration

`opennms_minion_kafka` is the **common** configuration, rendered to `etc/org.opennms.core.ipc.kafka.cfg`. The sink, rpc and twin modules all use it unless given their own configuration.

To point a module at a different broker, set its dictionary. Each renders its own Karaf PID file, and each is written only when non-empty:

| Variable | Renders |
|---|---|
| `opennms_minion_kafka` | `org.opennms.core.ipc.kafka.cfg` |
| `opennms_minion_kafka_sink` | `org.opennms.core.ipc.sink.kafka.cfg` |
| `opennms_minion_kafka_rpc` | `org.opennms.core.ipc.rpc.kafka.cfg` |
| `opennms_minion_kafka_twin` | `org.opennms.core.ipc.twin.kafka.cfg` |

### A module configuration is complete, not a delta

This is the part that surprises people, and the upstream documentation is misleading about it. The docs say module values *"take precedence over common configuration values"*, which sounds like a key-level override. It is not. OpenNMS selects a **whole file**:

```
module file HAS bootstrap.servers    →  module file used in full, common file ignored
module file LACKS bootstrap.servers  →  module file ignored in full, common file used
```

`OsgiKafkaConfigProvider` reads the module PID and checks for `bootstrap.servers`; if it is absent it discards those properties entirely and falls back to the common PID. So a module file containing only `group.id` has **no effect at all** — the module silently keeps using the common configuration.

Because of that, every module dictionary must repeat `bootstrap.servers` even when it matches the common one. That duplication is a runtime requirement, not a quirk of this role. The role refuses to render a module file without it, rather than let the misconfiguration pass silently:

```
`opennms_minion_kafka_sink` is set but does not define `bootstrap.servers`. …
A module file without it has no effect at all.
```

Note also that module settings cannot be expressed as prefixed keys inside the common dictionary — in Karaf the `.cfg` filename *is* the PID, so `org.opennms.core.ipc.sink.kafka.group.id` placed in the common file is just an oddly-named property that nothing reads.

### Example: sink and rpc on different clusters

```yaml
opennms_minion_kafka:
  "bootstrap.servers": kafka.example.org:9092

opennms_minion_kafka_sink:
  "bootstrap.servers": sink-kafka.example.org:9092   # required, even to repeat
  "group.id": HQ-Minion-Sink

opennms_minion_kafka_rpc:
  "bootstrap.servers": rpc-kafka.example.org:9092
  "group.id": HQ-Minion-RPC
```

Twin is left unset here, so it keeps using the common configuration.

### Going back to the common configuration

Remove the module's variable and re-run. The role deletes that module's `.cfg` file, so the module falls back to the common PID.

Deleting the file matters: a leftover module file still defines `bootstrap.servers`, and OpenNMS would keep selecting it in full — leaving the module pointed at a broker you thought you had removed, with the Ansible run reporting clean.

## Variables

See [`defaults/main.yml`](defaults/main.yml).

## Example

```yaml
- hosts: opennms_minion
  roles:
    - indigo423.opennms.opennms_minion
```

## License

GPL-3.0-or-later
