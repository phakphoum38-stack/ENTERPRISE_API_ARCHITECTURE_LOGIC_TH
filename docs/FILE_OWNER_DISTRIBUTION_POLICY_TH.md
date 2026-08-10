# Research OS File Owner Distribution Policy

สถานะ: V3 Unified / standalone owner package

## เป้าหมาย

ชุดที่ส่งให้ผู้ใช้ระบบเจ้าของไฟล์ต้องเป็นชุดขั้นต่ำและมีเฉพาะความสามารถด้านเจ้าของไฟล์/สิทธิ์ไฟล์ตาม contract ที่กำหนดไว้เท่านั้น

## Runtime allowlist

ชุด runtime อนุญาตเพียง:

- `tools/research_os_api/v2_file_ownership_boundary.py`

การ export ใช้ exact allowlist จึงไม่ copy ไฟล์อื่นจาก Research OS โดยอัตโนมัติ

## Package guard

`tools/research_os_api/v2_owner_package.py`

ทำหน้าที่:

- ตรวจว่ารายการไฟล์ตรง exact allowlist
- ปฏิเสธไฟล์ส่วนเกิน
- สแกนเนื้อหา source ก่อน export
- ปฏิเสธ marker ของระบบภายนอกที่ไม่อยู่ในขอบเขต owner package
- สร้าง `OWNER_PACKAGE_MANIFEST.json`
- export ไป destination ใหม่เท่านั้น

## Owner package invariants

- ไม่พ่วง Unified Master
- ไม่พ่วง provider/search layer
- ไม่พ่วง browser/network feature
- ไม่พ่วงระบบเสริมจาก package อื่น
- ไม่สร้าง permission backend โดยอัตโนมัติ
- ไม่เปลี่ยน owner/ACL ระหว่าง export
- ถ้ามีไฟล์นอก allowlist ให้ fail closed

## Integration

Research OS ฉบับเต็มสามารถประกอบ owner นี้ผ่าน Unified Master ได้ แต่ standalone owner package ไม่ต้องพก integration owner หรือระบบอื่นติดไปด้วย

การแยกระหว่าง subsystem อยู่ใน integration contract ภายนอก ไม่เขียน dependency ย้อนกลับเข้าไฟล์ owner runtime
