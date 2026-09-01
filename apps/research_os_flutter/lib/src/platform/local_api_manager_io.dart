import 'dart:io';

import 'local_api_types.dart';

bool get supported => Platform.isWindows;

Future<Directory?> _findRepoRoot() async {
  final starts = <Directory>[
    Directory.current,
    File(Platform.resolvedExecutable).parent,
  ];

  for (final start in starts) {
    var current = start.absolute;
    for (var i = 0; i < 10; i++) {
      final marker = File(
        '${current.path}${Platform.pathSeparator}scripts${Platform.pathSeparator}start-research-os-local.ps1',
      );
      if (await marker.exists()) return current;
      final parent = current.parent;
      if (parent.path == current.path) break;
      current = parent;
    }
  }
  return null;
}

String _dataDir() {
  final configured = Platform.environment['RESEARCH_OS_DATA_DIR']?.trim();
  if (configured != null && configured.isNotEmpty) return configured;
  final home = Platform.environment['USERPROFILE'] ?? Directory.current.path;
  return '$home${Platform.pathSeparator}ResearchOSData';
}

Future<LocalApiCommandResult> _runScript(
  String script, {
  List<String> args = const <String>[],
}) async {
  if (!Platform.isWindows) {
    return const LocalApiCommandResult(
        ok: false, message: 'รองรับเฉพาะ Windows Desktop');
  }

  final root = await _findRepoRoot();
  if (root == null) {
    return const LocalApiCommandResult(
      ok: false,
      message: 'หาโฟลเดอร์ Research OS ไม่พบ',
      details:
          'ให้ติดตั้ง/clone repository บน Windows ก่อน แล้วเปิดแอปจากชุด Research OS Desktop',
    );
  }

  final scriptPath =
      '${root.path}${Platform.pathSeparator}scripts${Platform.pathSeparator}$script';
  if (!await File(scriptPath).exists()) {
    return LocalApiCommandResult(
        ok: false, message: 'ไม่พบ $script', details: scriptPath);
  }

  try {
    final result = await Process.run(
      'powershell.exe',
      <String>[
        '-NoProfile',
        '-NonInteractive',
        '-ExecutionPolicy',
        'Bypass',
        '-WindowStyle',
        'Hidden',
        '-File',
        scriptPath,
        ...args,
      ],
      workingDirectory: root.path,
    );
    final stdoutText = result.stdout.toString().trim();
    final stderrText = result.stderr.toString().trim();
    final detail = <String>[stdoutText, stderrText]
        .where((value) => value.isNotEmpty)
        .join('\n');
    return LocalApiCommandResult(
      ok: result.exitCode == 0,
      message: result.exitCode == 0 ? 'สำเร็จ' : 'คำสั่งไม่สำเร็จ',
      details: detail,
    );
  } on Object catch (error) {
    return LocalApiCommandResult(
        ok: false,
        message: 'เรียก Local API Manager ไม่สำเร็จ',
        details: error.toString());
  }
}

Future<LocalApiCommandResult> _runElevatedServiceAction(String action) async {
  if (!Platform.isWindows) {
    return const LocalApiCommandResult(
        ok: false, message: 'รองรับเฉพาะ Windows Desktop');
  }
  final root = await _findRepoRoot();
  if (root == null) {
    return const LocalApiCommandResult(
        ok: false, message: 'หาโฟลเดอร์ Research OS ไม่พบ');
  }
  final scriptPath =
      '${root.path}${Platform.pathSeparator}scripts${Platform.pathSeparator}research-os-service.ps1';
  if (!await File(scriptPath).exists()) {
    return LocalApiCommandResult(
        ok: false,
        message: 'ไม่พบ Research OS Service Manager',
        details: scriptPath);
  }

  final escapedScript = scriptPath.replaceAll("'", "''");
  final escapedData = _dataDir().replaceAll("'", "''");
  final argumentList =
      "'-NoProfile','-ExecutionPolicy','Bypass','-WindowStyle','Hidden','-File','$escapedScript','-Action','$action','-DataDir','$escapedData'";
  final command =
      "Start-Process powershell.exe -Verb RunAs -Wait -WindowStyle Hidden -ArgumentList $argumentList -PassThru | Select-Object -ExpandProperty ExitCode";

  try {
    final result = await Process.run(
      'powershell.exe',
      <String>[
        '-NoProfile',
        '-NonInteractive',
        '-ExecutionPolicy',
        'Bypass',
        '-Command',
        command
      ],
      workingDirectory: root.path,
    );
    final output = result.stdout.toString().trim();
    final error = result.stderr.toString().trim();
    final exitCode =
        int.tryParse(output.split(RegExp(r'\s+')).last) ?? result.exitCode;
    return LocalApiCommandResult(
      ok: exitCode == 0,
      message: exitCode == 0
          ? 'Service $action สำเร็จ'
          : 'Service $action ไม่สำเร็จ',
      details:
          <String>[output, error].where((value) => value.isNotEmpty).join('\n'),
    );
  } on Object catch (error) {
    return LocalApiCommandResult(
      ok: false,
      message: 'เปิดสิทธิ์ Administrator สำหรับ Service ไม่สำเร็จ',
      details: error.toString(),
    );
  }
}

Future<LocalApiCommandResult> status() =>
    _runScript('status-research-os-local.ps1',
        args: <String>['-DataDir', _dataDir()]);

Future<LocalApiCommandResult> start() => _runScript(
      'start-research-os-local.ps1',
      args: <String>['-DataDir', _dataDir(), '-Background'],
    );

Future<LocalApiCommandResult> stop() => _runScript('stop-research-os-local.ps1',
    args: <String>['-DataDir', _dataDir()]);

Future<LocalApiCommandResult> backup() => _runScript('backup-research-os.ps1',
    args: <String>['-DataDir', _dataDir()]);

Future<LocalApiCommandResult> enableAutostart() => _runScript(
      'enable-research-os-autostart.ps1',
      args: <String>['-DataDir', _dataDir()],
    );

Future<LocalApiCommandResult> disableAutostart() =>
    _runScript('disable-research-os-autostart.ps1');

Future<LocalApiCommandResult> serviceStatus() => _runScript(
      'research-os-service.ps1',
      args: <String>['-Action', 'status', '-DataDir', _dataDir()],
    );

Future<LocalApiCommandResult> installService() =>
    _runElevatedServiceAction('install');
Future<LocalApiCommandResult> uninstallService() =>
    _runElevatedServiceAction('uninstall');
Future<LocalApiCommandResult> startService() =>
    _runElevatedServiceAction('start');
Future<LocalApiCommandResult> stopService() =>
    _runElevatedServiceAction('stop');
Future<LocalApiCommandResult> restartService() =>
    _runElevatedServiceAction('restart');

Future<LocalApiCommandResult> openDataFolder() async {
  if (!Platform.isWindows) {
    return const LocalApiCommandResult(
        ok: false, message: 'รองรับเฉพาะ Windows Desktop');
  }
  final dir = Directory(_dataDir());
  await dir.create(recursive: true);
  try {
    final result = await Process.run('explorer.exe', <String>[dir.path]);
    return LocalApiCommandResult(
      ok: result.exitCode == 0 || result.exitCode == 1,
      message: 'เปิดโฟลเดอร์ข้อมูลแล้ว',
      details: dir.path,
    );
  } on Object catch (error) {
    return LocalApiCommandResult(
        ok: false, message: 'เปิดโฟลเดอร์ไม่สำเร็จ', details: error.toString());
  }
}
