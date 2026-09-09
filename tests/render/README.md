# Rendered-configuration fixtures

`make check-render` renders role templates against the inventories here and compares the result to the recorded expectations. No hosts, no services, no privileges, no network.

## Why this exists

`ansible-lint` validates YAML shape, not the content a template produces. Two defects shipped past it in one afternoon:

- Values written **unquoted** into `/etc/default/{minion,sentinel}` — a file systemd parses *and* `container.init` sources as shell. A JSON value broke both consumers.
- The fix for that emitted **doubled backslashes**, because `'\\'` inside a YAML-embedded Jinja expression does not mean what it means inside a `.j2` file.

Both were string-level mistakes in generated configuration. Both were found by rendering the template and reading the output, which is what this automates.

A rendered file is decidable without a network. Whether the address in it accepts a connection is not — that belongs to a smoke bed. Note the bed cannot replace this check: a bed whose DNS resolves the inventory's own hostnames makes a wrong address work, so it would pass on configuration this check rejects.

## Layout

```
tests/
  check-rendered-config.yml        the play: loads vars, renders, compares
  check-rendered-config-file.yml   per-file render and comparison
  render/
    fixtures/<name>/
      hosts.yml   inventory — groups the role's derivations read, plus a
                  `render_target` group naming the host to render as
      meta.yml    which role, which templates (loaded before role defaults,
                  because the paths are built from it)
      vars.yml    role variable overrides, plus `render_canary: fixture`
    expected/<name>/<file>         recorded output, compared byte for byte
```

## Fixtures

| Fixture | Renders | Pins |
|---|---|---|
| `colocated` | `opennms_core` → `opennms.conf` | quoting and backslash escaping; that `opennms_jvm_conf` merges over its defaults rather than replacing them |
| `minion-pyroscope` | `opennms_minion` → `pyroscope-env` | the stanza both defects shipped in: single quoting that survives systemd *and* a sourcing shell |
| `distributed` | `opennms_sentinel` → Kafka sink cfg, `pyroscope-env` | the one existing inventory-derived address — three brokers joined, sorted despite being declared out of order — and Sentinel's copy of the Pyroscope stanza |
| `kafka-single` | `stub_kafka` → `server.properties` | that a single-member group still renders the pre-clustering single-node form |
| `kafka-cluster` | `stub_kafka` → `server.properties` | the cluster form: sorted quorum voters with stable node ids, replication 3, min.isr 2 |

The last two are a pair on purpose. Either alone would pass while the shape logic was broken; the difference between them is the assertion.

The two `pyroscope-env` fixtures are a pair for a different reason: the Minion and Sentinel roles render the same stanza from two template files, so they are given the **same** values deliberately. The expectations should differ only in the jar path and the application name, and anything else diverging is a defect.

Those values are chosen to break a naive rendering — JSON, a `$` a sourcing shell would expand, an embedded double quote, a `#` that would start a comment, and a bare space. The recorded output round-trips through `sh -c '. ./file'` unchanged, which is the property the quoting exists for.

## Adding a fixture

1. `tests/render/fixtures/<name>/hosts.yml` — declare the groups the role reads. **Check the role's actual group variable**: `stub_kafka` reads `kafka_cluster_group`, which defaults to `message_broker`, not `kafka`. A fixture naming a group nothing reads renders the fallback shape and passes having tested nothing — that mistake was made while writing these.
2. `meta.yml` — `render_role` and `render_files`.
3. `vars.yml` — overrides, including `render_canary: fixture`.
4. `mkdir tests/render/expected/<name>` and run `make check-render-record`.
5. **Read the recorded output before committing it.** An expectation is only as good as the review it got; recording a defect converts this check from a net into a ratchet.

## Re-recording after an intended change

```console
$ make check-render-record
```

Separate target on purpose. An expectation that updated itself would make the check self-confirming, so re-recording is something a person chooses and a reviewer sees in the diff.

## Two notes on the mechanism

**Variable precedence is load-bearing.** Ansible ranks `include_vars` above task vars and far above inventory vars, so a fixture supplying overrides through its inventory would be silently overruled by the role defaults. The play loads `meta.yml`, then role `defaults/`, then role `vars/`, then the fixture's `vars.yml` — later `include_vars` wins. The `render_canary` assertion measures that rather than trusting it: without it, a precedence change in a future Ansible release would leave the check passing while rendering role defaults for every fixture.

**Nothing is connected to.** The play targets each fixture's `render_target` group with `connection: local` and `gather_facts: false`, so `inventory_hostname` and `groups` are the fixture's own while no SSH is attempted. Templates needing facts cannot be covered this way; none of the current fixtures do.
