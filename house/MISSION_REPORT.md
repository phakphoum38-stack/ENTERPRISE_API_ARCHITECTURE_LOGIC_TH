# 🏡 Mission Report

## Current mission

**Research OS v0.1 — เปิดได้ แล้วเจอเพื่อน**

- Status: BUILDING
- Owner: Phakphum
- Working name: Research OS
- Source of truth: Repository

## House progress

| ส่วนของบ้าน | สถานะ | รายละเอียด |
|---|---|---|
| ฐานราก | ✅ พร้อม | Vision, Constitution, Governance และ Ownership |
| โครงบ้าน | 🟡 กำลังสร้าง | Core Architecture และ Module boundaries |
| ประตูบ้าน | 🟡 Prototype | Research OS API และ Provider Adapters |
| ผู้ดูแลบ้าน | 🟡 Prototype | Research Curator, Knowledge Diff, Graph และ Git Publisher |
| ห้องรับแขก | ⏳ ยังไม่สร้าง | หน้าแอป “ยินดีต้อนรับกลับครับเพื่อน” |
| ห้องทำงาน | ⏳ ยังไม่เชื่อมครบ | Session + Chat + AI Runtime |
| ห้องสมุด | 🟡 เริ่มแล้ว | Research Artifacts และ Knowledge Graph |
| สมุดบันทึกบ้าน | ✅ เริ่มใช้งาน | `house/HOUSE_LOG.md` |

## Definition of done for v0.1

- [ ] เปิดแอปได้
- [ ] แสดงข้อความ “ยินดีต้อนรับกลับครับเพื่อน”
- [ ] กด “เริ่มงาน” ได้
- [ ] เริ่ม Session ได้
- [ ] ส่งข้อความผ่าน Research OS API ได้
- [ ] รับคำตอบจาก Mock Provider ได้
- [ ] เปลี่ยนไปใช้ AI Provider ที่ได้รับอนุญาตได้
- [ ] ปิดแอปโดยไม่พัง

## Core workflow target

```text
เปิดบ้าน
    ↓
เริ่ม Session
    ↓
คุยกับ AI
    ↓
จัดเก็บความรู้
    ↓
สร้างเอกสาร
    ↓
อัปเดต Mission Report
    ↓
อัปเดต House Log
    ↓
Review และอัปเดต Repository
```

## Current blocker

ยังไม่มี UI application ที่เชื่อม Research OS API แบบ End-to-End และยังต้องยืนยัน CI ล่าสุดให้ผ่าน

## Next construction work

1. ยืนยัน GitHub Actions ของ API และ Curator
2. สร้าง Minimum UI หน้าเดียว
3. เชื่อม `GET /health` และ `POST /v1/ai/generate`
4. ทดสอบด้วย Mock Provider
5. รัน End-to-End และบันทึกผลใน House Log
