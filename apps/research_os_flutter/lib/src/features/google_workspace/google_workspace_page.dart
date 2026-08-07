import 'package:flutter/material.dart';

class GoogleWorkspacePage extends StatelessWidget {
  const GoogleWorkspacePage({super.key});

  static const _services = <_WorkspaceService>[
    _WorkspaceService('Drive', Icons.cloud_outlined, 'ไฟล์, โฟลเดอร์, Backup และ Sync'),
    _WorkspaceService('Docs', Icons.description_outlined, 'อ่านและสรุปเอกสาร'),
    _WorkspaceService('Sheets', Icons.table_chart_outlined, 'ตาราง, เวร, วิเคราะห์ข้อมูล'),
    _WorkspaceService('Calendar', Icons.calendar_month_outlined, 'ปฏิทิน, นัดหมาย, เวร'),
    _WorkspaceService('Gmail', Icons.mail_outline, 'ค้นหา สรุป และจัดการอีเมล'),
    _WorkspaceService('Contacts', Icons.contacts_outlined, 'รายชื่อและข้อมูลผู้ติดต่อ'),
    _WorkspaceService('Tasks', Icons.task_alt_outlined, 'งานและ To-do'),
    _WorkspaceService('Keep', Icons.lightbulb_outline, 'โน้ตและความรู้สั้น'),
    _WorkspaceService('Meet', Icons.video_call_outlined, 'การประชุมและพื้นที่ Meet'),
    _WorkspaceService('Forms', Icons.list_alt_outlined, 'แบบฟอร์มและคำตอบ'),
    _WorkspaceService('Chat', Icons.forum_outlined, 'Spaces และข้อความ Google Chat'),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Google Workspace Hub')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: <Widget>[
          Text('Google Workspace', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 8),
          const Text(
            'ศูนย์กลางบริการ Google ของ Research OS • OAuth และ Token อยู่ที่ Backend เท่านั้น',
          ),
          const SizedBox(height: 16),
          const Card(
            child: ListTile(
              leading: Icon(Icons.security_outlined),
              title: Text('OAuth แบบศูนย์กลาง'),
              subtitle: Text(
                'ใช้บัญชี Google เดียว แต่ขอสิทธิ์เป็นรายบริการ ผู้ใช้สามารถปิดบริการที่ไม่ต้องการได้',
              ),
              trailing: Chip(label: Text('Local-first')),
            ),
          ),
          const SizedBox(height: 20),
          LayoutBuilder(
            builder: (context, constraints) {
              final columns = constraints.maxWidth >= 1000
                  ? 3
                  : constraints.maxWidth >= 620
                      ? 2
                      : 1;
              final width = (constraints.maxWidth - (columns - 1) * 12) / columns;
              return Wrap(
                spacing: 12,
                runSpacing: 12,
                children: _services
                    .map(
                      (service) => SizedBox(
                        width: width,
                        child: Card(
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: <Widget>[
                                Row(
                                  children: <Widget>[
                                    Icon(service.icon, size: 28),
                                    const SizedBox(width: 10),
                                    Expanded(
                                      child: Text(
                                        service.name,
                                        style: Theme.of(context).textTheme.titleMedium,
                                      ),
                                    ),
                                    const Chip(label: Text('รอ OAuth')),
                                  ],
                                ),
                                const SizedBox(height: 12),
                                Text(service.description),
                              ],
                            ),
                          ),
                        ),
                      ),
                    )
                    .toList(),
              );
            },
          ),
          const SizedBox(height: 20),
          const Card(
            child: ListTile(
              leading: Icon(Icons.vpn_key_outlined),
              title: Text('ยังไม่มีการเก็บ Google Secret ใน Flutter'),
              subtitle: Text(
                'เมื่อใส่ RESEARCH_OS_GOOGLE_CLIENT_ID และ RESEARCH_OS_GOOGLE_CLIENT_SECRET ใน Local API แล้ว จึงค่อยเริ่ม OAuth จาก Backend',
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _WorkspaceService {
  const _WorkspaceService(this.name, this.icon, this.description);

  final String name;
  final IconData icon;
  final String description;
}
