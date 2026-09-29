import 'package:shared_preferences/shared_preferences.dart';

class ApiEndpointStore {
  ApiEndpointStore._();

  static const _storageKey = 'research_os_api_base_url_v1';
  static const localDefault = 'http://127.0.0.1:8787';
  static const developerDefault = 'http://127.0.0.1:8790';
  static const renderDefault = 'https://research-os-api-phakphoum.onrender.com';

  // Connection names remain internal; PORT labels are user-facing.
  static const connectionResearchOs = 'research_os';
  static const connectionOwnerSpecial = 'owner_special';
  static const connectionDeveloperRuntime = 'developer_runtime';

  static const port1Label = 'PORT 1';
  static const port2Label = 'PORT 2';

  static const loginWindows = 'windows';
  static const loginGitHub = 'github';
  static const loginGoogle = 'google';
  static const loginNone = 'none';
  static const loginCustom = 'custom';

  static const userLevelOwner = 'owner';
  static const userLevelDeveloper = 'developer';
  static const userLevelGeneral = 'general';

  static const developerBuildDefault = String.fromEnvironment(
    'RESEARCH_OS_DEVELOPER_BASE_URL',
    defaultValue: developerDefault,
  );

  static const buildDefault = String.fromEnvironment(
    'RESEARCH_OS_API_BASE_URL',
    defaultValue: renderDefault,
  );

  static const port1BuildDefault = String.fromEnvironment(
    'RESEARCH_OS_PORT_1_BASE_URL',
    defaultValue: buildDefault,
  );

  static const port2BuildDefault = String.fromEnvironment(
    'RESEARCH_OS_PORT_2_BASE_URL',
    defaultValue: developerDefault,
  );

  static String profileUrl(String profile) {
    switch (profile) {
      case connectionOwnerSpecial:
        return normalize(port2BuildDefault);
      case connectionDeveloperRuntime:
        return normalize(developerBuildDefault);
      case connectionResearchOs:
      default:
        return normalize(port1BuildDefault);
    }
  }

  static String portLabel(String profile) {
    switch (profile) {
      case connectionOwnerSpecial:
        return port2Label;
      case connectionResearchOs:
      default:
        return port1Label;
    }
  }

  static String profileForPortLabel(String label) {
    switch (label) {
      case port2Label:
        return connectionOwnerSpecial;
      case port1Label:
      default:
        return connectionResearchOs;
    }
  }

  static String profileLabel(String profile) {
    switch (profile) {
      case connectionOwnerSpecial:
        return port2Label;
      case connectionDeveloperRuntime:
        return 'Developer Runtime';
      case connectionResearchOs:
      default:
        return port1Label;
    }
  }

  static String profileForUrl(String url) {
    final normalized = normalize(url);

    if (normalized == profileUrl(connectionOwnerSpecial)) {
      return connectionOwnerSpecial;
    }

    if (normalized == profileUrl(connectionDeveloperRuntime)) {
      return connectionDeveloperRuntime;
    }

    if (normalized == profileUrl(connectionResearchOs)) {
      return connectionResearchOs;
    }

    return 'custom';
  }

  static Future<String> load() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_storageKey)?.trim();

    if (saved == null || saved.isEmpty) {
      return normalize(profileUrl(connectionResearchOs));
    }

    final normalized = normalize(saved);

    // Migrate older Windows builds that persisted the development loopback
    // endpoint when the canonical PORT 1 endpoint is different.
    if (normalized == localDefault && port1BuildDefault != localDefault) {
      await prefs.setString(_storageKey, port1BuildDefault);
      return normalize(port1BuildDefault);
    }

    return normalized;
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
      throw const FormatException(
        'API Base URL ???????? http:// ???? https:// ??????????',
      );
    }
    return normalized;
  }
}
