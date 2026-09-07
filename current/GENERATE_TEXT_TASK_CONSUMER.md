# Generate Text Task Consumer

- Schema: `research-os-generate-text-task/v1`
- Status: CANONICAL
- Boundary: read-only intake / normalization

## Purpose

รับข้อความงานที่ Generate จัดเก็บไว้ในรูป JSON แล้วตรวจ schema, owner scope, ขนาด และ field allow-list ก่อนแปลงเป็น `generate.text` intent envelope สำหรับ dispatcher ชั้นถัดไป

## Task shape

```json
{
  "schema": "research-os-generate-text-task/v1",
  "task_id": "task-001",
  "owner_id": "owner",
  "text": "...",
  "stack": "python",
  "platform": "linux"
}
```

`stack` และ `platform` เป็น optional แต่ถ้ามีต้องอยู่ใน allow-list ที่ consumer กำหนด

## Bounds

- task file: 64 KiB
- task text: 32 KiB
- task collection: 100 JSON files
- task/owner identifiers: 64 characters

## Flow

```text
Stored Text Task
      ↓
GenerateTextTaskConsumer
      ↓
validate + normalize + source SHA256
      ↓
Generate `generate.text` Intent
      ↓
Deferred Dispatcher
      ↓
Generate Orchestrator
```

Consumer **ไม่** dispatch workflow, ไม่เรียก GitHub API, ไม่สร้าง branch, ไม่แก้ `main`, และไม่ execute tool/process/shell/browser/MCP/Computer Use

## Determinism

`consume_all()` อ่านไฟล์ตามชื่อเรียงลำดับ และ intent envelope ไม่ใส่ runtime timestamp, run id, nonce หรือข้อมูล volatile

## Owner isolation

`owner_id` เป็นส่วนหนึ่งของ task และ intent โดยตรง; consumer ไม่อนุญาต field ที่สามารถใช้เปลี่ยน authority หรือ scope โดยปริยาย

## Relationship to Generate Orchestrator

Generate Orchestrator ยังคงเป็น workflow orchestration authority และ exact-SHA gate ตาม existing registry. Consumer นี้เป็นเพียง intake boundary ที่เติมช่องว่างระหว่าง stored text task กับ dispatcher; จึงไม่มี execution authority ใหม่

## Evidence

Implementation: `tools/generate_text_task_consumer.py`
Regression tests: `tools/test_generate_text_task_consumer.py`
