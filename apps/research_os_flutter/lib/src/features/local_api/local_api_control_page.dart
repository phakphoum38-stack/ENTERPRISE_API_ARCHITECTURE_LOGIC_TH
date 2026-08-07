import 'package:flutter/material.dart';

import '../../platform/local_api_manager.dart';
import '../../ui/enterprise_components.dart';

class LocalApiControlPage extends StatefulWidget {
  const LocalApiControlPage({super.key});

  @override
  State<LocalApiControlPage> createState() => _LocalApiControlPageState();
}

class _LocalApiControlPageState extends State<LocalApiControlPage> {
  final LocalApiManager _manager = const LocalApiManager();
  bool _busy = false;
  LocalApiCommandResult? _lastResult;

  @override
  void initState() {
    super.initState();
    if (_manager.supported) _run(_manager.serviceStatus, silent: true);
  }

  Future<void> _run(Future<LocalApiCommandResult> Function() command, {bool silent = false}) async {
    if (_busy) return;
    setState(() => _busy = true);
    final result = await command();
    if (!mounted) return;
    setState(() {
      _busy = false;
      _lastResult = result;
    });
    if (!silent) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(result.ok ? 'สำเร็จ: ${result.message}' : 'ไม่สำเร็จ: ${result.message}')),
      );
    }
  }

  Widget _actionButton({
    required IconData icon,
    required String label,
    required Future<LocalApiCommandResult> Function() command,
    bool filled = false,
  }) {
    final onPressed = _busy || !_manager.supported ? null : () => _run(command);
    return filled
        ? FilledButton.icon(onPressed: onPressed, icon: Icon(icon), label: Text(label))
        : OutlinedButton.icon(onPressed: onPressed, icon: Icon(icon), label: Text(label));
  }

  @override
  Widget build(BuildContext context) {
    final resultText = _lastResult == null
        ? 'ยังไม่มีผลการทำงาน'
        : '${_lastResult!.ok ? 'OK' : 'ERROR'} — ${_lastResult!.message}\n${_lastResult!.details}';

    return ListView(
      padding: const EdgeInsets.fromLTRB(24, 22, 24, 32),
      children: <Widget>[
        EnterprisePageHeader(
          icon: Icons.dns_outlined,
          title: 'Local API & Windows Service',
          subtitle: 'ควบคุม Backend ของ Research OS จากหน้าต่างเดียว โดย Windows Service เป็นโหมดแนะนำสำหรับการใช้งานจริง',
          actions: <Widget>[
            IconButton(
              tooltip: 'ตรวจสถานะ Service',
              onPressed: _busy || !_manager.supported ? null : () => _run(_manager.serviceStatus),
              icon: const Icon(Icons.refresh),
            ),
          ],
        ),
        const SizedBox(height: 24),
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: <Widget>[
            SizedBox(width: 260, child: EnterpriseStatusTile(icon: Icons.miscellaneous_services_outlined, title: 'Windows Service', value: _manager.supported ? 'Available' : 'Unsupported', caption: 'ResearchOSService')),
            const SizedBox(width: 260, child: EnterpriseStatusTile(icon: Icons.link_outlined, title: 'Local endpoint', value: '127.0.0.1:8787', caption: 'Research OS API')),
            SizedBox(width: 260, child: EnterpriseStatusTile(icon: Icons.pending_actions_outlined, title: 'Manager', value: _busy ? 'Working…' : 'Ready', caption: 'GUI controlled')),
          ],
        ),
        const SizedBox(height: 28),
        EnterpriseSection(
          title: 'Windows Service',
          subtitle: 'เปิดพร้อม Windows, ทำงานเบื้องหลัง และมี Recovery policy เมื่อ API ล้ม',
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Wrap(
                    spacing: 10,
                    runSpacing: 10,
                    children: <Widget>[
                      _actionButton(icon: Icons.download_for_offline_outlined, label: 'ติดตั้ง Service', command: _manager.installService, filled: true),
                      _actionButton(icon: Icons.play_arrow, label: 'Start', command: _manager.startService),
                      _actionButton(icon: Icons.stop, label: 'Stop', command: _manager.stopService),
                      _actionButton(icon: Icons.restart_alt, label: 'Restart', command: _manager.restartService),
                      _actionButton(icon: Icons.monitor_heart_outlined, label: 'Status', command: _manager.serviceStatus),
                      _actionButton(icon: Icons.delete_outline, label: 'ถอน Service', command: _manager.uninstallService),
                    ],
                  ),
                  const SizedBox(height: 14),
                  const Divider(height: 1),
                  const SizedBox(height: 12),
                  const Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Icon(Icons.admin_panel_settings_outlined, size: 20),
                      SizedBox(width: 10),
                      Expanded(child: Text('Windows อาจแสดง UAC สำหรับคำสั่ง Service ที่ต้องใช้สิทธิ์ Administrator แต่ไม่ต้องเปิดหรือพิมพ์ PowerShell เอง')),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(height: 28),
        EnterpriseSection(
          title: 'Development fallback',
          subtitle: 'Local API แบบสคริปต์สำหรับ development หรือกรณียังไม่ติดตั้ง Service',
          child: Wrap(
            spacing: 10,
            runSpacing: 10,
            children: <Widget>[
              _actionButton(icon: Icons.play_circle_outline, label: 'Start API', command: _manager.start),
              _actionButton(icon: Icons.stop_circle_outlined, label: 'Stop API', command: _manager.stop),
              _actionButton(icon: Icons.restart_alt, label: 'Restart API', command: _manager.restart),
              _actionButton(icon: Icons.monitor_outlined, label: 'API Status', command: _manager.status),
            ],
          ),
        ),
        const SizedBox(height: 28),
        EnterpriseSection(
          title: 'Storage & resilience',
          subtitle: 'Local-first data, backup และ legacy startup fallback',
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Wrap(
                spacing: 10,
                runSpacing: 10,
                children: <Widget>[
                  _actionButton(icon: Icons.folder_open, label: 'เปิด Data Folder', command: _manager.openDataFolder),
                  _actionButton(icon: Icons.backup_outlined, label: 'Backup ตอนนี้', command: _manager.backup, filled: true),
                  _actionButton(icon: Icons.power_settings_new, label: 'เปิด Legacy Auto Start', command: _manager.enableAutostart),
                  _actionButton(icon: Icons.power_off_outlined, label: 'ปิด Legacy Auto Start', command: _manager.disableAutostart),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(height: 28),
        EnterpriseSection(
          title: 'Latest operation',
          subtitle: 'ผลจากคำสั่งล่าสุดของ Service/API Manager',
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: SelectableText(resultText),
            ),
          ),
        ),
        const SizedBox(height: 16),
        const Card(
          child: ListTile(
            leading: Icon(Icons.security_outlined),
            title: Text('Backend secrets remain isolated'),
            subtitle: Text('Service Host อ่านค่า Secret จาก Backend/Machine environment; Flutter ไม่ได้รับ Gemini, GitHub หรือ Google refresh token'),
            trailing: Chip(label: Text('Local-first')),
          ),
        ),
      ],
    );
  }
}
