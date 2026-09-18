# Phase 1 — Persistent Learned Skill Registry

## Purpose

Provide durable JSON persistence for approved Learned Skills while keeping the existing in-memory LearnedSkillRegistry and Core Skill registry separate.

## Contract

- Persistence format version is explicit (1).
- Only approved learned-skill records may be loaded.
- Missing persistence files are treated as an empty learned-skill set.
- Existing registry contents must not conflict with persisted records.
- Writes use a temporary file, fsync, and atomic os.replace.
- JSON serialization is deterministic.
- No credentials, Core Skill mutation, execution authority, merge authority, or workflow dispatch is introduced.

## Scope

This component is a persistence adapter, not a new execution engine or scheduler. It layers storage over the existing LearnedSkillRegistry.

## Verification

The companion test covers save/load round trip, deterministic repeated writes, empty missing-file behavior, and fail-closed rejection of non-approved persisted records.

The implementation is host-path agnostic so the runtime can supply a platform-appropriate location later.
