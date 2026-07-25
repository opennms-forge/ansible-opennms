# stub_victoriametrics

Benchmark **stub** role: installs a single-node VictoriaMetrics from the upstream
release tarball and runs it as a systemd service on `:8428`. Intended as an
OpenNMS time-series backend via the Prometheus `remote_write` plugin (same plugin
as Mimir; see `opennms_core`). Not a production-grade VictoriaMetrics deployment.
