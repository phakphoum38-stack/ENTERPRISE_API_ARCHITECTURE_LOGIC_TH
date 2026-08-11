import 'dart:io';

import 'package:research_os_flutter/src/api/research_os_api_client.dart';

Future<void> main() async {
  final baseUrl = Platform.environment['RESEARCH_OS_API_BASE_URL'] ??
      'http://127.0.0.1:8787';
  final expectedProvider =
      Platform.environment['RESEARCH_OS_EXPECTED_PROVIDER']?.trim();
  final api = ResearchOSApiClient(baseUrl: baseUrl);

  try {
    final health = await api.getHealth();
    if (health['status'] != 'ok') {
      throw StateError('health endpoint is not ok');
    }

    final providers = await api.getProviders();
    final activeProvider = providers['active']?.toString();
    if (expectedProvider != null &&
        expectedProvider.isNotEmpty &&
        activeProvider != expectedProvider) {
      throw StateError(
        'active provider mismatch: expected $expectedProvider, got $activeProvider',
      );
    }

    final generation = await api.generateText(
      'Connectivity test. Reply with exactly CHAT-E2E-READY and no extra text.',
    );
    final generationText = generation['text']?.toString().trim() ?? '';
    if (generationText.isEmpty) {
      throw StateError('live generation returned empty text');
    }
    if (expectedProvider != null &&
        expectedProvider.isNotEmpty &&
        generation['provider']?.toString() != expectedProvider) {
      throw StateError('generation did not use expected provider');
    }

    final memoryAnswer = await api.answerWithMemory(
      'Conversation so far:\n'
      'User: รหัสสำหรับทดสอบบริบทคือ KITE-731\n'
      'Assistant: รับทราบรหัส KITE-731\n\n'
      'User: รหัสสำหรับทดสอบบริบทคืออะไร? ตอบเฉพาะรหัส',
    );
    final memoryText = memoryAnswer['text']?.toString() ?? '';
    if (!memoryText.contains('KITE-731')) {
      throw StateError('answer-with-memory lost the supplied conversation context');
    }

    stdout.writeln('CHAT_CLIENT_SERVICE_E2E=PASS');
    stdout.writeln('ACTIVE_PROVIDER=${activeProvider ?? 'unknown'}');
    stdout.writeln('GENERATION_RESPONSE_RECEIVED=true');
    stdout.writeln('CONTEXT_RESPONSE_CONTAINS_MARKER=true');
  } finally {
    api.close();
  }
}
