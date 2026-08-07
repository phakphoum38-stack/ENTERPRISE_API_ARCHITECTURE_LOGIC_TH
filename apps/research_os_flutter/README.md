# Research OS Flutter

แอป Flutter แบบข้ามแพลตฟอร์มสำหรับใช้เป็นหน้าบ้านของ Research OS โดยไม่ฝัง Gemini API key หรือ GitHub token ไว้ใน client

## สถานะ Sprint 1

- Material 3 application shell
- Home dashboard
- Research OS API health/provider client
- AI Memory client methods
- Widget test
- GitHub Actions สำหรับ analyze, test และ build web

## รันในเครื่อง

เปิด Research OS API ก่อนจากราก repository:

```bash
python tools/research_os_api/server.py --host 127.0.0.1 --port 8787
```

จากนั้น:

```bash
cd apps/research_os_flutter
flutter create --platforms=web,android,ios,windows,macos,linux .
flutter pub get
flutter run --dart-define=RESEARCH_OS_API_BASE_URL=http://127.0.0.1:8787
```

สำหรับ Android emulator ให้ใช้ API base URL เป็น `http://10.0.2.2:8787`

## Security

- Gemini API key อยู่ฝั่ง Research OS API เท่านั้น
- แอป Flutter เรียก backend ผ่าน HTTP API
- ก่อนเปิดใช้งานผ่านเครือข่ายจริง ต้องเพิ่ม Authentication, TLS, CORS policy และ rate limiting ที่ backend
