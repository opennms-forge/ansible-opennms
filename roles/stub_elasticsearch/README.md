# stub_elasticsearch

POC / test stub that deploys a single-node Elasticsearch instance for OpenNMS flow data.

> **Not for production.** This role exists for evaluation and CI scenarios only. Use a dedicated Elasticsearch operator or cluster role for real deployments.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Key verification

The role verifies the **fingerprint** of the downloaded signing key, not the SHA-256 of the key file, matching `opennms_repositories` and `stub_pgsql`.

A fingerprint is a hash over the public key packet, so it *is* the key's identity, and it survives re-exports, re-armoring and repository host migrations. A file hash survives none of those, so pinning it produces hard failures on harmless events while never establishing which key was actually trusted.

Verification runs after the key is converted to GPG format and before it is copied into `/usr/share/keyrings/`, so a key that fails the check never reaches a trusted location.

### Provenance of the pinned fingerprint

`46095ACC8548582C1A2699A9D27D666CD88E42B4`

| Property | Value |
|---|---|
| User ID | `Elasticsearch (Elasticsearch Signing Key) <dev_ops@elasticsearch.org>` |
| Algorithm | RSA-2048 |
| Created | 2013-09-16 |
| Subkey | `3B0C6695387682E18F77B489AB6B7FCB60D31954` |

Corroborated by two sources independent of the key file itself:

- `keys.openpgp.org` returns a key under this fingerprint with the same creation timestamp and the same subkey.
- The repository's own `packages/8.x/apt/dists/stable/Release.gpg` is signed by this fingerprint, so it is demonstrably the key that signs the packages.

Change the pinned value only against comparable evidence.

Note that this key is RSA-2048 and dates from 2013, appreciably older than the OpenNMS signing key. A rotation is correspondingly more plausible, which is why the accepted value is a list rather than a single fingerprint.

## Variables

See [`defaults/main.yml`](defaults/main.yml).

| Variable | Default | Purpose |
|---|---|---|
| `es_key_url` | `https://artifacts.elastic.co/GPG-KEY-elasticsearch` | Where the signing key is fetched from. |
| `es_key_fingerprints` | `["46095ACC…D88E42B4"]` | Accepted primary-key fingerprints. Authoritative trust control. |
| `es_key_sha256` | `null` | Optional file-hash pin. Off by default; set it to opt into a second, stricter gate. |
| `es_key_ring_file` | `/usr/share/keyrings/elasticsearch-keyring.gpg` | Where the verified keyring is installed. |
| `es_repo_url` | `https://artifacts.elastic.co/packages/8.x/apt` | APT repository base URL. |

Fingerprints are compared case-insensitively with spaces stripped, so a value pasted from `gpg` output in spaced display format also matches.

### Handling a key rotation

`es_key_fingerprints` is a list so that a rotation is an append, not a swap. Verify the new fingerprint out-of-band first, then carry both through the transition:

```yaml
es_key_fingerprints:
  - "46095ACC8548582C1A2699A9D27D666CD88E42B4"  # Elasticsearch Signing Key (2013)
  - "<new fingerprint>"                          # successor key
```

Drop the retired entry once every host has been converged.

## Example

```yaml
- hosts: elasticsearch
  roles:
    - indigo423.opennms.stub_elasticsearch
```

## License

GPL-3.0-or-later
