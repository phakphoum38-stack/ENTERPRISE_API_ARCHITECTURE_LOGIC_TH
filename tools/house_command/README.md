# House Command Workflow

Workflow นี้เป็นประตูรับคำสั่งของบ้าน โดยรับเฉพาะคำสั่งที่ประกาศไว้ล่วงหน้าเท่านั้น ไม่รับข้อความ shell แบบอิสระ

## คำสั่งที่รองรับ

| คำสั่ง | หน้าที่ |
|---|---|
| `house-status` | อ่าน `MISSION_REPORT.md`, `HOUSE_LOG.md` และ `HOUSE_STRUCTURE.md` เพื่อสร้างรายงานบ้าน |
| `validate` | ตรวจความถูกต้องของ Research Artifacts |
| `test` | รัน Unit Tests ของ Research Curator และ Research OS API |
| `graph` | Export Knowledge Graph เป็น JSON และ Mermaid |
| `all` | รันทุกคำสั่งข้างต้นตามลำดับ |

## วิธีเรียกจาก GitHub

หลัง Workflow อยู่บน Default Branch:

1. เปิดแท็บ **Actions**
2. เลือก **House Command**
3. กด **Run workflow**
4. เลือกคำสั่ง
5. ใส่หมายเหตุได้ตามต้องการ

ผลลัพธ์จะแสดงใน Job Summary และถูกเก็บเป็น Workflow Artifact เป็นเวลา 14 วัน

## วิธีเรียกผ่าน GitHub API

ส่ง `repository_dispatch` event ชนิด `house-command` พร้อม `client_payload.command`

ตัวอย่าง Payload:

```json
{
  "event_type": "house-command",
  "client_payload": {
    "command": "house-status",
    "note": "ตรวจบ้านก่อนเริ่มงาน"
  }
}
```

## ขอบเขตความปลอดภัย

- ใช้สิทธิ์ `contents: read` เท่านั้น
- ไม่ Commit, Push, Merge หรือ Publish
- ไม่รับคำสั่ง shell จากผู้ใช้
- ทุกคำสั่งต้องอยู่ใน Allowlist ของ `dispatcher.py`
- คำสั่งที่ไม่รู้จักจะจบด้วย Exit Code 64
- ใช้ Mock Provider ในงานทดสอบ จึงไม่ต้องเปิดเผย API Key

## งานถัดไป

เมื่อเจ้าของบ้านอนุมัติ จึงค่อยเพิ่ม Workflow ฝั่ง Write สำหรับสร้าง Repository Draft หรือ Pull Request โดยต้องแยกสิทธิ์และมี Review Gate ต่างหาก
