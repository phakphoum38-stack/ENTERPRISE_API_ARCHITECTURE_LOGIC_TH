# Architecture Contract Boundary

สถานะ: Foundation Contract

เอกสารชุดนี้เป็นสะพาน Contract ระหว่าง Architecture Source of Truth กับ Repository ที่นำไป Implementation เช่น `phakphoum38-stack/flutter` และ Runner ในอนาคต

## หลักการ

1. Architecture Contract เป็น Source of Truth
2. Implementation ต้อง pin Contract Version ที่รองรับ
3. Contract เป็น Immutable ภายใน Version ที่ publish แล้ว
4. การเปลี่ยน breaking change ต้องออก Contract Version ใหม่
5. Implementation สามารถแตก branch/version ได้โดยไม่แก้ทับ Architecture Contract

## Contract Areas

- Workflow Definition
- Execution Plan / Snapshot
- Event Schema
- Runner Protocol
- Runner Capability
- Error / Result Contract
- Artifact Reference
- Secret Reference
- Version / Compatibility Policy

## Boundary

```text
Architecture Source of Truth
          │
          ▼
     Contract Version
          │
   ┌──────┴──────┐
   ▼             ▼
Tooling        Runner
flutter        runtime
```

Implementation ที่ไม่ตรง Contract ต้องถูกปฏิเสธโดย Compatibility Gate ก่อน release
