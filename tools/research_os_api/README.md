# Research OS API

API กลางแบบ **Provider-agnostic** สำหรับเชื่อม Research OS, AI Providers, Research Curator และ Knowledge Repository โดยไม่ผูก Core กับผู้ให้บริการรายเดียว

## สถานะ

- Version: `0.1.0`
- Runtime: Python standard library
- Default provider: `mock`
- Persistence: Preview-only ผ่าน API; การเขียน Repository ต้องผ่าน Git Publisher และ Review Gate

## เริ่มรัน

```bash
python tools/research_os_api/server.py --host 127.0.0.1 --port 8787
```

ตรวจสถานะ:

```bash
curl http://127.0.0.1:8787/health
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

## Endpoints

| Method | Endpoint | หน้าที่ |
|---|---|---|
| GET | `/health` | ตรวจสถานะ API |
| GET | `/v1/providers` | รายชื่อ Provider Adapters |
| GET | `/v1/browser-use/status` | ตรวจสถานะ Browser Use Cloud connector |
| POST | `/v1/browser-use/connect` | สร้าง Browser Use Cloud browser session ผ่าน backend |
| POST | `/v1/browser-use/disconnect` | หยุด Browser Use Cloud browser session |
| POST | `/v1/ai/generate` | เรียก AI ผ่าน Adapter |
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

### Browser Use Cloud

ตั้งค่า key เฉพาะฝั่ง backend/service แล้วให้ Flutter กด Connect ผ่าน API:

```bash
export BROWSER_USE_API_KEY="..."
```

Research OS เก็บ Browser Use API key และ CDP URL เต็มไว้ฝั่ง backend เท่านั้น; UI เห็นเฉพาะสถานะ session และ browser id.

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
