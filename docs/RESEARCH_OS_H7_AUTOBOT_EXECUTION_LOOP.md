# Research OS H7 — Autobot Execution Loop

## Purpose

H7 defines a bounded orchestration state machine connecting CI failure evidence to a repair attempt without granting release or approval authority.

## Flow

`CI FAIL → EVIDENCE → DIAGNOSIS → REPAIR PLAN → SAFETY GATE → REPAIR → COMMIT SHA → WAIT FOR CI → EVALUATE`

## States

`QUEUED → DIAGNOSING → REPAIR_PLANNED → REPAIRING → LOCAL_VERIFYING → SUBMITTED → WAITING_FOR_CI → CI_COMPLETED → EVALUATING → COMPLETED`

Unsafe or terminal conditions become `BLOCKED` or `FAILED`. A fresh authoritative CI result is required before completion.

## Identity

Every job is bound to an exact lowercase 40-character source SHA and bounded correlation ID. A repair must produce a different commit SHA, and subsequent CI evidence must match that new SHA and the original correlation ID.

## Safety

Retry history, failure fingerprints, event history, and payload size are bounded. Stale or mismatched CI evidence is rejected. Unknown or unsafe authority content fails closed.

## Authority boundary

Autobot may inspect, diagnose, plan, repair permitted files, create commits, and observe CI when explicitly granted. It may not approve, merge, release, install as release authority, bypass gates, rewrite evidence, escalate capabilities, or replace CI authority. This module performs no workflow dispatch, ref mutation, merge, release, install, shell/process execution, or evidence fabrication.
