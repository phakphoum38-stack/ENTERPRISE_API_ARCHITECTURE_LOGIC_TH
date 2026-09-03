# Research OS Canonical Release Path

## Purpose

This document defines the release authority for the Research OS Owner Special Windows product. It prevents historically accumulated workflows from becoming competing release authorities.

## Canonical path

```text
MAIN
  -> canonical commit SHA
  -> Research OS + Friend from the exact same SHA
  -> canonical Owner/Friend integration build
  -> Owner identity gate
  -> Friend ServiceHost/runtime startup
  -> Owner installer build
  -> install / upgrade / uninstall E2E
  -> packaged Owner identity gate
  -> validated Complete ZIP + validated Setup.exe
  -> release manifest + SHA256 evidence
  -> final release
```

Every release-facing artifact must be traceable to one canonical source SHA.

## Authorities

### 1. `owner-special-friend.yml`

**Role: canonical Owner release control pipeline.**

This is the primary end-to-end Windows Owner Special pipeline. It owns the dependency chain:

`Friend validation -> Owner Desktop -> Installer Build -> Installer Validation -> Owner Bundle`

The pipeline must remain the primary authority for validated Owner Windows release outputs.

### 2. `research-os-windows-artifact.yml`

**Role: Research OS + Friend Windows integration/package producer.**

Friend source must resolve from the exact canonical GitHub SHA. It must not pin an unrelated historical Friend commit for a release artifact.

Its Complete ZIP is an input to downstream validation only when its source SHA matches the release source SHA.

### 3. `research-os-release-integration.yml`

**Role: downstream integration/packaging validator.**

It may consume the exact Complete ZIP and build/validate the Owner installer, but it must not silently substitute a different source lineage.

### 4. `release.yml`

**Role: release/publishing stage for validated candidate results.**

It is not a competing build authority. It should publish only artifacts that already passed the applicable build, identity, E2E, and evidence gates.

## Non-authoritative workflows

Other workflows may remain for specialized validation, V3 candidate generation, iOS artifacts, evidence collection, smoke tests, or development CI. Their green status does not by itself authorize a Windows Owner release.

A workflow becomes release-authoritative only when it is explicitly connected to the canonical source SHA and the required downstream gates.

## Fail-closed rules

1. No release artifact from a mismatched Research OS/Friend SHA.
2. No Setup.exe release before install/upgrade/uninstall E2E passes.
3. No packaged Owner executable release before the final identity gate passes.
4. No Complete ZIP is considered final merely because it was successfully built.
5. No secondary workflow may override the canonical release authority.
6. New release-facing workflows require a re-audit of this path and the workflow registry.

## Historical tooling policy

The repository contains tooling accumulated across multiple versions. Do not delete historical workflows merely because they are not part of the canonical path.

Classify each workflow as one of:

- `CANONICAL` — owns a release-stage decision/output.
- `VALIDATION` — supplies evidence to a canonical stage.
- `SPECIALIZED` — serves a target such as iOS or V3 candidate builds.
- `TRIGGER` — starts another workflow but does not own release output.
- `LEGACY` — retained for compatibility/history and not release-authoritative.

Deletion requires dependency verification and evidence that no active path consumes the workflow or its artifacts.

## Current baseline

The canonical source-lineage gate is enforced by PR #219. The release path must continue to use the same SHA through Research OS, Friend, integration packaging, identity validation, and final evidence.
