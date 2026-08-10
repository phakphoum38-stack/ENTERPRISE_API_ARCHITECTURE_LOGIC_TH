# Research OS Tool Intelligence Training

สถานะ: V3 Unified / governed / review-first

## เป้าหมาย

สอน Research OS ให้ทำงานกับเครื่องมือเป็นระบบเดียวกันตั้งแต่การรู้จักของที่มีอยู่ การเลือกใช้ การวางแผน การค้นหาเครื่องมือภายนอก การประเมินหลักฐาน การออกแบบ adapter และการเรียนรู้จากผลการใช้งานจริง โดยไม่สร้างช่องทางติดตั้งหรือรันซอฟต์แวร์จากเว็บแบบอัตโนมัติ

## วงจรความสามารถ

1. Understand — อ่าน objective และระบุ capability ที่ต้องใช้
2. Inventory — ตรวจ ToolRegistry ซึ่งเป็น source of truth ของเครื่องมือที่ Research OS มีอยู่แล้ว
3. Rank — เลือกเครื่องมือจาก capability coverage, readiness และความเสี่ยงต่ำสุด
4. Gap — ระบุ capability ที่ยังไม่มีเครื่องมือรองรับ
5. Discover — เมื่อมี gap หรือผู้ใช้สั่งค้นหาเครื่องมือโดยตรง จึงค้นผ่าน web-search provider ที่ตั้งค่าไว้
6. Evidence — ขอแหล่งอ้างอิง publisher/project/version/license/platform/integration/auth/security
7. Evaluate — ประเมิน capability fit, provenance, maintenance, permission scope, credential risk, runtime risk, testability และ rollback
8. Design — สร้าง adapter plan แบบ reviewable โดย reuse ToolRegistry + ExecutionController เดิม
9. Review — ห้าม auto-download, auto-install, auto-register, auto-permission หรือ auto-execute
10. Execute — ถ้าผ่าน review แล้ว การใช้งานจริงยังต้องผ่าน ExecutionController/approval เดิม
11. Verify — ตรวจผลและ evidence หลังใช้งาน
12. Learn — LearningEngine บันทึก structured outcomes และสร้าง tool playbook สำหรับการเลือกครั้งต่อไป

## แหล่งค้นหาหลัก

ลำดับเริ่มต้น:

1. Official MCP Registry
2. GitHub Marketplace / canonical repositories
3. PyPI
4. npm registry
5. Official vendor/project websites

ไม่ใช้ผลการค้นหาเพียงอย่างเดียวเป็นสิทธิ์ในการติดตั้งหรือ execute

## ข้อมูลที่ candidate ต้องมี

- canonical/official URL
- publisher/owner
- tool type
- capabilities
- integration mode เช่น API, MCP, SDK, CLI หรือ plugin
- supported platforms
- license ถ้ามี
- credential/auth requirements
- network requirements
- evidence URLs
- risk level
- recommendation
- trust score ที่มาจาก evidence completeness ไม่ใช่จากชื่อเสียงเพียงอย่างเดียว

## การออกแบบ Adapter

ทุก adapter proposal ใช้หลัก Reuse → Update → Replace → Create

- reuse ToolRegistry เดิม
- reuse permissioned ExecutionController เดิม
- map capability เท่าที่จำเป็น
- least privilege
- secret เก็บเป็น reference/ชื่อ environment variable เท่านั้น
- read-only หรือ dry-run ก่อนเมื่อทำได้
- deterministic input validation
- mock/fake unit tests
- opt-in integration test
- evidence + rollback plan
- review ก่อน registration/execution

## Learning / Tool Playbook

Research OS เรียนจาก structured outcome เท่านั้น เช่น:

- verified
- failed
- blocked
- verification_failed

ใช้เพื่อประเมินความมั่นใจของเครื่องมือและหาปัญหาซ้ำ ไม่เก็บ hidden reasoning ไม่แก้ source code/model weights/permissions เอง

## API ที่ได้รับผลโดยอัตโนมัติ

`GET /v2/master`

จะแสดงสถานะ Tool Intelligence policy และแหล่งค้นหา

`POST /v2/master/plan`

จะเพิ่ม `tool_intelligence` ในแผน โดยสามารถระบุ `context.required_tool_capabilities` ได้ ถ้า objective เป็นคำสั่งค้นหาเครื่องมือโดยตรง Unified Master จะเรียก web-search provider เพื่อสร้าง external candidate research โดยยังไม่ติดตั้งหรือ execute

## Safety invariants

- external_tools_auto_downloaded = false
- external_tools_auto_installed = false
- external_tools_auto_executed = false
- automatic_permission_grant = false
- review_required = true
- self_modification = false
- automatic_merge_release_deploy = false
