import 'package:flutter/material.dart';

import '../../platform/local_api_manager.dart';

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
    if (_manager.supported) {
      _run(_manager.serviceStatus, silent: true);
    }
  }

  Future<void> _run(
    Future<LocalApiCommandResult> Function() command, {
    bool silent = false,
  }) async {
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
    if (filled) {
      return FilledButton.icon(onPressed: onPressed, icon: Icon(icon), label: Text(label));
    }
    return OutlinedButton.icon(onPressed: onPressed, icon: Icon(icon), label: Text(label));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Local API & Windows Service'),
        actions: <Widget>[
          IconButton(
            tooltip: 'ตรวจสถานะ Service',
            onPressed: _busy || !_manager.supported ? null : () => _run(_manager.serviceStatus),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: <Widget>[
          Text('Research OS Windows Service', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 8),
          const Text(
            'โหมดแนะนำสำหรับ Windows: API ทำงานเป็น Service เบื้องหลัง เปิดพร้อมเครื่อง และ Windows จะ Restart ให้อัตโนมัติเมื่อ Service ล้ม',
          ),
          const SizedBox(height: 20),
          Card(
            child: ListTile(
              leading: Icon(_manager.supported ? Icons.miscellaneous_services_outlined : Icons.info_outline),
              title: Text(_manager.supported ? 'Windows Service Control พร้อมใช้งาน' : 'รองรับเฉพาะ Windows Desktop'),
              subtitle: const Text('Service: ResearchOSService • API: http://127.0.0.1:8787'),
              trailing: _busy
                  ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Chip(label: Text('Recommended')),
            ),
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: <Widget>[
              _actionButton(icon: Icons.download_for_offline_outlined, label: 'ติดตั้ง Service', command: _manager.installService, filled: true),
              _actionButton(icon: Icons.play_arrow, label: 'Start Service', command: _manager.startService),
              _actionButton(icon: Icons.stop, label: 'Stop Service', command: _manager.stopService),
              _actionButton(icon: Icons.restart_alt, label: 'Restart Service', command: _manager.restartService),
              _actionButton(icon: Icons.monitor_heart_outlined, label: 'Service Status', command: _manager.serviceStatus),
              _actionButton(icon: Icons.delete_outline, label: 'ถอน Service', command: _manager.uninstallService),
            ],
          ),
          const SizedBox(height: 10),
          const Card(
            child: ListTile(
              leading: Icon(Icons.admin_panel_settings_outlined),
              title: Text('Windows อาจถามสิทธิ์ Administrator'),
              subtitle: Text('Install / Start / Stop / Restart / Uninstall Service จะเปิด UAC เท่านั้น ไม่ต้องพิมพ์ PowerShell เอง'),
            ),
          ),
          const SizedBox(height: 28),
          Text('Local API fallback', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          const Text('เก็บโหมดเดิมไว้สำหรับ Development หรือกรณีที่ยังไม่ติดตั้ง Windows Service'),
          const SizedBox(height: 12),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: <Widget>[
              _actionButton(icon: Icons.play_circle_outline, label: 'Start API', command: _manager.start),
              _actionButton(icon: Icons.stop_circle_outlined, label: 'Stop API', command: _manager.stop),
              _actionButton(icon: Icons.restart_alt, label: 'Restart API', command: _manager.restart),
              _actionButton(icon: Icons.monitor_outlined, label: 'API Status', command: _manager.status),
            ],
          ),
          const SizedBox(height: 28),
          Text('Storage & Backup', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: <Widget>[
              _actionButton(icon: Icons.folder_open, label: 'เปิด Data Folder', command: _manager.openDataFolder),
              _actionButton(icon: Icons.backup_outlined, label: 'Backup ตอนนี้', command: _manager.backup),
            ],
          ),
          const SizedBox(height: 28),
          Text('Legacy startup fallback', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          const Text('เมื่อ Service ติดตั้งแล้ว ไม่จำเป็นต้องเปิด Auto Start แบบสคริปต์อีก'),
          const SizedBox(height: 10),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: <Widget>[
              _actionButton(icon: Icons.power_settings_new, label: 'เปิด API พร้อม Windows', command: _manager.enableAutostart),
              _actionButton(icon: Icons.power_off_outlined, label: 'ปิด Auto Start', command: _manager.disableAutostart),
            ],
          ),
          const SizedBox(height: 28),
          Text('ผลล่าสุด', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: SelectableText(
                _lastResult == null
                    ? 'ยังไม่มีผลการทำงาน'
                    : '${_lastResult!.ok ? 'OK' : 'ERROR'} — ${_lastResult!.message}\n${_lastResult!.details}',
              ),
            ),
          ),
          const SizedBox(height: 16),
          const Card(
            child: ListTile(
              leading: Icon(Icons.security_outlined),
              title: Text('Service ไม่ฝัง Secret ในแอป'),
              subtitle: Text('Service Host อ่านค่าจาก Backend/Machine environment และเก็บข้อมูลใต้ ResearchOSData; Flutter ไม่ได้รับ Gemini, GitHub หรือ Google refresh token'),
            ),
          ),
        ],
      ),
    );
  }
}
