# Research OS V3 — AI Workspace Feature Map

สถานะ: Proposed  
ฐานระบบ: Research OS V2 stable  
แนวทาง: เพิ่มแบบโมดูล ไม่รื้อ Core/API V2 เดิม

## 1. หลักการที่ห้ามเปลี่ยน

1. **Preserve V2** — Core/API V2, Agent Runtime, Agent Orchestrator, Workspace Knowledge Engine และ Developer Platform เดิมยังเป็นฐานเสถียร
2. **One Truth** — แต่ละข้อมูลและตรรกะมี owner เพียงชุดเดียว แท็บใหม่เรียกใช้ owner เดิมผ่าน interface
3. **No Duplicate API** — ใช้ API/provider gateway ที่มีอยู่ ไม่สร้างระบบซ้ำและไม่ผูก key ไว้ใน source code
4. **Module and Tab First** — ฟีเจอร์ใหม่แยกเป็นโมดูลและแท็บที่ชัดเจน
5. **Local/Provider Neutral** — Brain Skills ทำงานกับกฎภายใน, local model หรือ OpenAI-compatible provider ได้
6. **Adaptive 6⁶** — รองรับโครงสร้างผู้ช่วยแบบลำดับชั้นสูงสุด 6⁶ แต่เปิด worker ตามภาระงานจริง
7. **Evidence Before Merge** — ทุก increment อยู่บน branch/PR แยก มี tests, migration notes และ rollback evidence
8. **Approval for Writes** — การส่ง แก้ ลบ เผยแพร่ หรือกระทำต่อระบบภายนอกต้องผ่าน permission และ approval gate

## 2. แผนผังแท็บหลัก

| แท็บ | ขอบเขต | Owner เดิมที่เชื่อม |
| --- | --- | --- |
| Chat | Conversations, streaming, history, share/export | Conversation/API service |
| Projects | Project context, folders, members, timeline | Workspace Knowledge Engine |
| Files & Knowledge | Upload, OCR, parsing, search, citations | Workspace Knowledge Engine |
| Memory | User/project memory, provenance, controls | Existing memory/context stores |
| Agents | Custom agents, orchestration, handoff, approvals | Agent Platform + Orchestrator |
| Brain Skills | Planning, reasoning, critique, safety, learning | New registry over Agent Runtime |
| Tools & Plugins | Tools, MCP, connectors, browser/computer actions | Developer Platform + tool gateway |
| Voice | Realtime and chained voice workflows | Media transport + Agent Runtime |
| Canvas | Documents, code, tables, charts, artifacts | Artifact/workspace services |
| Tasks & Automations | One-time, scheduled and conditional work | Orchestrator + scheduler |
| Developer | Provider, API, diagnostics, workflow builder | Developer Platform |
| Settings | Identity, privacy, permissions, devices, models | Security/admin services |

## 3. Chat และ Conversation

- สร้าง แก้ชื่อ ลบ เก็บถาวร และค้นหาแชต
- Streaming คำตอบแบบสด
- Markdown, ตาราง, สูตรคณิตศาสตร์ และ code blocks
- แก้ไขข้อความ, regenerate และ branch conversation
- Pin, share, export และ conversation history
- Sync ข้ามอุปกรณ์และโหมด local-first
- Offline queue และ conflict-safe synchronization
- Conversation provenance และ audit events

## 4. Multimodal

- ข้อความ
- รูปภาพและการวิเคราะห์ภาพ
- กล้องและภาพหน้าจอ
- PDF, Word, Excel, CSV และไฟล์โค้ด
- เสียงพูด, transcription และอ่านคำตอบ
- สร้างและแก้ไขรูปภาพ
- Media permission แยกตาม workspace
- จำกัดชนิดไฟล์ ขนาด และ retention policy

## 5. Voice Mode

- สนทนาเสียงแบบ realtime
- หยุดหรือพูดแทรกได้
- Transcript อัตโนมัติ
- เลือกเสียงและภาษา
- เรียก tools และ agents ด้วยเสียง
- รองรับ speech-to-speech และ chained STT → reasoning → TTS
- แสดงสถานะ microphone, listening, thinking, tool use และ speaking
- ใช้ approval เดียวกับ text workflow

อ้างอิง: [Voice agents](https://developers.openai.com/api/docs/guides/voice-agents)

## 6. Projects และ Workspace

- รวมแชต ไฟล์ คำสั่ง และ memory ตามโปรเจกต์
- Project instructions
- Workspace knowledge
- สมาชิกและสิทธิ์
- Timeline และ audit history
- Import/export และ backup
- รองรับหลาย folder
- Workspace templates
- Archive, restore และ data boundary ที่ชัดเจน

อ้างอิง: [ChatGPT desktop app](https://learn.chatgpt.com/docs/app)

## 7. Memory

- จำ preference และบริบทระยะยาว
- Memory แยกตามผู้ใช้และโปรเจกต์
- เปิด/ปิด ลบ และตรวจสอบ memory ได้
- ไม่บันทึก secrets
- สรุปและลดขนาด memory อัตโนมัติ
- Provenance ว่าข้อมูลมาจากไหน
- Memory candidate ต้องผ่าน policy ก่อน persist
- รองรับ expiry, pin, forget และ export

## 8. Files และ Knowledge

- อัปโหลดหลายไฟล์
- OCR และ document parsing
- Semantic + keyword search
- Vector index
- Citation ไปยังไฟล์ต้นฉบับ
- Data analysis และสร้างกราฟ
- ใช้ Workspace Knowledge ที่ Research OS มีอยู่แล้วเป็น owner
- Deduplication, checksum และ version history
- Permission-aware retrieval

อ้างอิง: [File search](https://developers.openai.com/api/docs/guides/tools-file-search)

## 9. Web Search และ Deep Research

- ค้นเว็บปัจจุบัน
- แสดง citations
- เปรียบเทียบหลายแหล่ง
- Deep research แบบหลายขั้นตอน
- รายงานพร้อมหลักฐาน
- จำกัด domain และวันที่
- Research timeline และ source library
- Source quality scoring และ conflict flags
- Snapshot/refresh policy สำหรับข้อมูลที่เปลี่ยนตามเวลา

อ้างอิง: [Web search](https://developers.openai.com/api/docs/guides/tools-web-search)

## 10. Agents

- สร้าง Custom Agent
- Instructions, model, tools และ knowledge ของแต่ละ agent
- Multi-agent orchestration
- Agent handoff
- Retry, pause, resume และ cancel
- Human approval ก่อน action สำคัญ
- Agent templates และ Agent Store ภายใน
- Visual workflow builder
- Typed inputs/outputs และ dependency graph
- Run timeline, diagnostics และ replay evidence

Research OS V2 มีฐาน Agent Platform และ Orchestrator อยู่แล้ว V3 จะต่อยอดโดยไม่สร้าง owner ใหม่

อ้างอิง: [Agent Builder](https://learn.chatgpt.com/api/docs/guides/agent-builder)

## 11. Brain Skills Layer

Brain Skills เป็นโมดูลความสามารถ ไม่อ้างว่าเป็นสมองหรือจิตสำนึกจริง

| Skill | หน้าที่ | Guard |
| --- | --- | --- |
| Planning | แบ่งเป้าหมายเป็นขั้นตอนและ dependency | จำกัดความลึก/จำนวนงาน |
| Reasoning | วิเคราะห์ข้อมูลและข้อจำกัด | ต้องแยก fact/inference |
| Memory | เลือก context ที่เกี่ยวข้อง | ห้ามเก็บ secrets |
| Knowledge | ค้นหลักฐานและ provenance | permission-aware |
| Tool Selection | เลือกเครื่องมือและ provider | capability + health checks |
| Agent Coordination | มอบหมายงานและ handoff | Adaptive capacity |
| Critic | ตรวจความครบถ้วนและความขัดแย้ง | ไม่แก้ผลลัพธ์โดยไร้ audit |
| Safety | ตรวจสิทธิ์และความเสี่ยง | approval ก่อน write |
| Learning | สร้าง lesson candidate จาก evidence | ไม่ self-modify โดยอัตโนมัติ |
| Provider Routing | เลือก local/compatible provider | fallback + budget limits |

### Adaptive 6⁶

- ระดับ 1: Master Orchestrator
- ระดับ 2: Domain Orchestrators สูงสุด 6
- ระดับ 3: Team Leads สูงสุด 6 ต่อ domain
- ระดับ 4: Specialist Agents สูงสุด 6 ต่อ team
- ระดับ 5: Worker Agents สูงสุด 6 ต่อ specialist
- ระดับ 6: Tool/Validator Workers สูงสุด 6 ต่อ worker

6⁶ คือ **capacity model** ไม่ใช่จำนวน process ที่เปิดพร้อมกัน Scheduler ต้องใช้ budget, queue, priority, readiness และ backpressure เพื่อเลือกจำนวน worker จริง

## 12. Tools, Plugins และ Connectors

- Function calling
- Web search
- File search
- Code execution
- Image generation
- Computer/browser control
- MCP servers
- Google Drive, Calendar, GitHub และบริการอื่น
- Read-only/write permission แยกกัน
- ขออนุมัติก่อนส่งข้อความ ลบ หรือแก้ข้อมูล
- Connector health, scopes และ revoke controls
- Prompt-injection isolation และ output validation

อ้างอิง: [Using tools](https://developers.openai.com/api/docs/guides/tools)

## 13. Canvas และ Artifacts

- แก้เอกสารข้างแชต
- Code editor พร้อม preview
- ตารางและ spreadsheet
- Charts และ dashboards
- Image workspace
- Version history
- Comments และ collaboration
- Export เป็น PDF, DOCX, XLSX, PPTX และไฟล์โค้ด
- Artifact provenance และ reproducible generation
- Preview sandbox แยกจาก production data

## 14. Tasks และ Automation

- งานครั้งเดียว
- งานตามเวลา
- งานประจำ
- Conditional monitoring
- Notification
- Pause/resume
- Run history
- Approval ก่อน external action
- Retry policy, timeout และ idempotency
- Quiet hours และ per-user timezone

## 15. Model Gateway

- OpenAI
- OpenAI-compatible providers
- Local models
- เลือก model อัตโนมัติตามงาน
- Fallback และ retry
- Budget/usage limits
- Provider health
- เปลี่ยน provider โดยไม่กระทบ UI
- Capability negotiation
- Provider secrets อยู่นอก source code

## 16. Security และ Administration

- OAuth/OIDC
- Device sessions
- Role-based permissions
- Workspace isolation
- Encryption
- Secret vault
- Rate limiting
- Audit log
- Data retention/export/delete
- Moderation และ safety policies
- Approval gate สำหรับ write actions
- Signed identity boundary
- Incident diagnostics ที่ redact secrets

## 17. ทุกแพลตฟอร์ม

- Windows `.exe`
- Android `.apk/.aab`
- iOS unsigned `.ipa` สำหรับ Sideloadly
- iOS signed `.ipa`
- macOS `.app/.dmg`
- Linux bundle/AppImage
- Web/PWA

ทุก artifact ต้องผูกกับ exact commit SHA, version, checksum และ build evidence

## 18. ลำดับสร้าง

1. Chat Shell + conversation streaming
2. Project, files และ memory
3. Model/provider gateway
4. Web/file search พร้อม citations
5. Voice และ image tools
6. Agents, Brain Skills, MCP และ approvals
7. Canvas, artifacts และ data analysis
8. Tasks/automations
9. Mobile/desktop builds
10. Production security และ multi-user sync

## 19. Definition of Done ต่อ Increment

- ไม่ทำให้ V1/V2 routes และ local data boundary เสีย
- มี unit/integration tests
- มี permission และ negative tests
- มี migration/rollback notes
- มี accessibility และ cross-platform checks ตาม scope
- เอกสาร API/UI/operations อัปเดตพร้อม code
- PR แสดง exact-SHA evidence
- ไม่มี release หรือ production deployment โดยอัตโนมัติ

## 20. เป้าหมาย

**Research OS V3 – AI Workspace** รักษา Research OS V2 เป็นฐานเสถียร และเพิ่มความสามารถแบบโมดูลทีละ increment โดย UI จัดเป็นแท็บที่เข้าใจง่าย แต่ Core/API/Data ownership ยังเป็น One Truth ชุดเดียว
