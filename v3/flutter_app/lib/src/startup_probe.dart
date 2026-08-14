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

  String? lastError;

  Future<bool> run() async {
    lastError = null;
    for (var attempt = 0; attempt < attempts; attempt++) {
      try {
        final health = await api.health();
        final user = await api.user();
        final providers = await api.providers();

        final probe = chatProbeMessage?.trim();
        Map<String, dynamic>? chat;
        if (probe != null && probe.isNotEmpty) {
          // The installed-binary proof must reach /v3/chat even when one of the
          // preceding response schemas is unexpectedly shaped. We validate all
          // contracts after the HTTP calls so CI can distinguish routing from a
          // semantic contract regression instead of silently stopping at providers.
          chat = await api.chat(
            probe,
            sessionId: 'installed-app-e2e',
            provider: 'auto',
            mode: 'answer',
          );
        }

        final healthOk = health['status'] == 'ok';
        final userOk = user['isolated'] == true;
        final providersOk = providers['providers'] is List;
        final chatOk = probe == null ||
            probe.isEmpty ||
            chat?['contract'] == 'research-os-v3-chat-v1';

        if (healthOk && userOk && providersOk && chatOk) {
          return true;
        }

        final failures = <String>[
          if (!healthOk) 'health.status',
          if (!userOk) 'user.isolated',
          if (!providersOk) 'providers.providers',
          if (!chatOk) 'chat.contract',
        ];
        throw StateError(
          'startup contract mismatch: ${failures.join(', ')}',
        );
      } catch (error) {
        lastError = error.toString();
      }
      if (attempt + 1 < attempts) {
        await Future<void>.delayed(retryDelay);
      }
    }
    return false;
  }
}
