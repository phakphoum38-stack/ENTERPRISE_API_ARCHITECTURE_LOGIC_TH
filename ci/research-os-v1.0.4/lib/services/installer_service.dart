import 'dart:convert';
import 'dart:io';

import '../models/system_snapshot.dart';
import 'settings_service.dart';

class InstallerService {
  static const rootName = 'DRIVE_VIRTUAL_CLOUD';
  static const bootstrapPath = r'C:\ProgramData\ResearchOS\cloud\bootstrap.json';
  static const legacyBootstrapPath = r'C:\ProgramData\DriveVirtualCloud\bootstrap.json';
  static const taskName = 'ResearchOSDriveCloudMirrorWorker';
  static const legacyTaskName = 'DriveVirtualCloudMirrorWorker';

  final SettingsService _settings = SettingsService();

  Future<String?> detectDriveRoot() async {
    if (!Platform.isWindows) return null;

    final settings = await _settings.load();
    final candidates = <String>[];
    if (settings.preferredRootPath.trim().isNotEmpty) {
      candidates.add(settings.preferredRootPath.trim());
    }

    var bootstrapFile = File(bootstrapPath);
    if (!await bootstrapFile.exists() && await File(legacyBootstrapPath).exists()) {
      bootstrapFile = File(legacyBootstrapPath);
    }
    if (await bootstrapFile.exists()) {
      try {
        final data = jsonDecode(await bootstrapFile.readAsString()) as Map<String, dynamic>;
        final saved = '${data['root_path'] ?? ''}'.trim();
        if (saved.isNotEmpty) candidates.add(saved);
      } catch (_) {}
    }

    candidates.addAll([
      r'G:\ไดรฟ์ของฉัน\DRIVE_VIRTUAL_CLOUD',
      r'G:\My Drive\DRIVE_VIRTUAL_CLOUD',
    ]);

    for (var code = 'D'.codeUnitAt(0); code <= 'Z'.codeUnitAt(0); code++) {
      final letter = String.fromCharCode(code);
      candidates.addAll([
        '$letter:\\ไดรฟ์ของฉัน\\$rootName',
        '$letter:\\My Drive\\$rootName',
        '$letter:\\$rootName',
      ]);
    }

    final seen = <String>{};
    for (final path in candidates) {
      if (!seen.add(path.toLowerCase())) continue;
      if (await Directory(path).exists()) return path;
    }
    return null;
  }

  Future<SystemSnapshot> inspectSystem() async {
    final root = await detectDriveRoot();
    var bootstrapFile = File(bootstrapPath);
    if (!await bootstrapFile.exists() && await File(legacyBootstrapPath).exists()) {
      bootstrapFile = File(legacyBootstrapPath);
    }
    Map<String, dynamic>? bootstrap;

    if (await bootstrapFile.exists()) {
      try {
        bootstrap = jsonDecode(await bootstrapFile.readAsString()) as Map<String, dynamic>;
      } catch (_) {}
    }

    final gitAvailable = await _commandAvailable('git', const ['--version']);
    final ghAvailable = await _commandAvailable('gh', const ['--version']);
    final githubAuthenticated = ghAvailable && await _commandAvailable('gh', const ['auth', 'status']);
    final workerState = await _getWorkerState();

    var bundleCount = 0;
    var mirrorCount = 0;
    var repositoryCount = 0;
    var restorePointCount = 0;
    var logs = <String>[];

    if (root != null) {
      bundleCount = await _countFiles('$root\\github\\bundles\\full', '.bundle');
      mirrorCount = await _countFiles('$root\\github\\mirrors\\bare', '.zip');
      final owner = (await _settings.load()).githubOwner;
      repositoryCount = await _countDirectories('$root\\github\\repositories\\$owner');
      restorePointCount = await _countFiles('$root\\backup\\restore_points', '');
      logs = await readRecentLogs(root: root);
    }

    return SystemSnapshot(
      rootPath: root,
      installed: await bootstrapFile.exists(),
      gitAvailable: gitAvailable,
      ghAvailable: ghAvailable,
      githubAuthenticated: githubAuthenticated,
      workerState: workerState,
      bundleCount: bundleCount,
      mirrorCount: mirrorCount,
      repositoryCount: repositoryCount,
      restorePointCount: restorePointCount,
      lastLogLines: logs,
      bootstrap: bootstrap,
    );
  }

  Future<String> install() async {
    if (!Platform.isWindows) throw UnsupportedError('รุ่นนี้รองรับ Windows ก่อน');
    final root = await detectDriveRoot();
    if (root == null) throw StateError('ไม่พบ DRIVE_VIRTUAL_CLOUD ใน Google Drive');

    final script = _assetScriptPath('bootstrap.ps1');
    if (!await File(script).exists()) throw StateError('ไม่พบ bootstrap.ps1 ใน Flutter assets');

    final result = await Process.run(
      'powershell.exe',
      [
        '-NoProfile',
        '-ExecutionPolicy',
        'Bypass',
        '-Command',
        'Start-Process PowerShell -Verb RunAs -Wait -ArgumentList @('
            "'-NoProfile','-ExecutionPolicy','Bypass','-File',"
            "'\"${_escapePs(script)}\"','-DriveRoot','\"${_escapePs(root)}\"')",
      ],
      runInShell: true,
    );
    if (result.exitCode != 0) {
      throw StateError('Bootstrap exit code ${result.exitCode}: ${result.stderr}');
    }
    return 'ติดตั้ง/ซ่อม Research OS Cloud Root สำเร็จ';
  }

  Future<String> runMirrorWorker() async {
    final result = await _powershell("\$name = if (Get-ScheduledTask -TaskName '$taskName' -ErrorAction SilentlyContinue) { '$taskName' } elseif (Get-ScheduledTask -TaskName '$legacyTaskName' -ErrorAction SilentlyContinue) { '$legacyTaskName' } else { throw 'Worker task not installed' }; Start-ScheduledTask -TaskName \$name -ErrorAction Stop; 'started'");
    if (result.exitCode != 0) throw StateError('เริ่ม Worker ไม่สำเร็จ: ${result.stderr}');
    return 'เริ่ม GitHub Mirror Worker แล้ว';
  }

  Future<String> stopMirrorWorker() async {
    final result = await _powershell("\$name = if (Get-ScheduledTask -TaskName '$taskName' -ErrorAction SilentlyContinue) { '$taskName' } elseif (Get-ScheduledTask -TaskName '$legacyTaskName' -ErrorAction SilentlyContinue) { '$legacyTaskName' } else { throw 'Worker task not installed' }; Stop-ScheduledTask -TaskName \$name -ErrorAction Stop; 'stopped'");
    if (result.exitCode != 0) throw StateError('หยุด Worker ไม่สำเร็จ: ${result.stderr}');
    return 'หยุด GitHub Mirror Worker แล้ว';
  }

  Future<String> openGithubLogin() async {
    if (!await _commandAvailable('gh', const ['--version'])) {
      throw StateError('ไม่พบ GitHub CLI (gh)');
    }
    await Process.start('cmd.exe', ['/k', 'gh auth login'], runInShell: true);
    return 'เปิด GitHub Login แล้ว';
  }

  Future<void> openRoot([String? root]) async {
    final path = root ?? await detectDriveRoot();
    if (path == null) throw StateError('ไม่พบ DRIVE_VIRTUAL_CLOUD');
    await Process.start('explorer.exe', [path], runInShell: true);
  }

  Future<void> openRelativeFolder(String relative, [String? root]) async {
    final path = root ?? await detectDriveRoot();
    if (path == null) throw StateError('ไม่พบ DRIVE_VIRTUAL_CLOUD');
    final full = '$path\\$relative';
    final directory = Directory(full);
    if (!await directory.exists()) await directory.create(recursive: true);
    await Process.start('explorer.exe', [full], runInShell: true);
  }

  Future<List<String>> readRecentLogs({String? root, int maxLines = 150}) async {
    final driveRoot = root ?? await detectDriveRoot();
    if (driveRoot == null) return const [];
    final logFile = File('$driveRoot\\logs\\github\\mirror-worker.log');
    if (!await logFile.exists()) return const [];
    try {
      final lines = await logFile.readAsLines();
      return lines.length <= maxLines ? lines : lines.sublist(lines.length - maxLines);
    } catch (_) {
      return const [];
    }
  }

  Future<ProcessResult> _powershell(String command) {
    return Process.run(
      'powershell.exe',
      ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', command],
      runInShell: true,
    );
  }

  Future<bool> _commandAvailable(String executable, List<String> arguments) async {
    try {
      final result = await Process.run(executable, arguments, runInShell: true);
      return result.exitCode == 0;
    } catch (_) {
      return false;
    }
  }

  Future<String> _getWorkerState() async {
    if (!Platform.isWindows) return 'Unsupported';
    try {
      final result = await _powershell(
        "\$task = Get-ScheduledTask -TaskName '$taskName' -ErrorAction SilentlyContinue; "
        "if (\$null -eq \$task) { \$task = Get-ScheduledTask -TaskName '$legacyTaskName' -ErrorAction SilentlyContinue }; "
        "if (\$null -eq \$task) { 'Not installed' } else { [string]\$task.State }",
      );
      if (result.exitCode != 0) return 'Unknown';
      final value = '${result.stdout}'.trim();
      return value.isEmpty ? 'Unknown' : value;
    } catch (_) {
      return 'Unknown';
    }
  }

  Future<int> _countFiles(String path, String extension) async {
    final directory = Directory(path);
    if (!await directory.exists()) return 0;
    try {
      var count = 0;
      await for (final entity in directory.list(followLinks: false)) {
        if (entity is File && (extension.isEmpty || entity.path.toLowerCase().endsWith(extension))) count++;
      }
      return count;
    } catch (_) {
      return 0;
    }
  }

  Future<int> _countDirectories(String path) async {
    final directory = Directory(path);
    if (!await directory.exists()) return 0;
    try {
      var count = 0;
      await for (final entity in directory.list(followLinks: false)) {
        if (entity is Directory) count++;
      }
      return count;
    } catch (_) {
      return 0;
    }
  }

  String _assetScriptPath(String name) {
    final appDir = File(Platform.resolvedExecutable).parent.path;
    return '$appDir\\data\\flutter_assets\\assets\\scripts\\$name';
  }

  String _escapePs(String value) => value.replaceAll("'", "''");
}
