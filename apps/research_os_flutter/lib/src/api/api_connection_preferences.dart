import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiConnectionPreferences {
  const ApiConnectionPreferences({
    required this.autoDiscovery,
    required this.scanLan,
    required this.heartbeatSeconds,
  });

  static const defaults = ApiConnectionPreferences(
    autoDiscovery: true,
    scanLan: true,
    heartbeatSeconds: 20,
  );

  static const _autoDiscoveryKey = 'research_os_api_auto_discovery_v1';
  static const _scanLanKey = 'research_os_api_scan_lan_v1';
  static const _heartbeatKey = 'research_os_api_heartbeat_seconds_v1';

  final bool autoDiscovery;
  final bool scanLan;
  final int heartbeatSeconds;

  Duration get heartbeatInterval => Duration(seconds: heartbeatSeconds);

  ApiConnectionPreferences copyWith({
    bool? autoDiscovery,
    bool? scanLan,
    int? heartbeatSeconds,
  }) {
    return ApiConnectionPreferences(
      autoDiscovery: autoDiscovery ?? this.autoDiscovery,
      scanLan: scanLan ?? this.scanLan,
      heartbeatSeconds: heartbeatSeconds ?? this.heartbeatSeconds,
    );
  }

  static Future<ApiConnectionPreferences> load() async {
    final prefs = await SharedPreferences.getInstance();
    final heartbeat = prefs.getInt(_heartbeatKey) ?? defaults.heartbeatSeconds;
    return ApiConnectionPreferences(
      autoDiscovery: prefs.getBool(_autoDiscoveryKey) ?? defaults.autoDiscovery,
      scanLan: prefs.getBool(_scanLanKey) ?? defaults.scanLan,
      heartbeatSeconds: heartbeat.clamp(5, 300),
    );
  }

  Future<void> save() async {
    final prefs = await SharedPreferences.getInstance();
    await Future.wait<void>(<Future<void>>[
      prefs.setBool(_autoDiscoveryKey, autoDiscovery),
      prefs.setBool(_scanLanKey, scanLan),
      prefs.setInt(_heartbeatKey, heartbeatSeconds.clamp(5, 300)),
    ]);
    apiConnectionPreferences.value = this;
  }
}

final ValueNotifier<ApiConnectionPreferences> apiConnectionPreferences =
    ValueNotifier<ApiConnectionPreferences>(ApiConnectionPreferences.defaults);
