import 'package:shared_preferences/shared_preferences.dart';

class ApiEndpointStore {
  ApiEndpointStore._();

  static const _storageKey = 'research_os_api_base_url_v1';
  static const localDefault = 'http://127.0.0.1:8787';
  static const renderDefault = 'https://research-os-api-phakphoum.onrender.com';

  static const buildDefault = String.fromEnvironment(
    'RESEARCH_OS_API_BASE_URL',
    defaultValue: localDefault,
  );

  static Future<String> load() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_storageKey)?.trim();
    return normalize(saved == null || saved.isEmpty ? buildDefault : saved);
  }

  static Future<void> save(String value) async {
    final normalized = normalize(value);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_storageKey, normalized);
  }

  static Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_storageKey);
  }

  static String normalize(String value) {
    var normalized = value.trim();
    while (normalized.endsWith('/')) {
      normalized = normalized.substring(0, normalized.length - 1);
    }
    final uri = Uri.tryParse(normalized);
    if (uri == null ||
        !uri.hasScheme ||
        (uri.scheme != 'http' && uri.scheme != 'https') ||
        uri.host.isEmpty) {
      throw const FormatException('API Base URL ต้องเป็น http:// หรือ https:// ที่ถูกต้อง');
    }
    return normalized;
  }
}
