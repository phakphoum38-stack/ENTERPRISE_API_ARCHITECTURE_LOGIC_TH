# Changelog

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
