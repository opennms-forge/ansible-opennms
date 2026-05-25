# common

Base system configuration (timezone, APT cache, common packages) for hosts running OpenNMS components.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Variables

See [`defaults/main.yml`](defaults/main.yml).

## Example

```yaml
- hosts: all
  roles:
    - indigo423.opennms.common
```

## License

GPL-3.0-or-later
