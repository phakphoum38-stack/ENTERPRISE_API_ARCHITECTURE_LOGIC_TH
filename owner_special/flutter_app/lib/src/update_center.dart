import 'dart:io';

import 'package:flutter/material.dart';

enum UpdateState {
  idle,
  updateAvailable,
  verifying,
  verified,
  waitingForUac,
  installing,
  completed,
  failed,
  hashMismatch,
}

class ResearchOsUpdateController extends ChangeNotifier {
  ResearchOsUpdateController._();

  static final ResearchOsUpdateController instance = ResearchOsUpdateController._();

  UpdateState state = UpdateState.idle;
  String currentVersion = '1.3.0';
  String? availableVersion;
  String? installerPath;
  String? expectedSha256;
  String message = 'ยังไม่มีอัปเดตใหม่';
  bool unread = false;

  bool get hasUpdate => availableVersion != null && availableVersion!.trim().isNotEmpty;

  void configureFromEnvironment() {
    final env = Platform.environment;
    final version = env['RESEARCH_OS_UPDATE_VERSION']?.trim();
    final path = env['RESEARCH_OS_UPDATE_INSTALLER']?.trim();
    final sha = env['RESEARCH_OS_UPDATE_SHA256']?.trim().toLowerCase();
    currentVersion = env['RESEARCH_OS_CURRENT_VERSION']?.trim().isNotEmpty == true
        ? env['RESEARCH_OS_CURRENT_VERSION']!.trim()
        : currentVersion;
    if (version != null && version.isNotEmpty) {
      availableVersion = version;
      installerPath = path?.isEmpty == true ? null : path;
      expectedSha256 = sha?.isEmpty == true ? null : sha;
      state = UpdateState.updateAvailable;
      message = 'มี Research OS เวอร์ชัน $version พร้อมติดตั้ง';
      unread = true;
    }
    notifyListeners();
  }

  void markRead() {
    if (!unread) return;
    unread = false;
    notifyListeners();
  }

  Future<void> installNow() async {
    final path = installerPath;
    final expected = expectedSha256;
    if (path == null || path.isEmpty || expected == null || expected.isEmpty) {
      state = UpdateState.failed;
      message = 'ยังไม่มี installer/manifest ที่พร้อมใช้งาน';
      notifyListeners();
      return;
    }
    final file = File(path);
    if (!await file.exists()) {
      state = UpdateState.failed;
      message = 'ไม่พบไฟล์ติดตั้งที่เตรียมไว้';
      notifyListeners();
      return;
    }

    state = UpdateState.verifying;
    message = 'กำลังตรวจสอบ SHA-256…';
    notifyListeners();

    try {
      if (!Platform.isWindows) {
        throw UnsupportedError('Update installation is currently supported on Windows only');
      }
      final hashResult = await Process.run(
        'powershell.exe',
        <String>[
          '-NoProfile',
          '-NonInteractive',
          '-Command',
          '(Get-FileHash -Algorithm SHA256 -LiteralPath "${path.replaceAll('"', '""')}").Hash.ToLowerInvariant()',
        ],
      );
      if (hashResult.exitCode != 0) {
        throw ProcessException('powershell.exe', const <String>[], hashResult.stderr.toString(), hashResult.exitCode);
      }
      final actual = hashResult.stdout.toString().trim().toLowerCase();
      if (actual != expected.toLowerCase()) {
        state = UpdateState.hashMismatch;
        message = 'หยุดการติดตั้ง: SHA-256 ไม่ตรงกับ build manifest';
        notifyListeners();
        return;
      }

      state = UpdateState.verified;
      message = 'Verified ✓ พร้อมขอสิทธิ์ติดตั้ง';
      notifyListeners();
      await Future<void>.delayed(const Duration(milliseconds: 250));

      state = UpdateState.waitingForUac;
      message = 'รอการอนุญาตจาก Windows';
      notifyListeners();

      final launch = await Process.run(
        'powershell.exe',
        <String>[
          '-NoProfile',
          '-NonInteractive',
          '-Command',
          'Start-Process -FilePath "${path.replaceAll('"', '""')}" -Verb RunAs',
        ],
      );
      if (launch.exitCode != 0) {
        throw ProcessException('powershell.exe', const <String>[], launch.stderr.toString(), launch.exitCode);
      }
      state = UpdateState.installing;
      message = 'เปิดตัวติดตั้งแล้ว กรุณาทำขั้นตอนใน Windows ให้เสร็จ';
      unread = false;
      notifyListeners();
    } catch (error) {
      state = UpdateState.failed;
      message = 'ติดตั้งไม่สำเร็จ: $error';
      notifyListeners();
    }
  }

  void retry() {
    if (!hasUpdate) return;
    state = UpdateState.updateAvailable;
    message = 'พร้อมลองติดตั้งอีกครั้ง';
    notifyListeners();
  }
}

class UpdateCenterPage extends StatefulWidget {
  const UpdateCenterPage({super.key});

  @override
  State<UpdateCenterPage> createState() => _UpdateCenterPageState();
}

class _UpdateCenterPageState extends State<UpdateCenterPage> {
  final controller = ResearchOsUpdateController.instance;

  @override
  void initState() {
    super.initState();
    controller.configureFromEnvironment();
    controller.markRead();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        final busy = controller.state == UpdateState.verifying ||
            controller.state == UpdateState.waitingForUac ||
            controller.state == UpdateState.installing;
        return ListView(
          key: const Key('update-center'),
          padding: const EdgeInsets.all(24),
          children: <Widget>[
            Row(
              children: <Widget>[
                const Icon(Icons.notifications_active_outlined, size: 30),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text('Notification & Update Center', style: Theme.of(context).textTheme.headlineSmall),
                      Text('Research OS ${controller.currentVersion}'),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: <Widget>[
                    Row(
                      children: <Widget>[
                        Icon(_iconFor(controller.state)),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            controller.hasUpdate
                                ? 'Research OS ${controller.availableVersion}'
                                : 'ระบบเป็นเวอร์ชันล่าสุด',
                            style: Theme.of(context).textTheme.titleLarge,
                          ),
                        ),
                        _StateChip(state: controller.state),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(controller.message, key: const Key('update-message')),
                    if (busy) ...<Widget>[
                      const SizedBox(height: 16),
                      const LinearProgressIndicator(),
                    ],
                    const SizedBox(height: 18),
                    Wrap(
                      spacing: 10,
                      runSpacing: 10,
                      children: <Widget>[
                        if (controller.hasUpdate)
                          FilledButton.icon(
                            key: const Key('install-update-now'),
                            onPressed: busy ? null : controller.installNow,
                            icon: const Icon(Icons.system_update_alt),
                            label: const Text('Install now'),
                          ),
                        if (controller.state == UpdateState.failed || controller.state == UpdateState.hashMismatch)
                          OutlinedButton.icon(
                            key: const Key('retry-update'),
                            onPressed: controller.retry,
                            icon: const Icon(Icons.refresh),
                            label: const Text('Retry'),
                          ),
                        TextButton(onPressed: () {}, child: const Text('Later')),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            const Card(
              child: ListTile(
                leading: Icon(Icons.shield_outlined),
                title: Text('Verified update policy'),
                subtitle: Text('Research OS ตรวจ SHA-256 ของ build นี้อัตโนมัติก่อนเปิด installer และจะหยุดทันทีหาก hash ไม่ตรง'),
              ),
            ),
            const Card(
              child: ListTile(
                leading: Icon(Icons.memory_outlined),
                title: Text('Memory & owner data'),
                subtitle: Text('ข้อมูลถาวรถูกแยกจากตัวโปรแกรมและต้องได้รับการรักษาระหว่างการอัปเดต'),
              ),
            ),
          ],
        );
      },
    );
  }

  static IconData _iconFor(UpdateState state) => switch (state) {
        UpdateState.completed => Icons.check_circle_outline,
        UpdateState.failed || UpdateState.hashMismatch => Icons.error_outline,
        UpdateState.verifying || UpdateState.verified => Icons.verified_outlined,
        UpdateState.waitingForUac => Icons.admin_panel_settings_outlined,
        UpdateState.installing => Icons.install_desktop_outlined,
        UpdateState.updateAvailable => Icons.system_update_outlined,
        UpdateState.idle => Icons.notifications_none,
      };
}

class _StateChip extends StatelessWidget {
  const _StateChip({required this.state});

  final UpdateState state;

  @override
  Widget build(BuildContext context) {
    final label = switch (state) {
      UpdateState.idle => 'Up to date',
      UpdateState.updateAvailable => 'Update available',
      UpdateState.verifying => 'Verifying',
      UpdateState.verified => 'Verified',
      UpdateState.waitingForUac => 'Waiting for UAC',
      UpdateState.installing => 'Installing',
      UpdateState.completed => 'Completed',
      UpdateState.failed => 'Failed',
      UpdateState.hashMismatch => 'Hash mismatch',
    };
    return Chip(label: Text(label));
  }
}
