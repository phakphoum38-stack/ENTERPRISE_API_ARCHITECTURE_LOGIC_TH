# Research Curator

Research Curator คือเครื่องมือแปลงบทสนทนาเป็น **Research Artifact** ที่จัดเก็บ ตรวจสอบ เปรียบเทียบ เชื่อมโยง และเผยแพร่ผ่าน Git ได้อย่างเป็นระบบ

## ความสามารถ v0.3.0

### Curator Core

- อ่านข้อความธรรมดา, stdin หรือ JSON conversation export
- Knowledge Filter ตัดข้อความตอบรับสั้นที่ไม่มีสาระ
- คำนวณ `quality_score` และใช้ Quality Gate
- แยก Source Hash และ Knowledge Content Hash
- ป้องกัน Duplicate Artifact จาก `content_hash`
- สกัด Summary, Discoveries, Hypotheses, Open Questions, Decisions และ Next Actions
- รองรับ Evidence และ Typed Relationships
- ตรวจ Cross-reference และ Truth Status lifecycle
- เลื่อนสถานะด้วยคำสั่ง `promote` พร้อม Evidence Gate

### Knowledge Operations

- เปรียบเทียบ Artifact แบบรายการต่อรายการ
- แสดง Added, Removed และ Unchanged แยกตาม Section
- ส่งออก Knowledge Graph เป็น JSON
- ส่งออก Diagram เป็น Mermaid flowchart
- รายงาน Relationship target ที่ยังไม่มีใน Repository

### Git Publisher

- ตรวจ Metadata, Status, Quality และ Duplicate Gate ก่อน Publish
- สร้าง Branch จาก `main` หรือ Base ที่กำหนด
- Stage เฉพาะ Artifact และไฟล์ประกอบที่เลือก
- Commit และ Push ผ่าน Git
- เปิด Draft/Ready Pull Request ผ่าน GitHub CLI
- ไม่เผยแพร่ Hypothesis โดยค่าเริ่มต้น เว้นแต่ระบุ `--allow-hypothesis`

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

## สร้าง Knowledge Diff Report

```bash
python tools/research_curator/knowledge_ops.py diff \
  --old research/artifacts/RES-OLD.md \
  --new research/artifacts/RES-NEW.md \
  --output research/diffs/RES-OLD_TO_RES-NEW.md
```

รายงานจะแยกความเปลี่ยนแปลงใน Discoveries, Hypotheses, Open Questions, Decisions, Next Actions และ Evidence

## ส่งออก Knowledge Graph

```bash
python tools/research_curator/knowledge_ops.py graph \
  --artifacts research/artifacts \
  --output research/graph/knowledge-graph
```

ผลลัพธ์:

- `research/graph/knowledge-graph.json`
- `research/graph/knowledge-graph.mmd`

## Publish ผ่าน Git และ GitHub CLI

ต้องมี `git`, `gh` และ Working Tree ที่สะอาด:

```bash
python tools/research_curator/git_publisher.py \
  --artifact research/artifacts/RES-....md \
  --include research/artifacts/README.md \
  --include research/graph/knowledge-graph.json \
  --include research/graph/knowledge-graph.mmd \
  --open-pr \
  --draft
```

Publish Gate เริ่มต้น:

- Status ต้องเป็น `observed`, `repeated`, `validated` หรือ `standardized`
- `quality_score` ต้องไม่น้อยกว่า 45
- ห้ามเป็น Duplicate Artifact
- Metadata สำคัญต้องครบ

การ Publish สมมติฐานต้องระบุอย่างชัดเจน:

```bash
python tools/research_curator/git_publisher.py \
  --artifact research/artifacts/RES-....md \
  --allow-hypothesis \
  --open-pr \
  --draft
```

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

## Provider Adapter

โหมดพื้นฐานไม่ต้องใช้ AI ภายนอก หากต้องการ enrichment ให้กำหนด `CURATOR_API_URL`, `CURATOR_API_KEY`, `CURATOR_MODEL` แล้วเพิ่ม `--provider` ตอนสั่ง `curate`

## CI

GitHub Actions จะทำงานดังนี้:

1. Compile Curator, Knowledge Operations และ Git Publisher
2. รัน Unit Tests
3. Validate Metadata, Status, Evidence และ Relationships
4. ตรวจ Index Drift
5. ทดลอง Export Knowledge Graph และตรวจว่าไฟล์ไม่ว่าง

## หลักการสำคัญ

1. บทสนทนาเป็น Source ไม่ใช่ Single Source of Truth
2. Commit เฉพาะ Knowledge Diff ไม่ใช่ Transcript ทั้งหมด
3. Artifact ต้องมี Provenance, Source Hash และ Content Hash
4. สิ่งที่ยังไม่พิสูจน์ต้องอยู่ใน Hypotheses หรือ Open Questions
5. เครื่องมือห้ามแต่งข้อเท็จจริงที่ไม่มีใน Source
6. Truth Status ต้องเลื่อนตาม Evidence ไม่ใช่ความมั่นใจของ AI
7. Git Publisher ต้อง Fail Closed เมื่อไม่ผ่าน Gate
8. มนุษย์ควรตรวจ Artifact ก่อน Merge เมื่อใช้กับมาตรฐานสำคัญ
