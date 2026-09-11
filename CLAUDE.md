# CLAUDE.md

Ansible collection `indigo423.opennms`: deploys OpenNMS Horizon (Core, Minion, Sentinel) on Debian and Ubuntu, single-node or distributed. Not production-ready; the `stub_*` roles are POC only. Roles configure system-level files only, never anything the web UI or an API can set. The role catalogue is in `README.md` and `roles/<name>/README.md`; component versions live in `RELEASING.md`'s table and `roles/<role>/defaults/main.yml`.

## Commands

```bash
pip install -r requirements-dev.txt && make deps   # tooling and collections
make lint                 # ansible-lint, production profile; skipped rules in .ansible-lint
make check-credentials    # no placeholder passwords in defaults or group_vars
make check-urls           # every composed download URL in role defaults resolves
make check-render         # rendered templates match tests/render/expected/ byte for byte
make check-render-record  # re-record after an intended rendering change; read the diff
make verify               # the four checks above
ansible-playbook -i tests/render/fixtures/<name>/hosts.yml tests/check-rendered-config.yml -e fixture=<name>   # one fixture
ansible-playbook -i inventory/simple-stack.yml opennms-playbook.yml   # colocated test rig
```

CI is `.github/workflows/quality-gates.yml`, called by `ci.yml` on every PR and push to main and by `galaxy-release.yml` before publishing. It runs the four Makefile checks plus actionlint and zizmor on the workflows.

## Git

Never push to `main`; branch, PR, squash-merge. Conventional Commits, `git commit -s`, and an `Assisted-by:` trailer on AI-assisted commits (see `CONTRIBUTING.md`). Releases: `RELEASING.md`.

## Architecture in five sentences

`opennms_repositories` writes the APT source and must run before any package install; the dist derives from `opennms_version`, so source and pin cannot name different majors. `opennms_core`, `opennms_minion` and `opennms_sentinel` each include `openjdk`, `opennms_repositories`, `timesync` and `pyroscope_agent` themselves; `timesync` fails the play on clock skew unless `timesync_required: false`. Core's tasks are split by concern (`01-packages`, `10-database-setup`, `20-config`, `21-kafka`, `22-timeseries-plugin`, `50-firewall`), and its OpenNMS properties templates live under `roles/opennms_core/templates/etc/opennms.properties.d/`. Grafana comes from `indigo423.grafana` (a fork of `grafana.grafana`) with `grafana_provisioning` enabling the OpenNMS plugin afterwards; `stub_mimir` is a wrapper over that fork's `mimir` role. Every external collection is pinned in `requirements.yml` and floored in `galaxy.yml`.

## Scope rule for new roles

A role belongs here only if OpenNMS has a wire to the system it deploys: a database it queries, a broker it publishes to, a store it writes to. Systems OpenNMS is *measured against* belong in `opennms-forge/opennms-benchmark` under `deployments/roles/`.

## Endpoints versus cluster shape

Endpoints (database host, Kafka bootstrap servers, `elasticUrl`, remote_write URLs) are declared in each inventory file's own `vars:` blocks. Roles keep literal defaults (`localhost`) and look up no groups, because past the POC an endpoint is a VIP, a pooler or a DNS name that appears in no inventory. Cluster shape (Kafka quorum, Elasticsearch seeds, Mimir memberlist) is derived by the roles from group membership, because the group is definitionally the answer. `opennms_sentinel`'s Kafka list predates the split and derives from `sentinel_kafka_group`. Per-topology values never go in `inventory/group_vars/`, which all four inventories share. See issue #171.

## Gotchas an agent gets wrong

- A tag defined only inside a dynamically included file is unreachable; put the tags on the `include_tasks`/`include_role` too, or use `apply:` on `include_role` (#175, #186).
- `opennms_jvm_conf` and `opennms_env` merge over role defaults; a `PYROSCOPE_*` key restated in both aborts the run.
- `/etc/default/minion` and `/etc/default/sentinel` are parsed by systemd *and* sourced by a shell; values there are single-quoted and may not contain a single quote. Two escaping defects shipped past lint here, which is why `make check-render` exists.
- Mimir must always be told its address; on a host without a private-range interface it will not start otherwise (#158). The unit's start limit is disabled before the package installs (#159).
- Variables are scoped per role on purpose (`opennms_<role>_pinned_packages`); a shared name silently misconfigured two roles (#182). Removed names fail the run naming the replacement.
- Endpoint values in the reference inventory carry the literal alternative commented beneath them; keep that pattern when adding one.
- Every source file starts with the SPDX header (`GPL-3.0-or-later`, holder Ronny Trommer); the `source-headers` skill applies it. Jinja templates use a `{# … #}` block, which renders to nothing.
