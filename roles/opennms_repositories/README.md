# opennms_repositories

Adds the OpenNMS APT repository (`debian.opennms.org`) and the upstream GPG signing key on Debian/Ubuntu hosts.

Must run before any OpenNMS package install.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Key verification

The role verifies the **fingerprint** of the downloaded signing key, not the SHA-256 of the key file.

A fingerprint is a hash over the public key packet, so it *is* the key's identity.
It survives re-exports, re-armoring, added third-party signatures and repository host migrations.
A file hash survives none of those, so pinning it produces hard failures on harmless events while never establishing which key was actually trusted.

The rule this collection follows: **hash immutable artifacts, fingerprint keys.**
A released jar at a versioned URL (`prom_jmx_exporter_sha256` in `opennms_core`) is immutable, so its file hash is its identity and stays pinned.
A key file served from a live host is a re-exportable representation of a stable object, so the fingerprint is pinned instead.

Verification runs *after* the key is converted to GPG format and *before* it is copied into `/usr/share/keyrings/`, so a key that fails the check never reaches a trusted location.

### Provenance of the pinned fingerprint

`701E145FE26283F8C073BAAE697677243260D071`

| Property | Value |
|---|---|
| User ID | `OpenNMS Signing Key 2023 <opennms@opennms.org>` |
| Algorithm | RSA-4096 |
| Created | 2023-01-05 |
| Subkey | `9FD8186993E15F6EC368220001B0CCF2D404F881` |

Corroborated by two sources independent of the key file itself:

- `keys.openpgp.org` returns a key under this fingerprint with the same creation timestamp and the same subkey.
- The repository's own `dists/stable/Release.gpg` is signed by this fingerprint, so it is demonstrably the key that signs the packages.

Change the pinned value only against comparable evidence.

## Variables

See [`defaults/main.yml`](defaults/main.yml).

| Variable | Default | Purpose |
|---|---|---|
| `opennms_key_url` | `https://debian.opennms.org/OPENNMS-GPG-KEY` | Where the signing key is fetched from. |
| `opennms_key_fingerprints` | `["701E145F…3260D071"]` | Accepted primary-key fingerprints. Authoritative trust control. |
| `opennms_key_sha256` | `null` | Optional file-hash pin. Off by default; set it to opt into a second, stricter gate. |
| `opennms_key_ring_file` | `/usr/share/keyrings/opennms-stable-archive-keyring.gpg` | Where the verified keyring is installed. |
| `opennms_repo_url` | `https://debian.opennms.org` | APT repository base URL. |

Fingerprints are compared case-insensitively with spaces stripped, so a value pasted from `gpg` output in spaced display format also matches.

### Handling a key rollover

`opennms_key_fingerprints` is a list so that a rollover is an append, not a swap.
Verify the new fingerprint out-of-band first, then carry both through the transition:

```yaml
opennms_key_fingerprints:
  - "701E145FE26283F8C073BAAE697677243260D071"  # OpenNMS Signing Key 2023
  - "<new fingerprint>"                          # successor key
```

Drop the retired entry once every host has been converged.

## Example

```yaml
- hosts: all
  roles:
    - indigo423.opennms.opennms_repositories
```

## License

GPL-3.0-or-later
