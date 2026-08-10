# Research OS File Ownership Boundary

สถานะ: V3 Unified / independent owner / boundary-only

## เป้าหมาย

แยกระบบเจ้าของไฟล์ออกจาก Cyber Web Security อย่างชัดเจน เพื่อไม่ให้มาตรฐานเว็บไซต์/API กลายเป็นแหล่งอำนาจของ filesystem ownership หรือ ACL โดยไม่ตั้งใจ

## Owner

`tools/research_os_api/v2_file_ownership_boundary.py`

Owner: `FileOwnershipBoundary`

Contract: `research-os-file-ownership-boundary-v1`

## ขอบเขตที่ owner นี้ถือ

- file ownership policy boundary
- filesystem ACL boundary
- document ownership boundary
- storage authorization handoff

## สิ่งที่ยังไม่ทำ

Owner ปัจจุบันเป็น `boundary_only` จึงยังไม่ใช่ Windows/Linux ACL backend และไม่อ้างว่ามีสิทธิ์เปลี่ยน owner จริง

- ไม่เปลี่ยน file owner
- ไม่ grant/revoke ACL
- ไม่อ่าน private file metadata เอง
- ไม่แก้ document ownership
- ไม่ใช้ Cyber Web Security เป็น authorization source

หากเพิ่มการเปลี่ยน owner/ACL ในอนาคต ต้องมี dedicated backend, explicit authorization, audit evidence และ test แยกจาก Cyber Web Security

## Cyber Web Security boundary

Cyber Web Security และ File Ownership เป็นคนละ owner:

| Responsibility | CyberWebSecurityStandard | FileOwnershipBoundary |
|---|---:|---:|
| HTTPS / TLS / Certificates | Owner | No |
| CSP / HSTS / CORS | Owner | No |
| API input/auth/session security | Owner | No |
| Secret-safe logging | Owner | No |
| File ownership policy boundary | No | Owner |
| Filesystem ACL boundary | No | Owner |
| Document ownership boundary | No | Owner |
| Change actual file owner today | No | No — dedicated backend required |
| Grant actual filesystem ACL today | No | No — dedicated backend required |

## Cross-owner invariants

- `separate_from_cyber_web_security = true`
- `shared_authority = false`
- `cyber_may_change_file_owner = false`
- `cyber_may_grant_file_acl = false`
- `file_owner_may_override_cyber_policy = false`
- `file_owner_may_disable_security_controls = false`

## Unified Master

`UnifiedMasterOrchestrator` compose ทั้งสอง owner แต่ไม่รวม authority ของสองระบบเข้าด้วยกัน

`status()` แสดง `cyber_web_security` และ `file_ownership` เป็นคนละส่วน

`plan()` แสดงแผนของแต่ละ owner แยกกัน และยืนยันว่า planning ไม่เปลี่ยน file owner หรือ ACL

## Testing

- `test_v2_cyber_web_standard.py` ตรวจว่า Cyber ไม่มี file-owner/ACL authority
- `test_v2_file_ownership_boundary.py` ตรวจว่า File Ownership ไม่มี Cyber authority และไม่มี mutation backend โดยปริยาย
- `test_unified_master_orchestrator.py` ตรวจ cross-owner invariants ทั้งสองทิศทาง
