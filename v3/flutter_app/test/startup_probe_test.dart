import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_v3_flutter/src/api/v3_api.dart';
import 'package:research_os_v3_flutter/src/startup_probe.dart';

class FakeApi implements V3Api {
  int healthCalls = 0;
  int providerCalls = 0;
  int userCalls = 0;
  int chatCalls = 0;
  String? lastChatMessage;
  String? lastChatSessionId;
  String? lastChatProvider;
  String? lastChatMode;

  @override
  Future<Map<String, dynamic>> health() async {
    healthCalls++;
    return {'status': 'ok', 'version': 'v3-clean'};
  }

  @override
  Future<Map<String, dynamic>> master({int tasks = 1}) async {
    return {
      'contract': 'unified-master-orchestrator-v3-clean',
      'scale': '1^3',
      'maximum_leaf_capacity': 1,
    };
  }

  @override
  Future<Map<String, dynamic>> providers() async {
    providerCalls++;
    return {
      'providers': [
        {
          'name': 'mock',
          'ready': true,
          'connected': true,
          'secret_exposed': false,
        },
      ],
    };
  }

  @override
  Future<Map<String, dynamic>> user() async {
    userCalls++;
    return {
      'user_id': 'alice',
      'profile_id': 'default',
      'scope': 'users/alice/profiles/default',
      'isolated': true,
    };
  }

  @override
  Future<Map<String, dynamic>> chat(
    String message, {
    String sessionId = 'default',
    String provider = 'auto',
    String mode = 'answer',
  }) async {
    chatCalls++;
    lastChatMessage = message;
    lastChatSessionId = sessionId;
    lastChatProvider = provider;
    lastChatMode = mode;
    return {
      'contract': 'research-os-v3-chat-v1',
      'text': 'mock:$message',
      'provider': 'mock',
      'session_id': sessionId,
    };
  }
}

void main() {
  test('startup probe proves health user isolation and provider routes', () async {
    final api = FakeApi();

    final connected = await StartupProbe(
      api,
      attempts: 1,
      retryDelay: Duration.zero,
    ).run();

    expect(connected, isTrue);
    expect(api.healthCalls, 1);
    expect(api.userCalls, 1);
    expect(api.providerCalls, 1);
    expect(api.chatCalls, 0);
  });

  test('startup probe sends the installed executable chat proof', () async {
    final api = FakeApi();

    final connected = await StartupProbe(
      api,
      attempts: 1,
      retryDelay: Duration.zero,
      chatProbeMessage: 'installed-exe-e2e',
    ).run();

    expect(connected, isTrue);
    expect(api.healthCalls, 1);
    expect(api.userCalls, 1);
    expect(api.providerCalls, 1);
    expect(api.chatCalls, 1);
    expect(api.lastChatMessage, 'installed-exe-e2e');
    expect(api.lastChatSessionId, 'installed-app-e2e');
    expect(api.lastChatProvider, 'auto');
    expect(api.lastChatMode, 'answer');
  });
}
