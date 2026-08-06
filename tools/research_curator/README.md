# Research Curator

Research Curator คือเครื่องมือแปลงบทสนทนาเป็น **Research Artifact** ที่จัดเก็บและตรวจสอบย้อนหลังได้ใน Repository

## ความสามารถ v0.1.0

- อ่านข้อความธรรมดาหรือ JSON conversation export
- สร้าง Artifact ID แบบคงที่จากวันที่และ Source Hash
- สกัด Summary, Discoveries, Hypotheses, Open Questions, Decisions และ Next Actions
- สร้าง Markdown พร้อม machine-readable front matter
- อัปเดต `research/artifacts/README.md` อัตโนมัติ
- ตรวจ Metadata และ Truth Status
- ทำงานแบบ deterministic ได้โดยไม่ต้องเชื่อมบริการภายนอก
- รองรับ provider adapter แบบเลือกใช้ผ่าน HTTP endpoint

## เริ่มใช้งาน

```bash
python tools/research_curator/curator.py curate \
  --input conversation.txt \
  --title "Knowledge must be reasoner-agnostic" \
  --status hypothesis \
  --tag knowledge \
  --tag reasoning
```

หรือส่งข้อความผ่าน stdin:

```bash
cat conversation.txt | python tools/research_curator/curator.py curate \
  --title "Conversation-to-Knowledge Workflow"
```

ตรวจ Artifact:

```bash
python tools/research_curator/curator.py validate
```

สร้างดัชนีใหม่:

```bash
python tools/research_curator/curator.py index
```

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

แล้วเพิ่ม `--provider`:

```bash
python tools/research_curator/curator.py curate \
  --input conversation.json \
  --title "Research Session" \
  --provider
```

Endpoint ต้องรับ request และคืน response ในรูปแบบ Chat Completions-compatible โดยเนื้อหาคำตอบต้องเป็น JSON ตาม schema ที่เครื่องมือร้องขอ

## Truth Status

ค่าที่รองรับ:

- `hypothesis`
- `observed`
- `repeated`
- `validated`
- `reference`
- `deprecated`

เครื่องมือจะไม่ยกระดับสถานะให้เอง การเปลี่ยนจาก Hypothesis ไปเป็น Validated ต้องมี Evidence และผ่านกระบวนการ Review ที่กำหนดในอนาคต

## หลักการสำคัญ

1. บทสนทนาเป็น Source ไม่ใช่ Single Source of Truth
2. Artifact ต้องมี Provenance และ Source Hash
3. สิ่งที่ยังไม่พิสูจน์ต้องอยู่ใน Hypotheses หรือ Open Questions
4. เครื่องมือห้ามแต่งข้อเท็จจริงที่ไม่มีใน Source
5. มนุษย์ต้องตรวจ Artifact ก่อน Merge เมื่อใช้กับมาตรฐานสำคัญ
