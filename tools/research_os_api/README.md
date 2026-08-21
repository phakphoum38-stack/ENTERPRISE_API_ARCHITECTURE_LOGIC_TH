# Research OS API

API กลางแบบ **Provider-agnostic** สำหรับเชื่อม Research OS, AI Providers, Research Curator และ Knowledge Repository โดยไม่ผูก Core กับผู้ให้บริการรายเดียว

## สถานะ

- Version: `0.1.0`
- Runtime: Python standard library
- Default provider: `mock`
- Persistence: Preview-only ผ่าน API; การเขียน Repository ต้องผ่าน Git Publisher และ Review Gate

## เริ่มรัน

### Windows — Local Research OS พร้อม Friend Service

สำหรับ Research OS Web ที่ใช้ `RESEARCH_OS_AI_ROUTE=friend` ให้ใช้ launcher นี้แทนการเปิด API อย่างเดียว เพราะ Friend Service ที่ `127.0.0.1:8790` เป็น dependency ของ research route:

```powershell
.\scripts\start-research-os-local.ps1
```

Launcher จะ:

1. สร้าง data/log directories
2. ตรวจ `http://127.0.0.1:8790/owner/health`
3. ถ้ายังไม่ทำงาน จะ start `owner_special/scripts/run_friend_service.py`
4. รอจน health เป็น `ok`
5. ตั้ง `RESEARCH_OS_FRIEND_URL` และ `RESEARCH_OS_AI_ROUTE=friend`
6. จึง start Research OS API ที่ `8787`
7. เมื่อรันแบบ foreground จะ cleanup Friend Service ตอนจบ

Background mode:

```powershell
.\scripts\start-research-os-local.ps1 -Background
```

ตรวจสถานะ:

```powershell
curl http://127.0.0.1:8787/health
curl http://127.0.0.1:8790/owner/health
```

> ไม่ควรแก้ปัญหา `Connection refused` ด้วยการ fallback ไป `mock` เพราะจะทำให้ research response อาจกลายเป็น mock/echo ที่ไม่ใช่ผลจาก Friend runtime จริง

### API อย่างเดียว

ถ้าตั้งใจใช้ API โดยไม่ใช้ Friend route:

```bash
python tools/research_os_api/server.py --host 127.0.0.1 --port 8787
```

วิเคราะห์บทสนทนา:

```bash
curl -X POST http://127.0.0.1:8787/v1/conversations/analyze \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Provider-independent architecture",
    "conversation": "Research OS ควรมี API กลางและเปลี่ยน AI Provider ได้",
    "tags": ["api", "architecture"]
  }'
```

ทดลอง AI Adapter โดยไม่ใช้ API Key:

```bash
curl -X POST http://127.0.0.1:8787/v1/ai/generate \
  -H 'Content-Type: application/json' \
  -d '{"provider":"mock","prompt":"วิเคราะห์แนวคิดนี้"}'
```

## Friend Service

Canonical entrypoint:

```bash
python owner_special/scripts/run_friend_service.py --owner-id owner --host 127.0.0.1 --port 8790
```

Health endpoint:

```text
GET http://127.0.0.1:8790/owner/health
```

Chat endpoint requires the Owner identity headers and is consumed internally by `/v1/ai/generate` when `RESEARCH_OS_AI_ROUTE=friend`.

## Endpoints

| Method | Endpoint | หน้าที่ |
|---|---|---|
| GET | `/health` | ตรวจสถานะ API |
| GET | `/v1/providers` | รายชื่อ Provider Adapters |
| POST | `/v1/ai/generate` | เรียก AI ผ่าน Adapter หรือ Friend route |
| POST | `/v1/conversations/analyze` | สร้าง Artifact Preview |
| GET | `/v1/knowledge/artifacts` | อ่าน Artifact Index |
| GET | `/v1/knowledge/graph` | อ่าน Knowledge Graph |

ดูสัญญาเต็มใน `openapi.yaml`

## Provider Configuration

### Mock

```bash
export RESEARCH_OS_PROVIDER=mock
```

### OpenAI-compatible หรือ Local LLM

รองรับ endpoint ที่ใช้ Chat Completions-compatible contract เช่น Local gateway หรือ provider adapter ภายในองค์กร

```bash
export RESEARCH_OS_PROVIDER=openai-compatible
export RESEARCH_OS_OPENAI_ENDPOINT="http://localhost:11434/v1/chat/completions"
export RESEARCH_OS_OPENAI_MODEL="local-model"
export RESEARCH_OS_OPENAI_API_KEY="optional"
```

### Anthropic

```bash
export RESEARCH_OS_PROVIDER=anthropic
export RESEARCH_OS_ANTHROPIC_API_KEY="..."
export RESEARCH_OS_ANTHROPIC_MODEL="..."
```

### Gemini

```bash
export RESEARCH_OS_PROVIDER=gemini
export RESEARCH_OS_GEMINI_API_KEY="..."
export RESEARCH_OS_GEMINI_MODEL="..."
```

ชื่อโมเดลจริงต้องกำหนดผ่าน Environment Variable เพื่อไม่ฝัง dependency กับรุ่นใดใน Core

## Security Boundary

API รุ่นแรก bind ที่ `127.0.0.1` โดยค่าเริ่มต้นและยังไม่มีระบบ Authentication จึง **ห้ามเปิดออกอินเทอร์เน็ตโดยตรง**

ก่อนใช้ในเครือข่ายหรือ Production ต้องเพิ่มอย่างน้อย:

- Authentication และ Authorization
- TLS
- Secret manager
- Rate limiting
- Request size limit
- Audit log
- CORS policy
- Network allowlist

## Governance

- API วิเคราะห์และ Preview ได้ แต่ไม่ Commit หรือ Merge โดยตรง
- การเขียน Repository ต้องผ่าน Git Publisher
- AI Provider ไม่มีสิทธิ์เปลี่ยน Ownership, License หรือ Governance
- Owner เป็นผู้ตัดสินใจขั้นสุดท้าย
