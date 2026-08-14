import 'dart:async';

import 'api/v3_api.dart';

final class StartupProbe {
  StartupProbe(
    this.api, {
    this.attempts = 12,
    this.retryDelay = const Duration(milliseconds: 300),
    this.chatProbeMessage,
  });

  final V3Api api;
  final int attempts;
  final Duration retryDelay;
  final String? chatProbeMessage;

  Future<bool> run() async {
    for (var attempt = 0; attempt < attempts; attempt++) {
      try {
        final health = await api.health();
        final user = await api.user();
        final providers = await api.providers();
        final providerList = providers['providers'];
        if (health['status'] == 'ok' &&
            user['isolated'] == true &&
            providerList is List) {
          final probe = chatProbeMessage?.trim();
          if (probe != null && probe.isNotEmpty) {
            final chat = await api.chat(
              probe,
              sessionId: 'installed-app-e2e',
              provider: 'auto',
              mode: 'answer',
            );
            if (chat['contract'] != 'research-os-v3-chat-v1') {
              throw StateError('unexpected V3 chat contract');
            }
          }
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
