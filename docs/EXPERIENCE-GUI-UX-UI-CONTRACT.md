# Experience GUI / UX / UI Contract

**Plane:** EXPERIENCE  
**Baseline:** `5e16741bb42f6f888542d74b37781e723a7d6643`

## Purpose

This contract isolates human-facing product work from Core and Platform implementation. Every experience change must resolve an explicit target identity before implementation.

## Target identity

```
Product
  -> Surface
    -> Screen
      -> Component
        -> Implementation Target
```

Missing, ambiguous, or unknown target identity is **HOLD**. The system must not guess which UI is intended.

## Workflow ownership

GUI, UX, UI, Design System, Visual Regression, Accessibility, and Experience Release are distinct workflow responsibilities. They may share existing assurance infrastructure but do not create a second assurance engine.

## Evidence lifecycle

```
Requirement / Design
       ↓
Experience Identity
       ↓
Implementation
       ↓
Functional Verification
       ↓
Visual Verification
       ↓
Accessibility Verification
       ↓
Evidence / Provenance
       ↓
Existing Assurance Plane
```

Visual evidence and test evidence support assurance; neither grants authority.

## State presentation

The UI must preserve semantic state: UNKNOWN cannot render as success, failed state cannot render as success, stale state must be visible, and authority state must be distinguishable from evidence state.

## Authority boundary

Experience work cannot mutate runtime authority, grant permissions, approve reviews, merge, enable auto-merge, or rewrite history. Owner and Merge authority remain unchanged.

## 10^1000

`10^1000` is logical coverage only. It is never materialized as UI instances, workflows, jobs, rows, or execution units. Actual UI testing remains bounded and representative.

## Non-goals

No duplicate runtime, platform, assurance, or autonomous merge system.
