# CHANGELOG

All notable changes to this project are documented here. This file is maintained
automatically by [python-semantic-release](https://python-semantic-release.readthedocs.io/)
from [Conventional Commits](https://www.conventionalcommits.org/); do not edit it
by hand. Releases are cut by `.github/workflows/release.yml` on pushes to `main`.

<!-- version list -->

## v1.4.1 (2026-07-11)

### Bug Fixes

- **a11y**: Labels, live region, skip link, focus styles
  ([`13dc310`](https://github.com/jkindrix/overengineered-todo/commit/13dc3106e4399799d7e35b311cf3ad9f101759d1))

- **audit**: Detect trailing truncation with a head anchor
  ([`ffbb71c`](https://github.com/jkindrix/overengineered-todo/commit/ffbb71c6ac8198ab19f2842d7a62f39122e06145))

### Continuous Integration

- Make pyright a real gate (CI + pre-commit)
  ([`e522803`](https://github.com/jkindrix/overengineered-todo/commit/e522803865b3ac1fcbebf23a6797046d8c0438ef))

### Documentation

- Reconcile stale docs and sharpen the security scope
  ([`53f2333`](https://github.com/jkindrix/overengineered-todo/commit/53f2333a859eec9ddbc785e4511126172fa6d027))


## v1.4.0 (2026-07-11)

### Features

- GraphQL transport (Strawberry) over the same application service
  ([`7754335`](https://github.com/jkindrix/overengineered-todo/commit/7754335593d289aa7f734f280e10b8c55ccbdc4f))


## v1.3.0 (2026-07-11)

### Features

- CQRS read-model projection (status counts)
  ([`d9c155b`](https://github.com/jkindrix/overengineered-todo/commit/d9c155b3a6a11b954cdbcf1b45266cb6b0aa2a81))


## v1.2.0 (2026-07-10)

### Documentation

- **roadmap**: Defer #20 (outbox) to be built with #33 (webhooks)
  ([`00c014f`](https://github.com/jkindrix/overengineered-todo/commit/00c014f1eaaa6ee6764d2424a3ca360d3963d0fc))

### Features

- Event sourcing demonstration (replay, snapshots, versioning)
  ([`8f8c643`](https://github.com/jkindrix/overengineered-todo/commit/8f8c643786a04a981268b769f24e3c537562626d))

### Testing

- Formally verify the state machine with TLA+ (TLC in CI)
  ([`39cccc7`](https://github.com/jkindrix/overengineered-todo/commit/39cccc7595fcd4c9950dadf100c052c2d09fb377))


## v1.1.0 (2026-07-10)

### Chores

- **github**: Community-health files, issue forms, and process workflows
  ([`7f12b9e`](https://github.com/jkindrix/overengineered-todo/commit/7f12b9e9402bd2d87ff98d6dcd7088caa36c6d86))

### Code Style

- Format examples/fifty_lines.py (ruff)
  ([`3c3a79e`](https://github.com/jkindrix/overengineered-todo/commit/3c3a79e1368d6bbf20c33979b0e7ccf087d8fa04))

### Documentation

- Add annotated code tour + design journal
  ([`232d313`](https://github.com/jkindrix/overengineered-todo/commit/232d3137dc700e77454839e66dda996092c6e605))

- Add C4 architecture diagrams (Mermaid)
  ([`3d32f7b`](https://github.com/jkindrix/overengineered-todo/commit/3d32f7b3d8cf76f079eed857bdc38d0324b4c6a9))

- Add the '50 lines vs. this' contrast (examples + doc)
  ([`3d82a7c`](https://github.com/jkindrix/overengineered-todo/commit/3d82a7c5c3daf06d956de45f2c316dea85c2ad3a))

- MkDocs Material site with Diataxis nav, auto API reference, Pages deploy
  ([`ef403b0`](https://github.com/jkindrix/overengineered-todo/commit/ef403b0b92f55197ee1bbe08de30cf30c4504d7c))

- Tidy changelog after first automated release
  ([`ca44a03`](https://github.com/jkindrix/overengineered-todo/commit/ca44a0336edcda47907a9b241c1475714e4c4d18))

- **roadmap**: Add Phase 6 (GitHub process & governance); note quick wins + issues #39-52
  ([`8ca8a1c`](https://github.com/jkindrix/overengineered-todo/commit/8ca8a1c70c4feb47b0dd928b7acea06e58612bfb))

- **roadmap**: Mark Phase 3 4/5 complete; defer #10 (chapter branches)
  ([`123b3f8`](https://github.com/jkindrix/overengineered-todo/commit/123b3f8eff5175cac8f7076d92db1a194d9d02ff))

### Features

- Tamper-evident audit log via SHA-256 hash chain
  ([`6c281b1`](https://github.com/jkindrix/overengineered-todo/commit/6c281b1929ee798e12250f9a9c7bc2aef97c6d7d))


## v1.0.0 (2026-07-10)

- Initial Release
