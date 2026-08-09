# Research OS v1 — คู่มือสำหรับผู้ใช้ทั่วไป

> เอกสารนี้สำหรับผู้ใช้ทั่วไปเท่านั้น
> เป้าหมายเวอร์ชัน: Research OS 1.0.0
> แพลตฟอร์มหลัก: Windows x64
> Developer, source code, build, CI/CD และ debugging แยกไว้ใน `DEVELOPER_GUIDE_TH.md`

Research OS เป็น Enterprise Workspace แบบ local-first ที่รวม AI, Knowledge, Multi-Agent, GitHub, Google Workspace และ Local Service ไว้ในโปรแกรมเดียว โดยผู้ใช้ทั่วไปไม่จำเป็นต้องติดตั้ง Python, .NET SDK, Flutter หรือเครื่องมือพัฒนาเพิ่มเติม

---

## 1. ระบบที่ผู้ใช้ทั่วไปจะพบ

Research OS V1 มีส่วนหลักดังนี้

- Home — หน้าภาพรวมและสถานะระบบ
- AI Chat — สนทนากับ AI provider ที่ตั้งค่าไว้
- Agent Center — ใช้ Multi-Agent และ orchestration
- Library — ดู Research Artifacts และข้อมูลความรู้
- Knowledge Graph — ดูความสัมพันธ์ของข้อมูลและองค์ความรู้
- GitHub — ใช้งานส่วนเชื่อมต่อ GitHub ที่ระบบอนุญาต
- Google Workspace — Drive, Docs, Sheets, Calendar, Gmail และ Workspace
- Local API & Service — ดูสถานะ backend ภายในเครื่อง
- System Monitor — ตรวจสุขภาพระบบ
- Settings — ตั้งค่า Theme, API Base URL และการตั้งค่าที่ UI รองรับ

ระบบเบื้องหลังที่ผู้ใช้ไม่ต้องจัดการเอง ได้แก่ Windows Service, Local API, bundled Python runtime, ServiceHost, Memory/Knowledge storage, Agent Runtime, Router, Task Queue, Event Bus, Shared Context, permission model และ confirmation policy

---

# ส่วน A — การติดตั้ง

## 2. ความต้องการของระบบ

- Windows 10 หรือ Windows 11 แบบ 64-bit
- สิทธิ์ Administrator ตอนติดตั้ง
- พื้นที่ว่างอย่างน้อยประมาณ 500 MB ขึ้นไป
- อินเทอร์เน็ตเฉพาะฟังก์ชันที่ต้องใช้บริการภายนอก เช่น GitHub, Google Workspace หรือ AI provider

ผู้ใช้ทั่วไปไม่ต้องติดตั้ง Python หรือ .NET SDK เอง เพราะ installer รวม runtime ที่จำเป็นไว้แล้ว

## 3. ไฟล์ติดตั้ง

รูปแบบไฟล์:

```text
Research-OS-Setup-<version>-x64.exe
```

ให้ใช้ไฟล์จาก Research OS Release ที่ผ่าน Installer Validation แล้วเท่านั้น

> หมายเหตุ: build บางชุดอาจยังแสดงเลข packaging metadata เก่าในชื่อ installer แม้ตัวแอปเป็น 1.0.0 จนกว่าจะ sync metadata ของ Inno Setup ให้ตรงกัน

## 4. วิธีติดตั้ง

1. เปิดไฟล์ `Research-OS-Setup-*-x64.exe`
2. เมื่อ Windows ขอสิทธิ์ Administrator ให้กด **Yes**
3. ใช้ตำแหน่งติดตั้งมาตรฐาน หรือเลือกตำแหน่งที่ต้องการ
4. เลือกสร้าง Desktop shortcut ได้
5. กด **Install**
6. ระบบจะติดตั้งตัวแอป, Local API, ServiceHost และ runtime ที่จำเป็น
7. ระบบจะสร้าง Windows Service ชื่อ `ResearchOSService`
8. เมื่อเสร็จเลือก **Launch Research OS after installation** ได้

ตำแหน่งโปรแกรมมาตรฐาน:

```text
C:\Program Files\Research OS
```

ตำแหน่งข้อมูลผู้ใช้และข้อมูลระบบ:

```text
C:\ProgramData\ResearchOS
```

ข้อมูลสำคัญถูกแยกไว้ใน:

```text
C:\ProgramData\ResearchOS\database
C:\ProgramData\ResearchOS\sessions
C:\ProgramData\ResearchOS\artifacts
C:\ProgramData\ResearchOS\backups
C:\ProgramData\ResearchOS\logs
```

การถอนโปรแกรมไม่ควรลบข้อมูลเหล่านี้โดยอัตโนมัติ

---

# ส่วน B — เริ่มใช้งานครั้งแรก

## 5. เปิด Research OS

เปิดจาก Desktop shortcut, Start Menu หรือไฟล์:

```text
C:\Program Files\Research OS\app\research_os_flutter.exe
```

หลังเปิดโปรแกรม ให้เริ่มจาก **Home** และ **System Monitor** เพื่อดูว่าสถานะระบบปกติ

Local API มาตรฐานคือ:

```text
http://127.0.0.1:8787
```

## 6. ถ้าแอปแจ้งว่า API unavailable

1. เปิดเมนู **Local API & Service**
2. ตรวจว่า Service เป็น Running
3. เปิด **System Monitor** และดู health status
4. ตรวจใน **Settings** ว่า API Base URL เป็น `http://127.0.0.1:8787`
5. ถ้ายังไม่พร้อม ให้ปิดและเปิดแอปใหม่

ผู้ใช้ทั่วไปไม่จำเป็นต้องใช้ PowerShell เว้นแต่กำลังทำ troubleshooting ตามคำแนะนำของผู้ดูแลระบบ

---

# ส่วน C — วิธีใช้แต่ละระบบ

## 7. Home

Home เป็น Dashboard กลาง ใช้ดูภาพรวมของ Research OS และสถานะ component สำคัญ แนะนำให้ใช้เป็นจุดเริ่มต้นทุกครั้งที่เปิดโปรแกรม

## 8. AI Chat

ใช้ถามคำถาม สรุปข้อมูล วิเคราะห์ข้อความ หรือทำงานผ่าน AI provider ที่เชื่อมต่อไว้

วิธีใช้:

1. เปิด **AI Chat**
2. พิมพ์คำถามหรืองาน
3. ส่งข้อความ
4. ตรวจผลลัพธ์ก่อนนำไปใช้จริง

ถ้า AI ไม่ตอบ ให้ตรวจ Settings, System Monitor และสถานะ provider

## 9. Agent Center

Agent Center เป็นศูนย์กลาง Multi-Agent ของระบบ

Agent หลักใน V1:

- Research Agent — Research, synthesis, Memory และ Knowledge
- Document Agent — PDF, Word, Excel, PowerPoint และ Markdown
- GitHub Agent — Repository, Commit, PR, Issues และ Workflows
- Google Workspace Agent — Drive, Docs, Sheets, Calendar, Gmail และ Workspace
- Shift Agent — Roster, replacement, leave, conflict และ calendar sync

### สร้าง orchestration

1. เปิด **Agent Center**
2. ไปที่ **Multi-Agent orchestration**
3. กด **Create orchestration**
4. ใส่ Objective
5. เพิ่ม Steps
6. ระบุ dependency หากงานหนึ่งต้องรออีกงาน
7. สร้าง orchestration
8. ตรวจสถานะ run
9. กด Execute เมื่อพร้อม

### Confirmation Gate

ถ้างานมีการเขียนหรือเปลี่ยนข้อมูล ระบบอาจหยุดรอการยืนยัน

ก่อนกด Confirm ให้ตรวจ Objective, Step และผลกระทบให้ครบ การอ่านข้อมูลสามารถทำงานตาม permission ได้ ส่วน write-capable action ต้องผ่าน confirmation policy ที่ระบบกำหนด

## 10. Library

ใช้ดู Research Artifacts และข้อมูลความรู้ที่ระบบบันทึกไว้ เหมาะสำหรับกลับมาเปิดผลวิเคราะห์ เอกสาร หรือองค์ความรู้เดิม

## 11. Knowledge Graph

ใช้ดูความสัมพันธ์ระหว่างข้อมูล, artifact, node และ knowledge ที่เชื่อมโยงกัน ช่วยให้เห็นว่าองค์ความรู้แต่ละส่วนเกี่ยวข้องกันอย่างไร

## 12. GitHub

ใช้เข้าถึงงาน GitHub ผ่านส่วนเชื่อมต่อของ Research OS เช่น Repository, Commit, Pull Request, Issues และ Workflows ตามสิทธิ์ที่เชื่อมไว้

การเปลี่ยนแปลง repository ควรตรวจข้อมูลให้ครบก่อนยืนยันทุกครั้ง

## 13. Google Workspace

รวมพื้นที่ทำงานสำหรับ Drive, Docs, Sheets, Calendar, Gmail และบริการ Workspace ที่ระบบรองรับ

งานอ่านข้อมูลและงานเขียนข้อมูลถูกแยกตามสิทธิ์ และงานที่มีผลต่อข้อมูลอาจต้องผ่าน confirmation

## 14. Local API & Service

เมนูนี้ใช้ดูสถานะ backend ภายในเครื่อง ผู้ใช้ทั่วไปควรใช้เพื่อดูสถานะเป็นหลัก ไม่จำเป็นต้องจัดการ service ด้วย command line

ค่าปกติ:

```text
Service: ResearchOSService
Local API: http://127.0.0.1:8787
```

## 15. System Monitor

ใช้ตรวจสุขภาพ Local API, backend และ component ต่าง ๆ ถ้าฟังก์ชันใดใช้งานไม่ได้ ควรตรวจหน้านี้ก่อน

## 16. Settings

ใช้ตั้งค่า Theme, API Base URL และการตั้งค่าที่ UI เปิดให้ใช้งาน

ค่า API Base URL สำหรับการติดตั้ง local มาตรฐาน:

```text
http://127.0.0.1:8787
```

---

# ส่วน D — ระบบข้อมูลและความปลอดภัย

## 17. Local-first storage

Research OS ออกแบบให้ข้อมูลหลักอยู่ในเครื่องก่อน โดยเก็บแยกจากไฟล์โปรแกรมภายใต้ `C:\ProgramData\ResearchOS`

## 18. Memory / Knowledge

Memory, sessions, artifacts, database และ backups ถูกแยกเป็นส่วนเพื่อให้ระบบสามารถอัปเดตตัวโปรแกรมโดยไม่ต้องลบข้อมูลผู้ใช้

## 19. Permission และ Confirmation

Agent ทุกตัวใช้ permission model และ confirmation policy ร่วมกัน เพื่อไม่ให้ action ที่มีผลต่อข้อมูลถูกทำโดยไม่มีการตรวจสอบ

---

# ส่วน E — การอัปเดตและถอนการติดตั้ง

## 20. การอัปเดต

เมื่อมี installer รุ่นใหม่:

1. ปิด Research OS
2. ใช้ installer รุ่นใหม่ที่ผ่าน release validation
3. ติดตั้งทับตามขั้นตอนมาตรฐาน
4. เปิดโปรแกรมและตรวจ Home / System Monitor
5. ตรวจ Library และข้อมูลเดิมว่าครบ

## 21. การถอนการติดตั้ง

ถอนจาก **Settings > Apps > Installed apps > Research OS > Uninstall** หรือใช้ shortcut uninstall ที่ installer สร้างไว้

ตัวถอนการติดตั้งจะถอน Windows Service ออก แต่ข้อมูล local ใน `C:\ProgramData\ResearchOS` ถูกออกแบบให้คงไว้ เพื่อใช้ติดตั้งใหม่หรือกู้คืนภายหลัง

ถ้าต้องการลบข้อมูลทั้งหมด ให้สำรองข้อมูลก่อนและดำเนินการแยกจากการถอนโปรแกรม

---

# ส่วน F — แก้ปัญหาเบื้องต้นสำหรับผู้ใช้ทั่วไป

## 22. เปิดแอปไม่ได้

- Restart Windows หนึ่งครั้งหลังติดตั้ง
- เปิดจาก Start Menu หรือ Desktop shortcut
- ตรวจว่า antivirus ไม่ได้ quarantine ไฟล์ของ Research OS

## 23. AI Chat ใช้ไม่ได้

- ตรวจอินเทอร์เน็ต
- ตรวจ provider ใน Settings
- ตรวจ System Monitor
- ตรวจว่า Local API พร้อม

## 24. Agent Center โหลดไม่ได้

- ตรวจ Local API & Service
- ตรวจ System Monitor
- กด Refresh orchestrations
- ปิดและเปิดแอปใหม่ถ้าจำเป็น

## 25. GitHub หรือ Google Workspace ใช้ไม่ได้

- ตรวจว่าบัญชี/connection ได้รับสิทธิ์แล้ว
- ตรวจอินเทอร์เน็ต
- ตรวจ permission ที่ระบบแสดง
- งานเขียนข้อมูลอาจต้องยืนยันก่อน

---

# ส่วน G — สิ่งที่ผู้ใช้ทั่วไปไม่ต้องทำ

ผู้ใช้ทั่วไปไม่ต้อง:

- clone repository
- ติดตั้ง Flutter SDK
- ติดตั้ง .NET SDK
- ติดตั้ง Python แยก
- รัน source code
- แก้ workflow หรือ GitHub Actions
- build installer เอง
- publish ServiceHost เอง
- แก้ OpenAPI หรือ source files
- ใช้ developer scripts เพื่อควบคุมระบบตามปกติ

หากต้องทำงานเหล่านี้ ให้ใช้ `DEVELOPER_GUIDE_TH.md`

---

## 26. เอกสารที่เกี่ยวข้อง

- `SYSTEM_OVERVIEW_TH.md` — ภาพรวมทุกระบบและความสัมพันธ์ของ component
- `DEVELOPER_GUIDE_TH.md` — คู่มือนักพัฒนาและผู้ดูแล source/build/CI
- `V1_FAST_TRACK.md` — หลักฐานและ release gates ของ V1

Research OS V1 แยกประสบการณ์ของ **ผู้ใช้ทั่วไป** ออกจาก **Developer/Maintainer** โดยชัดเจน เพื่อให้ผู้ใช้ติดตั้งและใช้งานได้โดยไม่ต้องเข้าใจโครงสร้าง source code หรือเครื่องมือพัฒนา
