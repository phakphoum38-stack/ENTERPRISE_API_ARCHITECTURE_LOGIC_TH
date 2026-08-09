# Research OS Workflow Policy

The RC2 validation path keeps only workflows that provide unique release evidence.

## Primary validation
- Research OS Agent Platform
- Research OS Developer Platform
- Research OS Build Service Host
- Research OS Branding
- Research OS Build Windows App

## Downstream validation
- Runtime Smoke
- Build Installer
- Installer Validation
- Windows Desktop verified candidate

## Consolidated checks
Performance, resilience, and V2 Completion Crew validation are consolidated into `research-os-agent-platform.yml` through the V2 quality gate and completion-crew test coverage. Separate duplicate workflows are intentionally removed to avoid duplicate/no-job noise and conflicting evidence.

Production, release, and staging workflows remain separate because they represent different deployment boundaries and are not part of this cleanup.
