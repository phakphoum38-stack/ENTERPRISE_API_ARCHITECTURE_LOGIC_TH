# 🏡 House Log

สมุดบันทึกนี้เก็บการเติบโตของ Research OS ในภาษาของ “บ้าน” พร้อมหลักฐานจาก Repository

## 2026-08-07 — Living House v0.1 implemented

### Completed

- เพิ่ม Entrance UI ที่ `apps/research_os_web/`
- แสดง “ยินดีต้อนรับกลับครับเพื่อน” และ House Motto
- เพิ่มปุ่ม `เริ่มงาน` และสร้าง Session ID ฝั่งผู้ใช้
- เชื่อม `GET /health` และ `POST /v1/ai/generate`
- เพิ่ม Chat Session ด้วย Mock Provider เป็นค่าเริ่มต้น
- เพิ่ม Knowledge Capture ผ่าน `POST /v1/conversations/analyze`
- คงการจัดเก็บแบบ Preview-only และต้องผ่าน Git Review Gate ก่อน Persist
- เพิ่ม End-to-End Test สำหรับ UI → Health → Chat → Knowledge Capture
- เพิ่ม UI/E2E checks ใน GitHub Actions

### Governance retained

- House Brain และ AI เสนอได้ แต่เจ้าของโครงการเป็นผู้ตัดสินใจ
- API ไม่เขียน Knowledge Artifact ลง Repository โดยอัตโนมัติ
- Provider เริ่มต้นเป็น `mock` เพื่อให้ทดสอบได้โดยไม่ใช้ Secret

### Current truth

บ้านเปิดได้จาก Research OS API server และเส้นทางหลักผ่านการทดสอบอัตโนมัติแล้ว เหลือการเพิ่ม Authentication และ Production deployment ก่อนเปิดใช้งานผ่าน Internet

### Next

1. เพิ่ม Authentication และ Session persistence
2. เพิ่ม Controlled Artifact Approval workflow
3. เตรียม Packaging/Deployment สำหรับผู้ใช้จริง

## 2026-08-06 — House structure established

### Decisions

- ใช้ `Research OS` เป็นชื่อระหว่างก่อสร้าง
- เมื่อบ้านพร้อมใช้งานจริง เจ้าของโครงการจะเป็นผู้อนุมัติชื่ออย่างเป็นทางการ
- กำหนด House Keeper เป็น Workflow หลักสำหรับการจัดเก็บความรู้และดูแลสถานะบ้าน

### Core capabilities retained

- คุยไปด้วยและจัดเก็บความรู้ไปด้วย
- สร้างเอกสารอัตโนมัติ
- อัปเดต Repository ผ่าน Review Gate
- ทำ Mission Report
- ทำ House Log
