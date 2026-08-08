import '../api/api_connection_preferences.dart';
import 'identity_api_client.dart';
import 'owner_session_store.dart';

class OwnerCloudSync {
  OwnerCloudSync._();

  static Future<void> pushConnectionPreferences(
    ApiConnectionPreferences preferences,
  ) async {
    final session = ownerSessionState.value;
    if (session == null || session.expired) return;
    final client = IdentityApiClient();
    try {
      await client.updatePreferences(session.token, <String, Object?>{
        'api_auto_discovery': preferences.autoDiscovery,
        'api_scan_lan': preferences.scanLan,
        'heartbeat_seconds': preferences.heartbeatSeconds,
      });
    } on Object {
      // Cloud preference sync is best-effort. Local settings remain authoritative
      // while offline and will be pushed again after the next local change.
    } finally {
      client.close();
    }
  }

  static Future<ApiConnectionPreferences?> pullConnectionPreferences() async {
    final session = ownerSessionState.value;
    if (session == null || session.expired) return null;
    final client = IdentityApiClient();
    try {
      final payload = await client.getProfile(session.token);
      final preferences = payload['preferences'];
      if (preferences is! Map<String, dynamic>) return null;
      final current = await ApiConnectionPreferences.load();
      final heartbeatRaw = preferences['heartbeat_seconds'];
      final heartbeat = heartbeatRaw is num
          ? heartbeatRaw.toInt().clamp(5, 300)
          : current.heartbeatSeconds;
      final merged = current.copyWith(
        autoDiscovery: preferences['api_auto_discovery'] is bool
            ? preferences['api_auto_discovery'] as bool
            : current.autoDiscovery,
        scanLan: preferences['api_scan_lan'] is bool
            ? preferences['api_scan_lan'] as bool
            : current.scanLan,
        heartbeatSeconds: heartbeat,
      );
      await merged.save();
      return merged;
    } on Object {
      return null;
    } finally {
      client.close();
    }
  }
}
