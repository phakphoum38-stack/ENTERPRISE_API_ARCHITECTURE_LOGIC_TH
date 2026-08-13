import 'dart:convert';
import 'dart:io';

import '../models/provider_profile.dart';

class ProviderService {
  String get providerPath {
    final base = Platform.environment['LOCALAPPDATA'] ?? r'C:\Users\Public\AppData\Local';
    return '$base\\ResearchOS\\config\\providers.json';
  }

  Future<List<ProviderProfile>> loadProviders() async {
    final file = File(providerPath);
    if (!await file.exists()) return const [];
    try {
      final raw = jsonDecode(await file.readAsString()) as Map<String, dynamic>;
      final list = (raw['providers'] as List<dynamic>? ?? const []);
      final providers = <ProviderProfile>[];
      for (final item in list) {
        final profile = ProviderProfile.fromJson(Map<String, dynamic>.from(item as Map));
        providers.add(profile.copyWith(keyStored: await hasSecret(profile.id)));
      }
      return providers;
    } catch (_) {
      return const [];
    }
  }

  Future<void> saveProviders(List<ProviderProfile> providers) async {
    final file = File(providerPath);
    await file.parent.create(recursive: true);
    const encoder = JsonEncoder.withIndent('  ');
    await file.writeAsString(
      encoder.convert({'providers': providers.map((e) => e.toJson()).toList()}),
      flush: true,
    );
  }

  Future<void> upsertProvider(ProviderProfile profile, {String? secret}) async {
    final providers = await loadProviders();
    final index = providers.indexWhere((p) => p.id == profile.id);
    if (index >= 0) {
      providers[index] = profile;
    } else {
      providers.add(profile);
    }
    await saveProviders(providers);
    if (secret != null && secret.trim().isNotEmpty) await saveSecret(profile.id, secret.trim());
  }

  Future<void> deleteProvider(String id) async {
    final providers = await loadProviders();
    providers.removeWhere((p) => p.id == id);
    await saveProviders(providers);
    await deleteSecret(id);
  }

  Future<void> saveSecret(String id, String secret) async {
    final encoded = base64Encode(utf8.encode(secret));
    final result = await _runVault('set', id, secretBase64: encoded);
    if (result.exitCode != 0) throw StateError('บันทึก API key ไม่สำเร็จ: ${result.stderr}');
  }

  Future<String?> readSecret(String id) async {
    final result = await _runVault('get', id);
    if (result.exitCode == 3) return null;
    if (result.exitCode != 0) throw StateError('อ่าน API key ไม่สำเร็จ: ${result.stderr}');
    final value = '${result.stdout}'.trim();
    if (value.isEmpty) return null;
    return utf8.decode(base64Decode(value));
  }

  Future<bool> hasSecret(String id) async {
    final result = await _runVault('exists', id);
    return result.exitCode == 0 && '${result.stdout}'.trim().toLowerCase() == 'true';
  }

  Future<void> deleteSecret(String id) async {
    await _runVault('delete', id);
  }

  Future<String> testProvider(ProviderProfile provider) async {
    final uri = Uri.parse('${_normalizeBase(provider.baseUrl)}/models');
    final client = HttpClient()..connectionTimeout = const Duration(seconds: 12);
    try {
      final request = await client.getUrl(uri).timeout(const Duration(seconds: 12));
      final secret = await readSecret(provider.id);
      if (secret != null && secret.isNotEmpty) request.headers.set(HttpHeaders.authorizationHeader, 'Bearer $secret');
      request.headers.set(HttpHeaders.acceptHeader, 'application/json');
      final response = await request.close().timeout(const Duration(seconds: 15));
      final body = await utf8.decoder.bind(response).join();
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return 'เชื่อมต่อสำเร็จ • HTTP ${response.statusCode}';
      }
      final short = body.length > 220 ? '${body.substring(0, 220)}…' : body;
      throw StateError('HTTP ${response.statusCode}: $short');
    } finally {
      client.close(force: true);
    }
  }

  Future<ProcessResult> _runVault(String action, String id, {String secretBase64 = ''}) async {
    if (!Platform.isWindows) throw UnsupportedError('Provider vault รองรับ Windows ก่อน');
    final script = _assetScriptPath('provider-vault.ps1');
    if (!await File(script).exists()) throw StateError('ไม่พบ provider-vault.ps1');
    return Process.run(
      'powershell.exe',
      [
        '-NoProfile',
        '-NonInteractive',
        '-ExecutionPolicy',
        'Bypass',
        '-File',
        script,
        '-Action',
        action,
        '-Id',
        id,
        if (secretBase64.isNotEmpty) ...['-SecretBase64', secretBase64],
      ],
      runInShell: false,
    );
  }

  String _assetScriptPath(String name) {
    final appDir = File(Platform.resolvedExecutable).parent.path;
    return '$appDir\\data\\flutter_assets\\assets\\scripts\\$name';
  }

  String _normalizeBase(String value) => value.trim().replaceAll(RegExp(r'/+$'), '');
}
