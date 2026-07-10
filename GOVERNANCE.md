# Governance

This project is a personal teaching repository with a deliberately lightweight —
but explicitly documented — governance model. (Documenting governance at all, for a
to-do app, is itself part of the point.)

## Roles

- **Maintainer** (currently [@jkindrix](https://github.com/jkindrix)): final say on
  scope, architecture, and releases. Owns everything in [CODEOWNERS](.github/CODEOWNERS).
- **Contributors**: anyone who opens an issue, discussion, or pull request.

## How decisions are made

- **Architecture decisions** are recorded as
  [ADRs](https://jkindrix.github.io/overengineered-todo/adr/). A change to the
  layering or a core pattern should come with a new ADR (proposed via the
  *ADR proposal* issue form, discussed, then accepted).
- **Everything else** is decided by the maintainer, informed by Discussions.

## Change process

1. Open an issue or discussion describing the change.
2. For nontrivial or architectural changes, propose an ADR.
3. Submit a pull request. CI must be green (lint, types, architecture contracts,
   security scans, tests, docs build).
4. The maintainer reviews and merges.

## Roadmap

Planned work lives in [docs/ROADMAP.md](docs/ROADMAP.md) and the
[project board](https://github.com/users/jkindrix/projects/2), organized into
phases with ROI tags. The roadmap is the source of truth for sequencing.

## Release process

Releases are automated by [semantic-release](.github/workflows/release.yml) from
Conventional Commits. See [CHANGELOG.md](CHANGELOG.md).
