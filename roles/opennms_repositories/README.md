# opennms_repositories

Adds the OpenNMS APT repository (`debian.opennms.org`) and the upstream GPG signing key on Debian/Ubuntu hosts.

Must run before any OpenNMS package install.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Repository dist

The APT source targets an explicit per-major dist, `opennms-<major>`, derived from the OpenNMS version.

`stable` is deliberately **not** used. It is an alias that floats: it resolves to `opennms-36` today, and the presence of `opennms-34`, `opennms-35` and `opennms-36` shows it has moved before. Pointing a source at it means a plain `apt upgrade` could offer a *major* version jump once `stable` follows `opennms-37`. Using the explicit dist also silences apt's `Conflicting distribution … expected stable but got opennms-NN` warning.

| Variable | Default | Purpose |
|---|---|---|
| `opennms_repo_major` | `"36"` | Major release line of the repository. |
| `opennms_repo_dist` | `opennms-{{ opennms_repo_major }}` | The dist used in the APT source line. Override for a mirror with a different layout. |
| `opennms_repo_filename` | `opennms` | Name of the sources file the role owns, without the `.list` suffix. |

## Which sources files the role owns

The role writes exactly one file, `/etc/apt/sources.list.d/opennms.list`, and expects to be the only OpenNMS source on the host.

The filename is fixed rather than derived from the source line, because a derived name embeds the dist.
Left to Ansible, changing the dist wrote a *new* file and left the previous one enabled — so a host deployed before the explicit-dist change carried `stable` alongside `opennms-36`, and every later major bump would have added one more.
A fixed name makes a dist change rewrite the entry in place.

To clear what earlier runs left behind, the role removes files matching `/etc/apt/sources.list.d/debian_opennms_org_*.list`.

That pattern is the shape Ansible derives from a `deb` line, so it selects only files this role wrote under an older dist.
A file you named yourself is left alone: if you deliberately add a second OpenNMS source — a branch build, a testing dist — give it a name of your own such as `opennms-testing.list` and the role will not touch it.

### First run on a host deployed before this change

Three one-time effects, all expected:

- The run reports `changed` for the source and the cleanup, even though the enabled dist is the same.
- The source moves from `debian_opennms_org_<dist>_main.list` to `opennms.list`. Automation keying off the old path needs updating.
- `apt-get update` stops printing `Conflicting distribution … expected stable but got opennms-NN`, because the entry that produced it is gone.

The component roles (`opennms_core`, `opennms_minion`, `opennms_sentinel`) pass `opennms_repo_major` at include time, derived from their own `opennms_version`, so bumping the OpenNMS version moves the repository with it.

The default covers consumers that reach this role without an OpenNMS version — `stub_pgsql`, which needs the repository only for `iplike`, and standalone Galaxy installs. It is a bare major rather than a full version on purpose: a full version here would be one more place the OpenNMS release is written down, and drift between a value and the thing consuming it is what this guards against.

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
