# Changelog

## v3.2.0

- Marked the active Workflow Runtime contract set as the current development version.
- Preserved `v1.0.0-draft` as a historical snapshot.
- Recorded V3 runtime and Research OS API validation status: 130 V3 tests and 114 API tests passed.
- Updated the validation snapshot after runtime hardening to 144 V3 tests passing with 1 skipped.
- Declared the implemented Google, cloud conversation, memory, and GitHub dashboard routes in the draft OpenAPI contract.
- Added OpenAPI security schemes for Research OS sessions and the server-side sync key.
- Added a canonical tool registry with ownership, boundaries, evidence and lifecycle state.
- Added a GitHub Actions deduplication matrix identifying canonical release gates and specialized evidence workflows.
- Recorded V1/V2 ownership, migration boundaries and retirement criteria in the compatibility map.
- Added the provider-neutral V3 service API contract draft for health, master, providers and user scope boundaries.
- Recorded durable runtime gaps for event persistence and queue-to-engine state projection.
- Added observability coverage for structured events, correlation IDs, redaction and production telemetry gaps.
- Recorded source-level release artifact and installer alignment, including the intentional architecture/application version distinction.
- Added a delete/retire candidate list with evidence requirements; no deletion is approved by the audit.
- Recorded CI evidence status for `a06f0b7`: core gates passed, while Windows candidate/installer exact-SHA evidence remains open.
- Added the first durable workflow event store foundation with sequence ordering and consumer idempotency tests.
- Added durable event delivery lifecycle state with completion, failure and retry attempt tracking.
- Added failure/retry coverage proving pending outbox events survive event-store unavailability without duplication.
- Added bounded outbox draining with per-event failure isolation for retry workers.
- Added `v3/scripts/drain_outbox.py` as a one-shot operational outbox publisher with JSON metrics.
- Added dependency-free Prometheus text export for durable workflow event metrics.
- Added a production observability runbook for outbox scheduling, metrics scrape and alert response.
- Added a dedicated V3 Runtime Event Store CI gate for durable events, outbox, projection and metrics.
- Added a repeatable release alignment validator for Flutter, installer, OpenAPI version and V3 packaging checks.
- Added a GUI/UX audit status document that gates setup.exe until Flutter and visual review evidence is approved.
- Added a dedicated GUI/UX CI workflow for asset validation, Flutter analyze and widget tests without release build steps.
- Added a durable one-event delivery API that retries failed consumers and suppresses completed duplicates.
- Added short-lived event delivery leases and expired-claim reclaim for distributed consumers.
- Added safe durable delivery counters and a restart/replay integration test covering the full local event flow.
- Added a transactional queue outbox and idempotent publisher bridge to the durable workflow event store.
- Added an idempotent workflow state projector and end-to-end queue-to-projection coverage.

บันทึกการเปลี่ยนแปลงทั้งหมดของ ENTERPRISE API ARCHITECTURE LOGIC TH และ ANEF

รูปแบบเวอร์ชันใช้ Semantic Versioning และเก็บ Snapshot ทุกเวอร์ชันไว้ใน `versions/`

## [2.0.0-rc.1] — 2026-08-09

### Changed

- เลื่อน Research OS V2 จาก `2.0.0-dev.1` เป็น `2.0.0-rc.1` สำหรับรอบ Release Candidate
- เปลี่ยน Windows installer metadata และชื่อไฟล์ติดตั้งให้ใช้เวอร์ชัน `2.0.0-rc.1`
- ยึด verified development candidate `4e25c05c9c14a857a21fc639d0bb3467015a1974` เป็นฐานของ RC branch
- RC ต้องผ่าน exact-SHA CI, Runtime Smoke, Build Installer, Installer Validation, verified candidate และ live staging gate อีกครั้งก่อนพิจารณา merge

### Safety

- ยังไม่ merge `main`
- ยังไม่สร้าง GitHub Release หรือ tag
- ยังไม่ deploy V2 ทับ production V1

## [v1.0.0-draft] — 2026-08-06

### Added

- เริ่มโครงสร้างเอกสารแบบเก็บทุกเวอร์ชัน
- เพิ่ม ANEF-001 — Project Overview
- เพิ่ม ANEF-002 — Vision
- เพิ่ม ANEF-003 — Mission
- เพิ่ม ANEF-004 — Core Values
- เพิ่ม ANEF-005 — Constitution
- เพิ่ม ANEF-006 — Design Principles
- เพิ่ม ANEF-007 — Enterprise Glossary พร้อมคำศัพท์มาตรฐาน 100 รายการ
- เพิ่ม ANEF-008 — Naming Standard
- เพิ่ม ANEF-009 — Documentation Standard
- เพิ่ม ANEF-010 — Versioning Standard
- เพิ่ม ANEF-011 — Repository Structure
- เพิ่ม Version Index และนโยบายรักษาเวอร์ชัน
- กำหนด `current/` เป็นตัวชี้ไปยังเวอร์ชันที่กำลังพัฒนา
- เพิ่ม Research Curator v0.1 สำหรับแปลงบทสนทนาเป็น Research Artifact
- เพิ่ม Research Curator v0.2 พร้อม Knowledge Filter, Quality Gate, Duplicate Detection, Typed Relationships และ Truth Status Promotion
- เพิ่ม Research Curator v0.3 พร้อม Knowledge Diff Report, JSON/Mermaid Knowledge Graph Export และ Validated Git Publisher
- เพิ่ม Research OS API v0.1 แบบ Provider-agnostic พร้อม REST endpoints สำหรับ Health, Provider, AI Generation, Conversation Analysis, Artifact Index และ Knowledge Graph
- เพิ่ม Provider Interface และ Adapters สำหรับ Mock, OpenAI-compatible/Local LLM, Anthropic และ Gemini
- เพิ่ม OpenAPI 3.1 Contract และ HTTP Integration Tests
- เพิ่ม Unit Tests สำหรับ Curator Core และ Knowledge Operations
- เพิ่ม GitHub Actions สำหรับ Compile, Test, Validate, Index Drift, Graph Export และ API Integration Tests

### Updated

- อัปเดตสารบัญเวอร์ชัน `v1.0.0-draft` ให้ครอบคลุม ANEF-001 ถึง ANEF-011
- แก้สถานะเอกสารล่าสุดใน Root README, Current README และ Version Index ให้ตรงกัน
- ย้าย Research Artifact รุ่นแรกเข้าสู่ Metadata Schema v0.2
- อัปเดตคู่มือ Research Curator สำหรับ Workflow แบบ Conversation → Knowledge Diff → Artifact → Graph → Git → Pull Request
- กำหนด API Analysis เป็น Preview-only และแยกการเขียน Repository ผ่าน Git Publisher กับ Review Gate
