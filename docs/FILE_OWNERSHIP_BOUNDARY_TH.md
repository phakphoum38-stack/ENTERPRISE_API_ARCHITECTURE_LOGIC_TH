# Research OS File Ownership Boundary

สถานะ: V3 Unified / independent owner / boundary-only

## เป้าหมาย

กำหนดขอบเขตระบบเจ้าของไฟล์ให้เป็นโมดูลเฉพาะทางที่ดูแลเฉพาะ file ownership, filesystem ACL, document ownership และ storage authorization handoff โดยไม่พ่วง subsystem อื่นเข้ามาในชุดเจ้าของไฟล์

## Owner

`tools/research_os_api/v2_file_ownership_boundary.py`

Owner: `FileOwnershipBoundary`

Contract: `research-os-file-ownership-boundary-v2`

## ขอบเขต

- file ownership policy boundary
- filesystem ACL boundary
- document ownership boundary
- storage authorization handoff

## สถานะ implementation

Owner ปัจจุบันเป็น `boundary_only` จึงยังไม่ใช่ Windows/Linux ACL backend และไม่อ้างว่ามีสิทธิ์เปลี่ยน owner จริง

- ไม่เปลี่ยน file owner
- ไม่ grant/revoke ACL
- ไม่อ่าน private file metadata เอง
- ไม่แก้ document ownership

หากเพิ่มการเปลี่ยน owner/ACL ในอนาคต ต้องมี dedicated backend, explicit authorization, audit evidence และ regression tests ของระบบเจ้าของไฟล์เอง

## Standalone distribution

ชุดที่นำไปใช้เป็น File Owner Package ใช้ exact allowlist และมี runtime เพียง:

- `tools/research_os_api/v2_file_ownership_boundary.py`

ไฟล์ประกอบจาก subsystem อื่นไม่ถูก copy เข้า package นี้

## Invariants

- `implementation_state = boundary_only`
- `operating_system_acl_backend = false`
- `changes_file_owner = false`
- `grants_file_acl = false`
- `reads_private_file_metadata = false`
- mutation ในอนาคตต้องใช้ dedicated backend
- mutation ในอนาคตต้องมี explicit authorization

## Testing

- `test_v2_file_ownership_boundary.py` ตรวจ contract และ read-only boundary
- `test_v2_owner_package.py` ตรวจ exact allowlist, dependency isolation และ export contents
