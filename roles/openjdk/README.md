# openjdk

Installs and configures the OpenJDK runtime used by OpenNMS Horizon components.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Variables

See [`defaults/main.yml`](defaults/main.yml).

## Example

```yaml
- hosts: all
  roles:
    - role: indigo423.opennms.openjdk
      vars:
        openjdk_version: 21
        openjdk_pkg_version: "21*"
```

## License

GPL-3.0-or-later
