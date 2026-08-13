import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_v3_flutter/src/api/v3_api.dart';
import 'package:research_os_v3_flutter/src/startup_probe.dart';

class FakeApi implements V3Api {
  int healthCalls = 0;
  int providerCalls = 0;
  int userCalls = 0;

  @override
  Future<Map<String, dynamic>> health() async {
    healthCalls++;
    return {
      'status': 'ok',
      'version': 'v3-full-10x10',
      'maximum_scale': '10^10',
      'maximum_logical_capacity': 10000000000,
    };
  }

  @override
  Future<Map<String, dynamic>> master({
    int tasks = 1,
    int risk = 1,
    int parallelism = 1,
  }) async => {
        'contract': 'unified-master-orchestrator-v3-full',
        'scale': '3^1',
        'maximum_leaf_capacity': 3,
      };

  @override
  Future<Map<String, dynamic>> providers() async {
    providerCalls++;
    return {
      'providers': [
        {'name': 'mock', 'ready': true, 'connected': true, 'secret_exposed': false},
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
  Future<Map<String, dynamic>> skills() async => {'skills': <Map<String, dynamic>>[]};

  @override
  Future<Map<String, dynamic>> tools() async => {'tools': <Map<String, dynamic>>[]};

  @override
  Future<Map<String, dynamic>> agents() async => {'agents': <Map<String, dynamic>>[]};

  @override
  Future<Map<String, dynamic>> memory({String query = '', int limit = 20}) async =>
      {'memory': <Map<String, dynamic>>[]};

  @override
  Future<Map<String, dynamic>> factoryPlan({
    int tasks = 1,
    int risk = 1,
    int parallelism = 1,
  }) async => {
        'scale': '3^1',
        'maximum_leaf_capacity': 3,
        'stage_order': ['master', 'factory', 'team', 'tests', 'release'],
        'decision': {'system_maximum_scale': '10^10'},
      };

  @override
  Future<Map<String, dynamic>> chat(
    String prompt, {
    String? agent,
    String? preferredProvider,
    int memoryLimit = 8,
  }) async => {'text': prompt, 'provider': 'mock', 'model': 'mock', 'memory_hits': []};

  @override
  Future<Map<String, dynamic>> addMemory(
    String text, {
    List<String> tags = const <String>[],
  }) async => {'memory': {'text': text}};

  @override
  Future<Map<String, dynamic>> runAgent(String name, String prompt) async =>
      {'agent': name, 'text': prompt};

  @override
  Future<Map<String, dynamic>> executeTool(
    String name,
    Map<String, dynamic> arguments, {
    bool approved = false,
  }) async => {'tool': name, 'result': arguments};
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
  });
}
