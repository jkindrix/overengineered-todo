# Architecture Decision Records (ADRs)

An ADR captures a single significant decision: its **context**, the **decision**,
the **consequences** (good and bad), and the **alternatives** we rejected. They are
the durable record of *why* the codebase is shaped as it is. Read them when you
ask "why is this like this?" or before changing something an ADR covers.

ADRs are immutable once accepted. To change a decision, add a new ADR that
**supersedes** the old one (and update the old one's status), rather than editing
history.

## Format

Each record follows the structure in [`_template.md`](_template.md): Status,
Context, Decision, Consequences, Alternatives considered, Related.

## Index

| # | Decision | Status |
|---|----------|--------|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-layered-hexagonal-architecture.md) | Adopt a layered / hexagonal architecture | Accepted |
| [0003](0003-value-objects.md) | Model identity and enumerations as value objects | Accepted |
| [0004](0004-rich-aggregate-and-state-machine.md) | Rich aggregate emitting events + centralized state machine | Accepted |
| [0005](0005-event-bus.md) | Dispatch domain events via a synchronous in-memory bus | Accepted |
| [0006](0006-event-log-and-transactional-gap.md) | Persist an append-only domain-event log | Accepted (gap resolved by 0013) |
| [0007](0007-application-service-cqrs.md) | Orchestrate use cases with a service + CQRS-lite DTOs | Accepted |
| [0008](0008-ports-repositories-mappers.md) | Abstract persistence behind ports + mapper repositories | Accepted |
| [0009](0009-di-container.md) | Wire the object graph in a DI container | Accepted |
| [0010](0010-interface-adapters.md) | Adapt transports in the interface layer | Accepted |
| [0011](0011-infrastructure-sqlite-config.md) | SQLite, model location, and env-driven config | Accepted |
| [0012](0012-testing-strategy.md) | Test in three tiers matching the layers | Accepted |
| [0013](0013-transactional-unit-of-work-event-store.md) | Atomic state + events via a Unit of Work and Event Store | Accepted |
| [0014](0014-tamper-evident-audit-log.md) | Tamper-evident audit log via a hash chain | Accepted |
| [0015](0015-formal-spec-tla-plus.md) | Formally verify the state machine with TLA+ | Accepted |
| [0016](0016-event-sourcing.md) | Demonstrate event sourcing (replay, snapshots, versioning) | Accepted |
| [0017](0017-cqrs-read-model.md) | A CQRS read-model projection (status counts) | Accepted |

## Conventions

- Filenames: `NNNN-kebab-case-title.md`, zero-padded, monotonically increasing.
- New ADRs start at status **Proposed**, move to **Accepted** when adopted, and to
  **Superseded by ADR-XXXX** or **Deprecated** when they no longer hold.
