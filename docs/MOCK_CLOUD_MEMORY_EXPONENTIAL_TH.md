# Mock Cloud และ Memory แบบยกกำลัง

## เป้าหมาย

ใช้ GitHub Actions เป็น cloud orchestration ฟรี/ต้นทุนต่ำ โดยแยก 2 โหมดชัดเจน:

1. **Simulated cloud** — รัน mock cloud ใน GitHub runner เอง ยิงผ่าน `localhost` ไม่กิน Browser Use Cloud quota
2. **Real cloud** — ยิง Browser Use Cloud จริงเฉพาะตอนตั้งใจ ด้วย `connect_cloud=true` และ `BROWSER_USE_API_KEY`

## Flow ที่ปลอดภัย

```text
GitHub Actions YAML
  → Browser Use Cloud simulator หรือ Browser Use Cloud จริง
  → Research OS API backend
  → Flutter client contract / widget tests
  → Memory evidence
```

Flutter ไม่ถือ secret และไม่เห็น full CDP URL:

- `BROWSER_USE_API_KEY` อยู่ที่ backend/GitHub Secrets
- `cdpUrl` เต็มอยู่ใน backend local session เท่านั้น
- UI เห็นเฉพาะ `connected`, `browser_id`, `cdp_host`, `api_base_host`

## Quota analysis

| โหมด | ยิง Browser Use Cloud จริง | ใช้ GitHub Actions minutes | ใช้ Browser Use quota |
| --- | --- | --- | --- |
| `connect_cloud=false` | ไม่ | ใช่ | ไม่ |
| `connect_cloud=true` | ใช่ | ใช่ | ใช่ |

ค่าเริ่มต้นควรเป็น `connect_cloud=false` เพื่อทดสอบเต็ม flow โดยไม่กิน quota จาก cloud provider.

## Memory แบบยกกำลัง

แนวคิด “ยกกำลัง” ไม่ควรหมายถึงเปิดทุก agent/cloud พร้อมกัน แต่ควรเป็น memory graph ที่ขยายตามหลักฐานจริง ตั้งแต่ Run → Branch → PR → Release → Product → Adaptive factory memory.

ถ้าคิดเป็น “6^6” ให้ใช้เป็น matrix ของมุมมอง เช่น 6 domains × 6 evidence types × 6 confidence levels × 6 actions × 6 owners × 6 retention windows ไม่ใช่จำนวน process ที่ต้องเปิดพร้อมกัน.

หลักการใช้งานจริง:

- ทุก run ต้องเขียน evidence แบบสั้น อ่านง่าย
- mock cloud ใช้เป็น default gate
- real cloud ใช้เฉพาะ release/high-confidence smoke
- memory ที่ยังไม่มี evidence ให้ถือว่าเป็น assumption ไม่ใช่ fact
