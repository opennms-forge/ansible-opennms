# Releasing

This document describes how to cut a release of `ansible-opennms`.

## Versioning

Releases follow [Semantic Versioning](https://semver.org/) with tags in the form `vMAJOR.MINOR.PATCH`.

- **MAJOR** — incompatible role or variable changes (e.g., renamed/removed defaults, removed roles, changed playbook entry points).
- **MINOR** — new roles, new opt-in features, or coordinated upstream version bumps that require user action (e.g., Horizon major version, JDK major version).
- **PATCH** — bug fixes and upstream version pins that don't change the user-facing contract.

While the project is `v0.x`, breaking changes may land in MINOR bumps; flag them clearly in the release notes under an `### Breaking Changes` heading.

## Where component versions live

When preparing a release, check these files for any version drift that should be reflected in the release notes:

| Component | File |
|-----------|------|
| OpenNMS Horizon | `roles/opennms_core/defaults/main.yml`, `roles/opennms_minion/defaults/main.yml`, `roles/opennms_sentinel/defaults/main.yml` (`opennms_version`) |
| OpenJDK | `roles/openjdk/defaults/main.yml` (`openjdk_version`) and per-role overrides in `roles/opennms_*/tasks/main.yml` |
| PostgreSQL | `roles/opennms_core/defaults/main.yml` (`pg_version`) |
| Kafka | `roles/stub_kafka/defaults/main.yml` |
| Elasticsearch | `roles/stub_elasticsearch/defaults/main.yml` |
| Grafana | `group_vars/grafana/vars.yml` (`grafana_version`) |
| Grafana Mimir | `roles/stub_mimir/defaults/main.yml` |
| Prometheus JMX Exporter | `roles/opennms_core/defaults/main.yml` (`prom_jmx_exporter_version`) |
| External collections | `requirements.yml` |

The Component Versions table in `CLAUDE.md` should also be in sync.

## Cutting a release

Releases are created from `main` after all intended changes have merged. The repository's branch protection forbids pushing to `main` directly — every change must arrive via a reviewed pull request.

1. **Confirm `main` is at the intended commit.**

   ```bash
   git checkout main
   git pull --ff-only
   gh pr list --state merged --base main -L 10   # sanity-check what's in
   ```

2. **Review commits since the previous tag.** Conventional Commit prefixes drive the release-note grouping.

   ```bash
   git log --oneline --no-merges $(git describe --tags --abbrev=0)..HEAD
   ```

3. **Decide the version bump** (MAJOR / MINOR / PATCH) using the rules above.

4. **Create the GitHub release.** This both creates the tag at `main`'s HEAD and publishes the release notes. Use the template in the next section.

   ```bash
   gh release create vX.Y.Z \
     --target main \
     --title "vX.Y.Z — <headline>" \
     --notes "$(cat release-notes.md)"
   ```

   Pass `--draft` first if you want to review on github.com before publishing.

5. **Verify** the tag appears in `git tag --sort=-creatordate | head` and the release page renders correctly.

## Release notes template

Match the structure used by `v0.2.0` and `v0.3.0`. Group changes by Conventional Commit type, omitting empty sections.

```markdown
## Overview

<One-paragraph headline: the most important user-visible change in this release.>

---

## Changes since vPREV

### Breaking Changes
- **`role-name`**: <description> (#PR).

### Features
- **`role-name`**: <description> (#PR).

### Fixes
- **`role-name`**: <description> (#PR).

### Chores
- <description>.

---

## Component Versions

| Component | Version |
|-----------|---------|
| OpenNMS Horizon | X.Y.Z |
| PostgreSQL | X |
| Apache Kafka (KRaft) | X.Y.Z |
| OpenJDK | X |
| Grafana | X.Y.Z |
| Elasticsearch | X.Y.Z |
| Grafana Mimir | X.Y.Z |
| Prometheus JMX Exporter | X.Y.Z |

---

## Upgrading from vPREV

<Concrete steps. If a re-run of the playbook is sufficient, say so. If there are manual cleanup steps (e.g., dpkg recovery, config migration), list the exact commands.>

```bash
ansible-playbook -i inventory/opennms-stack.yml opennms-playbook.yml
```

**Full changelog:** https://github.com/opennms-forge/ansible-opennms/compare/vPREV...vX.Y.Z
```

## Ansible Galaxy publishing

The collection is published to Ansible Galaxy as **`indigo423.opennms`**. Publication happens automatically when a GitHub release is published, via `.github/workflows/galaxy-release.yml`.

### One-time prerequisites

1. **Namespace ownership.** The `indigo423` namespace on https://galaxy.ansible.com must be owned (or co-owned) by the account that generates the API token. New collaborators are added via the *Namespaces* page on galaxy.ansible.com.
2. **API token.** Generate a token at https://galaxy.ansible.com/me/preferences (Preferences → API Key) and store it as the `ANSIBLE_GALAXY_API_KEY` secret under *Settings → Secrets and variables → Actions* for the repo. The token belongs to the user; if it rotates, update the secret.

### Per-release: bump `galaxy.yml` and update `CHANGELOG.md`

Before tagging a release, two files must be updated in the same PR that bumps role defaults and `CLAUDE.md`'s Component Versions table:

1. **`galaxy.yml`** — set `version:` to match the intended tag (without the `v` prefix):

   ```yaml
   # galaxy.yml
   version: 0.4.0   # matches the upcoming v0.4.0 tag
   ```

   The release workflow verifies `galaxy.yml`'s `version` equals `<release-tag>` minus the `v` and fails the build otherwise — this guard catches forgotten bumps before the artifact ships.

2. **`CHANGELOG.md`** — add a new `## [X.Y.Z] - YYYY-MM-DD` section at the top with short entries grouped by [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) categories (`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`). Update the link-reference list at the bottom. The file is required by the `galaxy[no-changelog]` ansible-lint rule and is shipped inside the published artifact.

### Release flow with Galaxy

1. Open a PR with all role-default bumps, the `CLAUDE.md` Component Versions update, **and** the `galaxy.yml` version bump.
2. Merge to `main`.
3. Create the GitHub release at `main` HEAD (see *Cutting a release* above). The `galaxy-release` workflow fires on the `release: published` event, runs the version-match check, builds the collection (`ansible-galaxy collection build`), and publishes the artifact to Galaxy.
4. Verify the new version appears at https://galaxy.ansible.com/ui/repo/published/indigo423/opennms/ within a couple of minutes.

### Republishing or recovering a failed run

- **CI failed mid-publish (or before the release existed):** edit the GitHub release and click *Publish release* again — this re-fires `release: published` and re-runs the workflow.
- **Manual fallback** (e.g., to backfill a tag from before this workflow existed):

  ```bash
  ansible-galaxy collection build --output-path dist/
  ansible-galaxy collection publish \
    --token "${ANSIBLE_GALAXY_API_KEY}" \
    dist/indigo423-opennms-*.tar.gz
  ```

  Run from a clean checkout of the exact tag you want to ship.

### What gets published

`ansible-galaxy collection build` reads `galaxy.yml` and respects the `build_ignore` list there. The published artifact intentionally excludes:

- `inventory/` — deployment harness, not consumable by collection users.
- `CLAUDE.md`, `RELEASING.md` — project-internal docs.

The repo's root-level playbooks (`opennms-playbook.yml`, `site.yml`, `hzn-*-deployment.yml`) are currently included as-is. If the collection should expose playbooks via FQCN (e.g., `indigo423.opennms.opennms`), they need to be moved into a `playbooks/` directory in a future PR — this is intentionally out of scope for the initial Galaxy enablement.
