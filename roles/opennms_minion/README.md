# opennms_minion

Deploys and configures the OpenNMS Minion agent for monitoring isolated network segments.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Package version pinning

This role writes an APT preferences file pinning the OpenNMS packages it installs to `opennms_version`.

**A routine `apt upgrade` will not move OpenNMS.** That is deliberate: OpenNMS upgrades need a planned maintenance window, and an unplanned jump — potentially across a major release — is exactly what this prevents.

To upgrade deliberately, change `opennms_version` and re-run the role. The pin is rewritten before the packages are installed, so the new version is permitted in the same run; there is no separate unpin step.

| Variable | Purpose |
|---|---|
| `opennms_pinned_packages` | The OpenNMS packages covered by the pin. |
| `opennms_apt_preferences_file` | Where the preferences file is written. |

`rrdtool`, `jrrd2` and `iplike` are deliberately **not** pinned. They are ordinary system packages, and blocking their security updates to protect something that is not OpenNMS would be the wrong trade.

The APT source also targets an explicit per-major dist (`opennms-36`) rather than the floating `stable` alias, so a major-version jump cannot happen even if the pin is removed. See [`opennms_repositories`](../opennms_repositories/README.md).

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
