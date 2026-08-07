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
      _run(_manager.status, silent: true);
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
        SnackBar(
          content: Text(result.ok ? 'สำเร็จ: ${result.message}' : 'ไม่สำเร็จ: ${result.message}'),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Local API Control Center'),
        actions: <Widget>[
          IconButton(
            tooltip: 'ตรวจสถานะ',
            onPressed: _busy || !_manager.supported ? null : () => _run(_manager.status),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: <Widget>[
          Text('ควบคุม Research OS API', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: 8),
          const Text(
            'เปิด ปิด รีสตาร์ต สำรองข้อมูล และตั้งค่าเริ่มพร้อม Windows ได้จากหน้าแอป ไม่ต้องเปิด PowerShell เอง',
          ),
          const SizedBox(height: 20),
          Card(
            child: ListTile(
              leading: Icon(
                _manager.supported ? Icons.desktop_windows_outlined : Icons.info_outline,
              ),
              title: Text(_manager.supported ? 'Windows Local API Manager พร้อมใช้งาน' : 'Local API Manager ไม่รองรับแพลตฟอร์มนี้'),
              subtitle: const Text('Local endpoint: http://127.0.0.1:8787'),
              trailing: _busy
                  ? const SizedBox(
                      width: 22,
                      height: 22,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : null,
            ),
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: <Widget>[
              FilledButton.icon(
                onPressed: _busy || !_manager.supported ? null : () => _run(_manager.start),
                icon: const Icon(Icons.play_arrow),
                label: const Text('Start API'),
              ),
              OutlinedButton.icon(
                onPressed: _busy || !_manager.supported ? null : () => _run(_manager.stop),
                icon: const Icon(Icons.stop),
                label: const Text('Stop API'),
              ),
              OutlinedButton.icon(
                onPressed: _busy || !_manager.supported ? null : () => _run(_manager.restart),
                icon: const Icon(Icons.restart_alt),
                label: const Text('Restart API'),
              ),
              OutlinedButton.icon(
                onPressed: _busy || !_manager.supported ? null : () => _run(_manager.status),
                icon: const Icon(Icons.monitor_heart_outlined),
                label: const Text('Status'),
              ),
            ],
          ),
          const SizedBox(height: 24),
          Text('Storage & Backup', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: <Widget>[
              OutlinedButton.icon(
                onPressed: _busy || !_manager.supported ? null : () => _run(_manager.openDataFolder),
                icon: const Icon(Icons.folder_open),
                label: const Text('เปิด Data Folder'),
              ),
              OutlinedButton.icon(
                onPressed: _busy || !_manager.supported ? null : () => _run(_manager.backup),
                icon: const Icon(Icons.backup_outlined),
                label: const Text('Backup ตอนนี้'),
              ),
            ],
          ),
          const SizedBox(height: 24),
          Text('Windows Startup', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: <Widget>[
              OutlinedButton.icon(
                onPressed: _busy || !_manager.supported ? null : () => _run(_manager.enableAutostart),
                icon: const Icon(Icons.power_settings_new),
                label: const Text('เปิด API พร้อม Windows'),
              ),
              OutlinedButton.icon(
                onPressed: _busy || !_manager.supported ? null : () => _run(_manager.disableAutostart),
                icon: const Icon(Icons.power_off_outlined),
                label: const Text('ปิด Auto Start'),
              ),
            ],
          ),
          const SizedBox(height: 24),
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
              title: Text('ไม่ฝังคีย์ไว้ในหน้าต่างนี้'),
              subtitle: Text('Gemini/GitHub secrets ยังคงอยู่ฝั่ง Backend หรือ Windows Environment ตามโครงสร้างเดิม'),
            ),
          ),
        ],
      ),
    );
  }
}
