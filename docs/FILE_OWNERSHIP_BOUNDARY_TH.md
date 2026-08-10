# Research OS File Ownership Boundary

สถานะ: V3 Unified / boundary-only

## ขอบเขต

File Ownership มีหน้าที่เพียง 3 ส่วนเท่านั้น:

- File Ownership
- Filesystem ACL
- Document Ownership

Owner: `FileOwnershipBoundary`

Contract: `research-os-file-ownership-boundary-v2`

ไฟล์หลัก:

- `tools/research_os_api/v2_file_ownership_boundary.py`

## สถานะปัจจุบัน

ระบบนี้เป็น `boundary_only` และยังไม่เปลี่ยน owner หรือ ACL จริง

- `changes_file_owner = false`
- `grants_file_acl = false`
- `changes_document_owner = false`

ไม่มี scope อื่นนอกเหนือจากสามรายการข้างต้น

## Testing

`test_v2_file_ownership_boundary.py` ตรวจว่า manifest และ plan มีเพียง:

1. `file_ownership`
2. `filesystem_acl`
3. `document_ownership`
