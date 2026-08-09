# Research OS v1 — ภาพรวมทุกระบบ

เอกสารนี้อธิบายองค์ประกอบทั้งหมดของ Research OS V1 ในระดับระบบ โดยไม่ลงรายละเอียดการพัฒนาเชิงลึก ผู้ใช้ทั่วไปสามารถอ่านเพื่อเข้าใจว่าระบบทำงานร่วมกันอย่างไร ส่วนรายละเอียด source/build/CI อยู่ใน `DEVELOPER_GUIDE_TH.md`

## 1. Desktop Application

Flutter Desktop เป็นหน้าหลักของผู้ใช้ ประกอบด้วย Home, AI Chat, Agent Center, Library, Knowledge Graph, GitHub, Google Workspace, Local API & Service, System Monitor และ Settings

## 2. Local API

Local API ทำงานบน `http://127.0.0.1:8787` และเป็นจุดเชื่อมระหว่าง UI กับ backend capabilities เช่น AI generation, Knowledge, Multi-Agent และ provider status

## 3. Windows Service

Service ชื่อ `ResearchOSService` ทำหน้าที่ดูแล backend ให้พร้อมหลังเปิดเครื่อง และใช้ ServiceHost สำหรับเปิด Local API อย่างต่อเนื่อง

## 4. ServiceHost

`ResearchOS.ServiceHost.exe` เป็น host ของ Windows Service และ bootstrap environment ของ Research OS backend

## 5. Bundled Python Runtime

Installer รวม Python runtime เพื่อให้ผู้ใช้ทั่วไปไม่ต้องติดตั้ง Python เอง Runtime นี้ใช้กับ Research OS API และ backend modules ที่ต้องใช้ Python

## 6. AI Provider Layer

Provider layer แยก AI provider ออกจาก application logic เพื่อให้ระบบรองรับ provider หลายแบบ และตรวจสถานะผ่าน provider endpoint ได้

## 7. AI Chat

AI Chat เป็น user-facing interface สำหรับส่ง prompt ไปยัง provider ที่ active และรับผลลัพธ์กลับผ่าน Local API

## 8. Agent Registry

Agent Registry เก็บ agent ที่ระบบรู้จัก เช่น Research Agent, Document Agent, GitHub Agent, Google Workspace Agent และ Shift Agent พร้อม capability และ permission ของแต่ละ agent

## 9. Capability Router

Router เลือก agent ตามความสามารถที่ต้องใช้ แทนการผูกงานกับ agent แบบตายตัว

## 10. Agent Runtime

Agent Runtime ดูแล lifecycle ของงาน, shared context, queue, events และ execution state ของ agent

## 11. Task Queue

Task Queue จัดลำดับงานที่รอทำและรองรับการทำงานหลายขั้นตอน

## 12. Event Bus

Event Bus ใช้ส่ง runtime events ระหว่าง component เพื่อให้สถานะของ orchestration และ agent สอดคล้องกัน

## 13. Shared Context

Shared Context ให้ agent ใช้บริบทงานร่วมกันโดยยังคง local-first model

## 14. Multi-Agent Orchestrator

Orchestrator สร้าง run, dependency chain, execute step, ตรวจสถานะ และจัดการ confirmation gate

## 15. Dependency Delegation

แต่ละ step สามารถขึ้นกับ step ก่อนหน้า ทำให้ workflow ซับซ้อนแบ่งงานหลาย agent ได้

## 16. Permission Model

Agent ใช้ permission model เพื่อกำหนดว่า capability ใดอ่านได้ เขียนได้ หรือจำเป็นต้องยืนยันก่อน

## 17. Confirmation Policy

งานที่มีผลต่อข้อมูลสามารถถูกหยุดที่ confirmation gate ก่อนดำเนินการจริง ลดความเสี่ยงจาก write action ที่ไม่ได้ตรวจสอบ

## 18. Research Agent

ใช้กับงาน Research, synthesis, Memory และ Knowledge

## 19. Document Agent

ใช้กับเอกสาร PDF, Word, Excel, PowerPoint และ Markdown ตาม capability ที่ระบบรองรับ

## 20. GitHub Agent

ใช้กับ Repository, Commit, Pull Request, Issues และ Workflows โดย write action อยู่ภายใต้ permission/confirmation policy

## 21. Google Workspace Agent

ใช้กับ Drive, Docs, Sheets, Calendar, Gmail และ Workspace ตามการเชื่อมต่อและสิทธิ์ที่ได้รับ

## 22. Shift Agent

ใช้กับ roster, replacement, leave, conflict และ calendar sync โดยงานที่เขียนข้อมูลต้องผ่าน policy ที่กำหนด

## 23. Library

Library เป็นพื้นที่ให้ผู้ใช้เปิด Research Artifacts และข้อมูล knowledge ที่จัดเก็บไว้

## 24. Research Artifacts

Artifact คือผลลัพธ์เชิงความรู้ที่สร้างจากการวิเคราะห์หรือกระบวนการของ Research OS และสามารถนำกลับมาใช้ต่อได้

## 25. Knowledge Graph

Knowledge Graph แสดงความสัมพันธ์ระหว่าง nodes, artifacts และ knowledge เพื่อช่วยค้นหาและติดตามความเชื่อมโยงของข้อมูล

## 26. Local Data Storage

ข้อมูลระบบหลักอยู่ภายใต้ `C:\ProgramData\ResearchOS` และแบ่งเป็น database, sessions, artifacts, backups และ logs

## 27. Database

ใช้เก็บข้อมูลที่ backend ต้องการแบบมีโครงสร้างตาม implementation ของระบบ

## 28. Sessions

เก็บข้อมูล session และ state ที่ต้องการคงไว้ระหว่างการใช้งาน

## 29. Backups

ใช้เป็นพื้นที่สำหรับข้อมูลสำรองของ local-first data

## 30. Logs

เก็บข้อมูล log ที่ใช้ตรวจสอบสุขภาพและแก้ปัญหาระบบ

## 31. GitHub Integration

ส่วน GitHub ใน UI เชื่อม capabilities ของ GitHub เข้ากับ Research OS โดยยังคงแยก read/write permission

## 32. Google Workspace Integration

รวมบริการ Drive, Docs, Sheets, Calendar และ Gmail เข้ากับ workspace โดยต้องผ่าน authentication/permission ที่กำหนด

## 33. Local API & Service Control

เป็นส่วน UI สำหรับดูและควบคุมสถานะ backend โดยไม่ต้องใช้ command line ในการใช้งานปกติ

## 34. System Monitor

ใช้ตรวจ health และ availability ของ component สำคัญ เช่น Local API และ backend integrations

## 35. Settings

ดูแล Theme, API Base URL และค่าที่ผู้ใช้สามารถตั้งได้จาก UI

## 36. Installer

Windows installer สร้าง one-click package ที่รวม Flutter app, ServiceHost, Python runtime, API modules และ scripts ที่จำเป็น

## 37. Uninstaller

ถอนตัวโปรแกรมและ Windows Service แต่เก็บ local data ภายใต้ `ProgramData\ResearchOS` ไว้ตามแนวทาง local-first

## 38. Release Pipeline

ระบบ release ใช้ build, runtime smoke, installer build, installer validation, verified release artifact, compatibility gate และ production health เพื่อลดความเสี่ยงก่อนปล่อย stable

## 39. Verification Manifest

Release artifact มี verification manifest และ digest เพื่อให้ผูก artifact กับ candidate SHA ที่ผ่าน validation ได้

## 40. Production Health

ตรวจ availability ของ production-facing services หลัง release เพื่อยืนยันว่าระบบยังพร้อมใช้งาน

---

# การแบ่งผู้ใช้กับ Developer

ผู้ใช้ทั่วไปควรทำงานผ่าน installer และ UI เป็นหลัก ส่วน Developer/Maintainer จึงค่อยเข้าถึง source code, API contract, scripts, build toolchain, CI/CD, logs เชิงลึก และ release workflows

เอกสารสำหรับผู้ใช้ทั่วไป: `INSTALLATION_AND_USAGE_TH.md`

เอกสารนักพัฒนา: `DEVELOPER_GUIDE_TH.md`
