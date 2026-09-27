# Laravel Platform Module Map V1

## Layering

### Interface
HTTP routes/controllers, request validation, API resources and context middleware.

### Application
Commands, queries, orchestration services and transaction boundaries.

### Domain/contract
Platform identifiers, capability/policy references, workflow contracts, event/command contracts and evidence/audit contracts.

### Infrastructure
Existing Research OS adapters, queue/event transport, persistence, telemetry and external tool adapters.

## Dependency rule

Interface -> Application -> Contracts/Domain -> Infrastructure.

Infrastructure is not a new source of security authority. Controllers do not contain workflow business logic. Queue workers do not make authorization decisions independently.

## Namespaces

ResearchOS\\Platform\\Core
ResearchOS\\Platform\\Identity
ResearchOS\\Platform\\Authorization
ResearchOS\\Platform\\Workflow
ResearchOS\\Platform\\Messaging
ResearchOS\\Platform\\Tools
ResearchOS\\Platform\\Evidence
ResearchOS\\Platform\\Audit
ResearchOS\\Platform\\Operations
ResearchOS\\Platform\\Configuration
ResearchOS\\Platform\\Versioning
ResearchOS\\Platform\\Control
