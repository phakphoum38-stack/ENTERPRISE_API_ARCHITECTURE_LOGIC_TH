import 'dart:io';

import '../models/repository_record.dart';
import 'settings_service.dart';

class RepositoryService {
  Future<List<RepositoryRecord>> listRepositories(String root, {String? owner}) async {
    final resolvedOwner = owner ?? (await SettingsService().load()).githubOwner;
    final ownerDir = Directory('$root\\github\\repositories\\$resolvedOwner');
    if (!await ownerDir.exists()) return const [];

    final records = <RepositoryRecord>[];
    await for (final entity in ownerDir.list(followLinks: false)) {
      if (entity is! Directory) continue;
      final name = entity.path.split(Platform.pathSeparator).last;
      final bundle = File('$root\\github\\bundles\\full\\$name.bundle');
      final mirror = File('$root\\github\\mirrors\\bare\\$name.git.zip');
      records.add(RepositoryRecord(
        name: name,
        folderPath: entity.path,
        hasBundle: await bundle.exists(),
        hasMirrorArchive: await mirror.exists(),
        snapshotFiles: await _countFiles(entity),
        bundleBytes: await bundle.exists() ? await bundle.length() : 0,
      ));
    }
    records.sort((a, b) => a.name.toLowerCase().compareTo(b.name.toLowerCase()));
    return records;
  }

  Future<void> openRepository(RepositoryRecord record) async {
    await Process.start('explorer.exe', [record.folderPath], runInShell: true);
  }

  Future<void> openBundle(String root, String name) async {
    final path = '$root\\github\\bundles\\full\\$name.bundle';
    if (!await File(path).exists()) throw StateError('ยังไม่มี bundle ของ $name');
    await Process.start('explorer.exe', ['/select,', path], runInShell: true);
  }

  Future<String> verifyBundle(String root, String name) async {
    final path = '$root\\github\\bundles\\full\\$name.bundle';
    if (!await File(path).exists()) throw StateError('ไม่พบ bundle ของ $name');
    final result = await Process.run('git', ['bundle', 'verify', path], runInShell: true);
    if (result.exitCode != 0) throw StateError('Bundle verify failed: ${result.stderr}');
    return 'Bundle $name ผ่านการตรวจสอบ';
  }

  Future<String> restoreBundle(String root, String name) async {
    final bundle = '$root\\github\\bundles\\full\\$name.bundle';
    if (!await File(bundle).exists()) throw StateError('ไม่พบ bundle ของ $name');
    final local = Platform.environment['LOCALAPPDATA'] ?? r'C:\Users\Public\AppData\Local';
    final restoreBase = Directory('$local\\ResearchOS\\restore-workspace');
    await restoreBase.create(recursive: true);
    final stamp = DateTime.now().toIso8601String().replaceAll(RegExp(r'[:.]'), '-');
    final destination = '${restoreBase.path}\\${name}_$stamp';
    final result = await Process.run('git', ['clone', bundle, destination], runInShell: true);
    if (result.exitCode != 0) throw StateError('Restore failed: ${result.stderr}');
    return destination;
  }

  Future<int> _countFiles(Directory directory) async {
    var count = 0;
    try {
      await for (final entity in directory.list(recursive: false, followLinks: false)) {
        if (entity is File) count++;
      }
    } catch (_) {}
    return count;
  }
}
