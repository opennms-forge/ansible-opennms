# Contributing

Thanks for considering a contribution. This document covers the two things that will block a pull request if you miss them — the sign-off and the AI-assistance trailer — plus the local checks that mirror CI.

## Before you open a pull request

Work starts from an issue. Open one describing the problem or the change, then reference it from the pull request with a closing keyword (`Closes #123`) so it resolves on merge.

`main` is protected: every change arrives via a reviewed pull request. Branch from `main` using a `<type>/<short-description>` name:

```bash
git checkout -b fix/minion-sink-topics
```

## Sign-off is required

Every commit must carry a Developer Certificate of Origin sign-off, created with `git commit -s`:

```
Signed-off-by: Your Name <your@email.example>
```

This certifies the [DCO](https://developercertificate.org/) — that you wrote the change or otherwise have the right to submit it under the project's license. It must be a **human identity**, never an agent or tool name. Use `git commit -s --amend` if you forget.

## AI-assisted contributions

AI assistance is welcome, and it must be disclosed. A commit produced with an AI agent's help carries an `Assisted-by` trailer naming the agent and model:

```
Assisted-by: ClaudeCode:claude-opus-5
Signed-off-by: Your Name <your@email.example>
```

The two trailers go in that order, at the end of the commit message.

The `Signed-off-by` human remains fully responsible for the change: for reviewing it, for its correctness, and for its license compliance. Disclosing AI assistance does not transfer any of that. A pull request whose author cannot explain what the code does will not be merged, regardless of how it was produced.

## Commit messages

[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/): `<type>[optional scope]: <description>`.

Types in use: `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `chore`, `ci`, `build`, `revert`. Breaking changes append `!` after the type or add a `BREAKING CHANGE:` footer — these drive the release notes, so they matter.

```
fix(opennms_core): compose download URLs that upstream actually serves
```

## Running the checks locally

CI runs the same targets, so a green local run is a good predictor.

```bash
make deps         # install the collections in requirements.yml
make lint         # ansible-lint, production profile
make check-urls   # resolve every download URL in role defaults
make verify       # both of the above
```

`make check-urls` makes outbound HTTPS requests and needs network access. It exists because `ansible-lint` validates YAML shape and cannot tell you that a download URL 404s — which is how several releases shipped broken.

Both `ansible-lint` and `download-urls` are required checks on `main`.

## Scope: what belongs in this collection

A role belongs here only if OpenNMS has a wire to the system it deploys — a database it queries, a broker it publishes to, a store it writes to. Systems OpenNMS is *measured against* belong in the benchmark repository instead.

Roles configure system-level files only. Anything settable through the OpenNMS web UI or its REST APIs is out of scope by design.

The `stub_*` roles are POC and testing scaffolding, not production deployments. Keep them simple; they are not the place for hardening work that belongs in a real operator or cluster role.

## Adding or changing a role

- Role defaults live in `roles/<role>/defaults/main.yml`. Give every variable a role-name prefix.
- A download URL belongs in `defaults`, not inline in a task, so `make check-urls` covers it.
- Version variables hold a **bare** version; the URL template supplies whatever tag prefix upstream uses. If Renovate manages the variable, its `# renovate:` annotation needs `extractVersion` so the bot cannot write a prefix the template also adds.
- Repository signing keys are verified by fingerprint before the keyring is installed. Never install a key without checking it, and never pin the key file's SHA-256 as the primary control — see any of the three repository roles for the pattern.
- Update `CHANGELOG.md` and the role's `README.md` in the same pull request as the change.

## Releases

Maintainers only. The procedure is in [RELEASING.md](RELEASING.md).

## Security

Do not open a public issue for a vulnerability. See [SECURITY.md](SECURITY.md).
