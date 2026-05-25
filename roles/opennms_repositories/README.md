# opennms_repositories

Adds the OpenNMS APT repository (`debian.opennms.org`) and the upstream GPG signing key on Debian/Ubuntu hosts.

Must run before any OpenNMS package install.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Variables

See [`defaults/main.yml`](defaults/main.yml).

## Example

```yaml
- hosts: all
  roles:
    - indigo423.opennms.opennms_repositories
```

## License

GPL-3.0-or-later
