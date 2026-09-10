# opennms_repositories

Adds the OpenNMS APT repository (`debian.opennms.org`) and the upstream GPG signing key on Debian/Ubuntu hosts.

Must run before any OpenNMS package install.

Part of the [`indigo423.opennms`](https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/) collection.

## Repository dist

The APT source targets an explicit per-major dist, `opennms-<major>`, derived from the OpenNMS version.

`stable` is deliberately **not** used. It is an alias that floats: it resolves to `opennms-36` today, and the presence of `opennms-34`, `opennms-35` and `opennms-36` shows it has moved before. Pointing a source at it means a plain `apt upgrade` could offer a *major* version jump once `stable` follows `opennms-37`. Using the explicit dist also silences apt's `Conflicting distribution … expected stable but got opennms-NN` warning.

| Variable | Default | Purpose |
|---|---|---|
| `opennms_repo_fallback_version` | `36.0.4` | OpenNMS release used only when the caller defines no `opennms_version`. |
| `opennms_repo_dist` | derived from `opennms_version` | The dist used in the APT source line. Override for a mirror with a different layout. |
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

## One host, one OpenNMS major

A host carries one OpenNMS major, and the role enforces it: if a second role in the same run asks for a different one, the run fails naming both roles and both majors.

Nothing else stops you. `opennms-minion` and `opennms-sentinel` declare no dependency on any OpenNMS package, so apt would carry a Core at one major beside a Minion at another quite happily. What breaks is this file: all three roles write `/etc/apt/sources.list.d/opennms.list`, so the last one to run would decide the major for the whole host and the others' version pins would stop matching anything fetchable.

If you hit the failure, set one `opennms_version` for the host, or give the two components hosts of their own.

Set it for the *host*, not for one component's group. On a colocated host `stub_pgsql` runs first and carries no version of its own, so it resolves the fallback: if that differs from what the component roles want, the two rewrite the sources file past each other on every run. Both dists carry `iplike`, so nothing breaks, but the run never settles. With the shipped defaults they agree, and a stack-level `opennms_version` makes them agree at any version you choose.

The check compares against a fact recorded during the run rather than the file on disk, which is what makes a deliberate major upgrade need no exemption: the first role of a run establishes the major whatever the host previously carried. Facts are per host, so a topology that runs each component on its own host never compares anything.

## Where the dist comes from

`opennms_repo_dist` is derived from the **caller's** `opennms_version`, so the source line and the version pin resolve from one fact and cannot name different majors. Bumping the OpenNMS version moves the repository with it, with nothing else to edit.

No caller passes the version in. `opennms_version` is already in scope when a component role includes this one, and it stays in scope through a nested include — which matters, because `opennms_icmp` includes this role again on its own account to install `jicmp` and `jicmp6`.

`opennms_repo_fallback_version` covers consumers that reach this role without a version: `stub_pgsql` on a database host that runs no component role, `opennms_icmp` installed standalone, and direct consumers. Two things about it are deliberate:

- It is a **full version carrying a `# renovate:` annotation**, not a bare major. Renovate updates every annotated occurrence of the OpenNMS release together, so this cannot drift from the component roles. Its unannotated predecessor did exactly that: it stayed at `36` while the roles moved, and the dist stopped matching the pin.
- It has a **name of its own** rather than being another `opennms_version`. A second default under that name would leave which value wins to role load order, and a caller cannot pass its own value through under the same name — `opennms_version: "{{ opennms_version }}"` is a recursive definition and raises `recursive loop detected in template`.

Setting `opennms_version` once for the whole stack therefore reaches every role that needs it, including the database host's `iplike`.

Only the latest Horizon release is supported upstream, so in practice every deployment follows the release Renovate bumps to. That is what makes the derivation matter: the source and the pin move together on a major bump, with nothing left behind to be updated by hand.

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
