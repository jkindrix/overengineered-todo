# Security Policy

## Scope

> **⚠️ Do not expose this application to an untrusted network without adding
> authentication and authorization.** The REST and GraphQL APIs are intentionally
> **open and unauthenticated**, and GraphQL is **CSRF-exempt**. The production-
> hardening settings make it *deployment-shaped*, not *safe to publish*. Keep it
> loopback-only until authentication (planned as #27) is added — and when
> cookie-based auth arrives, the blanket GraphQL CSRF exemption must be revisited.

This is a deliberately over-engineered **demonstration / teaching** project — a
local to-do app. It is not intended for production use as-is (it ships with an
insecure development `SECRET_KEY` default, guarded by a boot check that refuses to
start with it when `DEBUG=False`). Please keep that context in mind.

## Supported versions

The latest release on `main` is the only supported version.

| Version | Supported |
|---------|-----------|
| latest `main` / newest tag | ✅ |
| older tags | ❌ |

## Reporting a vulnerability

Please report suspected vulnerabilities **privately** via GitHub's
[private vulnerability reporting](https://github.com/jkindrix/overengineered-todo/security/advisories/new)
(Security → Report a vulnerability). Do not open a public issue for security
problems.

We aim to acknowledge reports within a few days. Since this is a personal teaching
project, there is no formal SLA.

## Automated posture

Dependencies and code are scanned continuously: **Dependabot** (deps + Actions),
**pip-audit** and **bandit** in CI, **CodeQL**, and **dependency-review** on pull
requests. See the workflows under `.github/workflows/`.
