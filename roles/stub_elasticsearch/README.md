# stub_elasticsearch

POC / test stub that deploys a single-node Elasticsearch instance for OpenNMS flow data.

> **Not for production.** This role exists for evaluation and CI scenarios only. Use a dedicated Elasticsearch operator or cluster role for real deployments.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Variables

See [`defaults/main.yml`](defaults/main.yml).

## Example

```yaml
- hosts: elasticsearch
  roles:
    - indigo423.opennms.stub_elasticsearch
```

## License

GPL-3.0-or-later
