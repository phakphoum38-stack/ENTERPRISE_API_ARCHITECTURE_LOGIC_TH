import 'dart:async';

import 'api/v3_api.dart';

final class StartupProbe {
  StartupProbe(
    this.api, {
    this.attempts = 12,
    this.retryDelay = const Duration(milliseconds: 300),
  });

  final V3Api api;
  final int attempts;
  final Duration retryDelay;

  Future<bool> run() async {
    for (var attempt = 0; attempt < attempts; attempt++) {
      try {
        final health = await api.health();
        final providers = await api.providers();
        final providerList = providers['providers'];
        if (health['status'] == 'ok' && providerList is List) {
          return true;
        }
      } catch (_) {
        // Startup connectivity is best-effort. The visible shell can retry.
      }
      if (attempt + 1 < attempts) {
        await Future<void>.delayed(retryDelay);
      }
    }
    return false;
  }
}
