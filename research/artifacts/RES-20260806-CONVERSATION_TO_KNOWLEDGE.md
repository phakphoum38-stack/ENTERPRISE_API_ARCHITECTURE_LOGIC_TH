---
artifact_id: "RES-20260806-CONVERSATION-TO-KNOWLEDGE"
title: "Conversation-to-Knowledge Continuous Publishing"
status: "observed"
created_at: "2026-08-06T07:45:00+00:00"
source_hash: "conversation:chat-session-2026-08-06"
tags: ["research", "knowledge", "automation", "github", "curation"]
---

# RES-20260806-CONVERSATION-TO-KNOWLEDGE — Conversation-to-Knowledge Continuous Publishing

## Summary

บทสนทนาระยะยาวไม่ควรถูกปล่อยให้สะสมเป็นข้อความจำนวนมากแล้วค่อยสรุปภายหลัง ระบบควรสกัด Knowledge Diff ระหว่างการสนทนา สร้าง Research Artifact อัปเดตดัชนี และส่งการเปลี่ยนแปลงเข้า Git อย่างต่อเนื่อง เพื่อรักษาองค์ความรู้ ลดงานซ้ำ และทำให้ทุกแนวคิดมีประวัติที่ตรวจสอบย้อนหลังได้

## Discoveries

- การคุยและการบันทึกองค์ความรู้ควรเป็นกระบวนการเดียวกัน ไม่ใช่งานสองช่วงที่แยกออกจากกัน
- Conversation เป็นแหล่งข้อมูลต้นทาง แต่ไม่ควรถูกถือเป็น Single Source of Truth โดยตรง
- สิ่งที่ควร Commit คือ Knowledge Diff ที่ผ่านการจัดหมวด พร้อม Provenance ไม่ใช่ Transcript ทั้งหมด
- Artifact ต้องแยก Discoveries, Hypotheses, Open Questions, Decisions และ Next Actions อย่างชัดเจน
- ทุก Artifact ควรมี Identity, Status, Source Hash, Timestamp และ Tags
- AI ควรทำหน้าที่ Research Curator ระหว่างสนทนา ไม่ใช่เพียงตอบข้อความ
- Repository ควรเติบโตไปพร้อมกับการสนทนา เพื่อไม่ให้ความรู้สูญหายหรือถูกสรุปซ้ำ

## Hypotheses

- Research Curator แบบ deterministic สามารถลดการสูญเสียองค์ความรู้ได้ แม้ยังไม่ใช้โมเดล AI ภายนอก
- Provider-agnostic enrichment สามารถเพิ่มคุณภาพการสกัดโดยไม่ผูก Repository กับผู้ให้บริการรายเดียว
- Knowledge Diff ที่มีโครงสร้างจะค้นหาและอ้างอิงได้ดีกว่าการเก็บ Transcript ขนาดใหญ่
- การอัปเดต Artifact ทุกครั้งที่มีสาระใหม่จะลดต้นทุนการสรุปงานระยะยาวอย่างมีนัยสำคัญ

## Open Questions

- เกณฑ์ใดใช้ตัดสินว่าเนื้อหาใหม่มีคุณค่าพอที่จะสร้าง Commit?
- ควรรวม Artifact ที่มีเนื้อหาซ้ำหรือเชื่อมด้วย Relationship แทน?
- Source transcript ควรถูกเก็บไว้นานเท่าใด และควรอยู่ที่ใด?
- การยกระดับสถานะจาก `hypothesis` เป็น `validated` ต้องใช้ Evidence ขั้นต่ำแบบใด?
- จะตรวจจับแนวคิดที่ถูกหักล้างภายหลังและทำ Deprecation อัตโนมัติได้อย่างไร?

## Decisions

- เริ่มสร้างเครื่องมือ `tools/research_curator/curator.py` ภายใน Repository นี้ทันที
- เวอร์ชันแรกต้องใช้งานได้โดยไม่ต้องมีบริการภายนอก
- Provider adapter เป็นความสามารถเสริมและต้องไม่เป็น dependency ของ Core
- รูปแบบ Artifact หลักเป็น Markdown พร้อม machine-readable front matter
- Truth Status แยกจาก Version และต้องไม่ถูกเลื่อนระดับโดยอัตโนมัติ
- Artifact ทุกชิ้นต้องผ่านการตรวจ Metadata ก่อน Merge

## Next Actions

- เพิ่ม Unit Tests สำหรับ parser, extractor, renderer และ validator
- เพิ่ม GitHub Action สำหรับตรวจ Artifact ใน Pull Request
- เพิ่ม Knowledge relationship fields และ cross-reference validator
- เพิ่มคำสั่ง `diff` เพื่อเทียบ Knowledge ใหม่กับ Artifact เดิม
- เพิ่มคำสั่ง `promote` สำหรับเปลี่ยน Truth Status พร้อม Evidence reference
- ออกแบบ GitHub Action ที่สร้าง Pull Request จาก Conversation Export โดยอัตโนมัติ

## Provenance

- Source: บทสนทนาระหว่างผู้ใช้และ AI วันที่ 6 สิงหาคม 2026
- Captured manually as the first live Research Curator artifact
- Generator target: `Research Curator v0.1.0`
