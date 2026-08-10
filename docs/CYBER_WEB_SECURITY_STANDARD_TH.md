# Research OS Cyber Web Security Standard

สถานะ: V3 Unified / separate owner / review-first

## เป้าหมาย

กำหนดมาตรฐาน Cybersecurity สำหรับเว็บไซต์และ API ของ Research OS โดยแยกความรับผิดชอบออกจากระบบเจ้าของไฟล์/สิทธิ์ไฟล์อย่างชัดเจน

## Baseline

- OWASP ASVS 5.0.0 — ใช้ Level 2 เป็น production baseline และเลือก Level 3 สำหรับ surface ที่มีความอ่อนไหวสูง
- OWASP Top 10:2025 — ใช้เป็น risk catalog และ regression awareness ไม่ใช้แทน ASVS
- NIST SP 800-218 SSDF 1.1 Final — Secure SDLC, supply chain, build, release และ vulnerability management
- NIST SP 800-52 Rev.2 — TLS/certificate/secure transport baseline

หมายเหตุ: NIST SSDF 1.2 / SP 800-218 Rev.1 ยังเป็น Draft ณ baseline นี้ จึงยังไม่ใช้แทน Final 1.1 เป็นข้อบังคับหลัก

## Security owner

`tools/research_os_api/v2_cyber_web_standard.py`

Owner: `CyberWebSecurityStandard`

หน้าที่:

- Web application security
- API security
- Browser security headers
- Authentication/session/OAuth boundary
- TLS/certificate policy
- Secret-safe logging
- Supply-chain / build provenance security
- Evidence-based assessment

## File ownership owner

ระบบเจ้าของไฟล์เป็น owner แยกต่างหาก Cyber Web Security Standard ไม่เป็น source of truth ของ file ownership และไม่มีอำนาจดังต่อไปนี้:

- อ่าน owner ของไฟล์เพื่อใช้เป็น authorization decision
- เปลี่ยน owner ของไฟล์
- grant/revoke filesystem ACL
- เปลี่ยน document ownership
- override สิทธิ์ที่ระบบเจ้าของไฟล์กำหนด

ในทางกลับกัน ระบบเจ้าของไฟล์ก็ไม่สามารถ override Cyber Web Security policy ได้โดยอัตโนมัติ ทั้งสองระบบเชื่อมกันได้เฉพาะ explicit contract ที่กำหนดไว้เท่านั้น

## Boundary matrix

| Responsibility | Cyber Web Security | File Ownership |
|---|---:|---:|
| HTTPS/TLS | Owner | No |
| CSP/HSTS/CORS | Owner | No |
| API input validation | Owner | No |
| Authentication/session security | Owner | No |
| Secret redaction/logging | Owner | No |
| Supply-chain/provenance checks | Owner | No |
| File owner identity | No | Owner |
| File ACL | No | Owner |
| Document ownership | No | Owner |
| Filesystem authorization source | No | Owner |

## Core controls

### Transport

- Public web surface ต้องใช้ HTTPS
- TLS 1.3 preferred/support; TLS 1.2 ใช้เฉพาะ compatibility ที่จำเป็น
- Certificate/hostname validation ต้องเชื่อถือได้
- Local loopback mode ไม่ถูกบังคับให้ใช้ public HTTPS/HSTS

### Browser

- Content-Security-Policy
- HSTS สำหรับ public HTTPS
- anti-clickjacking ผ่าน CSP `frame-ancestors` หรือ equivalent
- `X-Content-Type-Options: nosniff`
- Referrer-Policy
- Permissions-Policy

### API

- Explicit CORS allowlist
- Schema/input validation
- Rate/resource abuse controls สำหรับ exposed API
- Safe error handling

### Identity

- Strong authentication เมื่อจำเป็น
- Server-side authorization + least privilege
- Session/token expiry and scope validation
- Secure/HttpOnly/SameSite cookie policy เมื่อใช้ cookie
- OAuth/OIDC callback validation และห้าม persist secret query values

### Data / Logs

- API/UI status ห้ามเปิดเผย secret
- Data minimization
- Security audit logs ต้อง redact secret
- Production security events ต้องมี response ownership

### Supply Chain

- Dependency governance
- Exact revision/build provenance
- Trusted production signing เมื่อมี public artifact
- Vulnerability triage/remediation process

## Assessment model

`CyberWebSecurityStandard.assess(evidence, deployment_mode=...)`

รองรับ:

- `public`
- `local_loopback`

Assessment เป็น read-only และ evidence-based:

- ไม่ auto-remediate
- ไม่เปลี่ยน file owner
- ไม่ grant ACL
- ไม่ deploy
- ไม่ release

## Unified Master integration

`GET /v2/master` ผ่าน `UnifiedMasterOrchestrator.status()` จะแสดง owner และ Cyber Web Security manifest แยกจาก file ownership boundary

`UnifiedMasterOrchestrator.assess_cyber_web_security(...)` ใช้ตรวจ evidence ได้โดยไม่แตะระบบเจ้าของไฟล์

## Invariants

- `cyber_security_separate_from_file_ownership = true`
- `cyber_security_can_change_file_owner = false`
- `cyber_security_can_grant_file_acl = false`
- `permission_grant_authority = false`
- `automatic_remediation = false`
- `automatic_merge_release_deploy = false`
