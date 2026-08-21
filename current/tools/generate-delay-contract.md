# Generate Delay Contract

- Document ID: ANEF-GEN-001
- Version: v1.0.0-draft
- Status: Draft
- Owner: Research OS / Generate Orchestrator

## Purpose

กำหนด Contract สำหรับค่าหน่วงเวลา (delay) ที่ Generate สร้างขึ้นครั้งเดียว แล้วนำค่าเดิมไปใช้กับการ `sleep` และ downstream steps โดยไม่คำนวณซ้ำ

## Contract

1. Generate ต้องสร้างค่า `delay_seconds` หนึ่งค่าใน execution context
2. ค่า `delay_seconds` ต้องเป็นตัวเลขที่ไม่ติดลบ
3. `sleep(delay_seconds)` ต้องใช้ค่าที่ Generate สร้างไว้โดยตรง
4. หลัง `sleep` ค่าเดิมต้องสามารถถูกอ่านและส่งต่อให้ downstream step ได้
5. การใช้ค่า delay เดิมต้องไม่สร้างค่าหน่วงใหม่โดยไม่จำเป็น
6. Execution context ต้องผูกกับ workflow/run context เพื่อให้ตรวจสอบย้อนหลังได้

## Formula

```text
GeneratedDelay = Generate(delay_seconds)
SleepResult = sleep(GeneratedDelay)
DownstreamDelay = GeneratedDelay
```

ดังนั้น:

```text
SleepInput == GeneratedDelay == DownstreamDelay
```

## Validation

- `delay_seconds < 0` -> reject
- `delay_seconds == 0` -> valid
- `sleep()` ต้องถูกเรียกด้วยค่าที่ Generate ไว้
- downstream ต้องเห็นค่าเดียวกับค่าที่ Generate

## Safety Boundary

Delay Contract เป็น execution primitive ไม่ใช่ scheduling policy ระดับ queue

หากระบบมีงานจำนวนมาก Production scheduler สามารถเปลี่ยน implementation จาก blocking sleep เป็น delayed scheduling ได้ในอนาคต โดยต้องรักษา Contract เดิม:

```text
GeneratedDelay -> wait/delay -> downstream
```

## Compatibility

Contract นี้อยู่ใน `current/tools/` เพื่อใช้เป็นสัญญาระหว่าง Architecture Source of Truth กับ tooling/implementation และต้องรักษา compatibility เมื่อ version เปลี่ยน

## Revision History

| Version | Status | Change |
|---|---|---|
| v1.0.0-draft | Draft | Initial Generate Delay Contract |
