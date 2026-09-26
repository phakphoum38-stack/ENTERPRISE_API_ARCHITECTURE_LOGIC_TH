# Platform source boundary

All long-lived Research OS Laravel domain/application contracts belong below this boundary. Framework-specific controllers, jobs and persistence adapters depend inward on these contracts rather than making framework classes the canonical architecture.

Required subdomains:

- Core
- Identity
- Authorization
- Workflow
- Messaging
- Tools
- Evidence
- Audit
- Operations
- Configuration
- Versioning
- Control
