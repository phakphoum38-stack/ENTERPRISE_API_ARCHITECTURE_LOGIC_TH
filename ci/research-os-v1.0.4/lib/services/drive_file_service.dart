import 'dart:io';

import '../models/drive_entry.dart';

class DriveFileService {
  Future<List<DriveEntry>> list(String directoryPath) async {
    final dir = Directory(directoryPath);
    if (!await dir.exists()) return const [];
    final entries = <DriveEntry>[];
    await for (final entity in dir.list(followLinks: false)) {
      final stat = await entity.stat();
      final name = entity.path.split(Platform.pathSeparator).last;
      entries.add(DriveEntry(
        name: name,
        path: entity.path,
        isDirectory: entity is Directory,
        sizeBytes: entity is File ? stat.size : 0,
        modifiedAt: stat.modified,
      ));
    }
    entries.sort((a, b) {
      if (a.isDirectory != b.isDirectory) return a.isDirectory ? -1 : 1;
      return a.name.toLowerCase().compareTo(b.name.toLowerCase());
    });
    return entries;
  }

  Future<void> open(DriveEntry entry) async {
    if (entry.isDirectory) {
      await Process.start('explorer.exe', [entry.path], runInShell: true);
    } else {
      await Process.start('explorer.exe', ['/select,', entry.path], runInShell: true);
    }
  }
}
