# Research Curator

Research Curator คือเครื่องมือแปลงบทสนทนาเป็น **Research Artifact** ที่จัดเก็บ ตรวจสอบ และพัฒนาสถานะย้อนหลังได้ใน Repository

## ความสามารถ v0.2.0

- อ่านข้อความธรรมดา, stdin หรือ JSON conversation export
- Knowledge Filter ตัดข้อความตอบรับสั้นที่ไม่มีสาระออก
- คำนวณ `quality_score` และปฏิเสธ Artifact ที่ต่ำกว่าเกณฑ์
- สร้าง Source Hash และ Knowledge Content Hash แยกกัน
- ตรวจ Knowledge Diff ซ้ำจาก `content_hash`
- สกัด Summary, Discoveries, Hypotheses, Open Questions, Decisions และ Next Actions
- รองรับ Evidence และ Relationships แบบมีชนิด
- ตรวจ Cross-reference และ Relationship target
- Truth Status lifecycle: `new → hypothesis → experimenting → observed → repeated → validated → standardized → deprecated`
- การเลื่อนเป็น `validated` หรือ `standardized` ต้องมี Evidence
- สร้าง Markdown พร้อม machine-readable front matter
- อัปเดต `research/artifacts/README.md` อัตโนมัติ
- ทำงานแบบ deterministic โดยไม่ต้องเชื่อมบริการภายนอก
- รองรับ provider adapter แบบเลือกใช้

## สร้าง Artifact

```bash
python tools/research_curator/curator.py curate \
  --input conversation.txt \
  --title "Knowledge must be reasoner-agnostic" \
  --status hypothesis \
  --tag knowledge \
  --tag reasoning \
  --relate supports:RES-20260806-CONVERSATION-TO-KNOWLEDGE
```

หรือส่งผ่าน stdin:

```bash
cat conversation.txt | python tools/research_curator/curator.py curate \
  --title "Conversation-to-Knowledge Workflow"
```

Knowledge Filter ใช้ค่าเริ่มต้น `--min-quality 20` และเปลี่ยนได้:

```bash
python tools/research_curator/curator.py curate \
  --input conversation.txt \
  --title "High-confidence research note" \
  --min-quality 50
```

## ตรวจและสร้างดัชนี

```bash
python tools/research_curator/curator.py validate
python tools/research_curator/curator.py index
```

## เลื่อน Truth Status

```bash
python tools/research_curator/curator.py promote \
  research/artifacts/RES-....md \
  --to validated \
  --evidence "ผ่านการทดลองกับสามโดเมน"
```

ระบบห้ามลดสถานะย้อนหลัง ยกเว้นเปลี่ยนเป็น `deprecated` และบังคับ Evidence เมื่อต้องการ `validated` หรือ `standardized`

## Relationships ที่รองรับ

- `relates_to`
- `supports`
- `contradicts`
- `extends`
- `depends_on`
- `derived_from`
- `supersedes`
- `verified_by`
- `implements`

## รูปแบบ JSON ที่รองรับ

```json
[
  {"role": "user", "content": "ไม่ควรล็อกกฎ"},
  {"role": "assistant", "content": "กฎควรเป็น Policy Plugin ที่เปลี่ยนได้"}
]
```

หรือ:

```json
{
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

## Provider Adapter

โหมดพื้นฐานไม่ต้องใช้ AI ภายนอก หากต้องการให้โมเดลช่วยสกัดความรู้ ให้กำหนด:

```bash
export CURATOR_API_URL="https://provider.example/v1/chat/completions"
export CURATOR_API_KEY="..."
export CURATOR_MODEL="model-name"
```

แล้วเพิ่ม `--provider` ตอนสั่ง `curate` Endpoint ต้องรองรับ Chat Completions-compatible response และคืน JSON ตาม schema ที่เครื่องมือร้องขอ

## หลักการสำคัญ

1. บทสนทนาเป็น Source ไม่ใช่ Single Source of Truth
2. Commit เฉพาะ Knowledge Diff ไม่ใช่ Transcript ทั้งหมด
3. Artifact ต้องมี Provenance, Source Hash และ Content Hash
4. สิ่งที่ยังไม่พิสูจน์ต้องอยู่ใน Hypotheses หรือ Open Questions
5. เครื่องมือห้ามแต่งข้อเท็จจริงที่ไม่มีใน Source
6. Truth Status ต้องเลื่อนตาม Evidence ไม่ใช่ความมั่นใจของ AI
7. มนุษย์ควรตรวจ Artifact ก่อน Merge เมื่อใช้กับมาตรฐานสำคัญ
