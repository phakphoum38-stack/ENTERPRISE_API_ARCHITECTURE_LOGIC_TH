# 🏡 House Structure

เอกสารนี้กำหนดโครงสร้างเชิงระบบของ "บ้าน" ซึ่งเป็นชื่อเชิงประสบการณ์ของ Research OS ระหว่างการก่อสร้าง

## Core principle

> ในบ้านหลังนี้ ทุกบทสนทนาที่มีคุณค่าจะกลายเป็นส่วนหนึ่งของบ้าน

## House map

```text
house/
├── HOUSE_STRUCTURE.md      # แปลนบ้านและหน้าที่ของแต่ละส่วน
├── MISSION_REPORT.md       # บ้านเราสร้างไปถึงไหนแล้ว
├── HOUSE_LOG.md            # สมุดบันทึกการเติบโตของบ้าน
├── RULES.md                # กฎของบ้าน
└── README.md               # จุดเริ่มต้นสำหรับคนและ AI ที่เข้ามาในบ้าน

knowledge/
├── discoveries/            # สิ่งที่ค้นพบ
├── decisions/              # การตัดสินใจและเหตุผล
├── questions/              # คำถามที่ยังเปิดอยู่
├── hypotheses/             # สมมติฐานที่ต้องพิสูจน์
└── index/                  # ดัชนีความรู้

docs/
├── architecture/           # โครงสร้างและการออกแบบ
├── adr/                    # Architecture Decision Records
├── research/               # เอกสารวิจัย
└── specifications/         # ข้อกำหนดที่พร้อมนำไปพัฒนา

tools/
├── research_curator/       # สกัดความรู้จากบทสนทนา
├── research_os_api/        # API กลางและ AI provider adapters
└── house_keeper/           # ดูแล Mission Report, House Log และการเตรียม Repository update
```

## Meaning of each room

| ภาษาของบ้าน | ความหมายทางระบบ |
|---|---|
| ฐานราก | Vision, Constitution, Governance, Ownership |
| โครงบ้าน | Core Architecture และ Module boundaries |
| ประตูบ้าน | API และ Authentication boundary |
| ห้องรับแขก | UI หน้าแรกและ Working Session |
| ห้องทำงาน | Session Engine และ AI Runtime |
| ห้องสมุด | Knowledge, Artifact, Index และ Graph |
| สมุดบันทึกบ้าน | House Log และ Provenance |
| รายงานบ้าน | Mission Report และ Project health |
| ผู้ดูแลบ้าน | House Keeper / Research Curator workflow |

## Required workflow

```text
Conversation
    ↓
Knowledge Filter
    ↓
Knowledge Diff
    ↓
Artifact / Document
    ↓
Mission Report Update
    ↓
House Log Update
    ↓
Repository Review
    ↓
Commit / Pull Request
```

## House Keeper responsibilities

House Keeper ต้องรองรับความสามารถหลัก 5 ข้อ:

1. คุยไปด้วยและจัดเก็บความรู้ไปด้วย
2. สร้างเอกสารอัตโนมัติจากสิ่งที่มีคุณค่า
3. เตรียมและอัปเดต Repository ผ่าน Review Gate
4. อัปเดต Mission Report
5. อัปเดต House Log

## Governance boundary

- ความรู้เป็นของโครงการ
- การตัดสินใจเป็นของเจ้าของโครงการ
- AI เป็นผู้ช่วย ไม่ใช่ผู้ถือสิทธิ์
- AI สร้าง Commit หรือ Pull Request ได้ตามสิทธิ์ แต่ห้ามเปลี่ยน Ownership, License หรือ Merge โดยลำพัง

## Naming status

`Research OS` เป็นชื่อระหว่างก่อสร้าง เมื่อบ้านเปิดใช้งานได้จริง เจ้าของโครงการจะเป็นผู้อนุมัติชื่ออย่างเป็นทางการ
