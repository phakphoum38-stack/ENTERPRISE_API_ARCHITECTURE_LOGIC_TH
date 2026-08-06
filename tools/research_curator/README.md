# Research Curator

Research Curator คือเครื่องมือแปลงบทสนทนาเป็น **Research Artifact** ที่จัดเก็บ ตรวจสอบ เปรียบเทียบ เชื่อมโยง และเผยแพร่ผ่าน Git ได้อย่างเป็นระบบ

## ความสามารถ v0.3.0

- Curator Core: Knowledge Filter, Quality Gate, Duplicate Detection, Evidence, Relationships และ Truth Status
- Knowledge Diff Report: เปรียบเทียบ Added, Removed และ Unchanged แยกตาม Section
- Knowledge Graph Export: JSON และ Mermaid พร้อม External Targets
- Validated Git Publisher: ตรวจ Gate, สร้าง Branch, Commit, Push และเปิด Pull Request
- GitHub Actions: Compile, Unit Tests, Artifact Validation, Index Drift และ Graph Export

## สร้าง Artifact

```bash
python tools/research_curator/curator.py curate \
  --input conversation.txt \
  --title "Knowledge must be reasoner-agnostic" \
  --status hypothesis \
  --tag knowledge \
  --relate supports:RES-20260806-CONVERSATION-TO-KNOWLEDGE
```

## ตรวจและเลื่อนสถานะ

```bash
python tools/research_curator/curator.py validate
python tools/research_curator/curator.py index
python tools/research_curator/curator.py promote \
  research/artifacts/RES-....md \
  --to validated \
  --evidence "ผ่านการทดลองกับสามโดเมน"
```

## Knowledge Diff

```bash
python tools/research_curator/knowledge_ops.py diff \
  --old research/artifacts/RES-OLD.md \
  --new research/artifacts/RES-NEW.md \
  --output research/diffs/RES-OLD_TO_RES-NEW.md
```

## Knowledge Graph

```bash
python tools/research_curator/knowledge_ops.py graph \
  --artifacts research/artifacts \
  --output research/graph/knowledge-graph
```

ผลลัพธ์คือ `.json` และ `.mmd`

## Git Publisher

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
- สมมติฐานต้องใช้ `--allow-hypothesis` อย่างชัดเจน

## หลักการสำคัญ

1. บทสนทนาเป็น Source ไม่ใช่ Single Source of Truth
2. Commit เฉพาะ Knowledge Diff ไม่ใช่ Transcript ทั้งหมด
3. Truth Status ต้องเลื่อนตาม Evidence
4. Git Publisher ต้อง Fail Closed เมื่อไม่ผ่าน Gate
5. มนุษย์ควรตรวจ Artifact สำคัญก่อน Merge
