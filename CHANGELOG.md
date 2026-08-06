# Changelog

บันทึกการเปลี่ยนแปลงทั้งหมดของ ENTERPRISE API ARCHITECTURE LOGIC TH และ ANEF

รูปแบบเวอร์ชันใช้ Semantic Versioning และเก็บ Snapshot ทุกเวอร์ชันไว้ใน `versions/`

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
- เพิ่ม Research Curator v0.2 พร้อม Knowledge Filter, Knowledge Diff duplicate detection, quality score, typed relationships และ Truth Status promotion
- เพิ่ม Unit Tests สำหรับ filter, duplicate detection, relationship parser และ evidence-aware promotion
- เพิ่ม GitHub Actions สำหรับ compile, unit test, artifact validation และ index drift

### Updated

- อัปเดตสารบัญเวอร์ชัน `v1.0.0-draft` ให้ครอบคลุม ANEF-001 ถึง ANEF-011
- แก้สถานะเอกสารล่าสุดใน Root README, Current README และ Version Index ให้ตรงกัน
- ย้าย Research Artifact แรกเข้าสู่ Metadata Schema v0.2
