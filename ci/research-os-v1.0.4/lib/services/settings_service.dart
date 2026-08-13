import 'dart:convert';
import 'dart:io';

import '../models/app_settings.dart';

class SettingsService {
  String get settingsPath {
    final base = Platform.environment['LOCALAPPDATA'] ?? r'C:\Users\Public\AppData\Local';
    return '$base\\ResearchOS\\config\\settings.json';
  }

  Future<AppSettings> load() async {
    if (!Platform.isWindows) return const AppSettings();
    final file = File(settingsPath);
    if (!await file.exists()) return const AppSettings();
    try {
      final json = jsonDecode(await file.readAsString()) as Map<String, dynamic>;
      return AppSettings.fromJson(json);
    } catch (_) {
      return const AppSettings();
    }
  }

  Future<void> save(AppSettings settings) async {
    final file = File(settingsPath);
    await file.parent.create(recursive: true);
    const encoder = JsonEncoder.withIndent('  ');
    await file.writeAsString(encoder.convert(settings.toJson()), flush: true);
  }
}
