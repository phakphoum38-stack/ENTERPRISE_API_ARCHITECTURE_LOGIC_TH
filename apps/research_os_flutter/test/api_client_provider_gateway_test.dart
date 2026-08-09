import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';

void main() {
  test('provider gateway status uses V2 endpoint', () async {
    late Uri requested;
    final client = MockClient((request) async {
      requested = request.url;
      return http.Response(
        jsonEncode(<String, Object?>{
          'api_version': 'v2',
          'gateway': <String, Object?>{
            'selected': <String, Object?>{
              'provider': 'local',
              'source': 'localhost-probe',
              'reason': 'first ready provider by local-first policy',
            },
            'providers': <Object?>[],
            'registry': <Object?>[],
            'safe': true,
          },
        }),
        200,
      );
    });
    final api = ResearchOSApiClient(baseUrl: 'http://127.0.0.1:8787', client: client);

    final payload = await api.getProviderGateway();

    expect(requested.path, '/v2/providers');
    expect((payload['gateway'] as Map)['safe'], isTrue);
  });

  test('generateText does not hard-code Gemini provider', () async {
    Map<String, dynamic>? body;
    final client = MockClient((request) async {
      body = jsonDecode(request.body) as Map<String, dynamic>;
      return http.Response(
        jsonEncode(<String, Object?>{
          'provider': 'local',
          'model': 'local-model',
          'text': 'ok',
        }),
        200,
      );
    });
    final api = ResearchOSApiClient(baseUrl: 'http://127.0.0.1:8787', client: client);

    await api.generateText('hello');

    expect(body?['prompt'], 'hello');
    expect(body?.containsKey('provider'), isFalse);
  });

  test('answerWithMemory leaves provider selection to backend', () async {
    Map<String, dynamic>? body;
    final client = MockClient((request) async {
      body = jsonDecode(request.body) as Map<String, dynamic>;
      return http.Response(
        jsonEncode(<String, Object?>{
          'provider': 'mock',
          'model': 'mock-v1',
          'text': 'answer',
          'memory_hits': <Object?>[],
          'memory_count': 0,
        }),
        200,
      );
    });
    final api = ResearchOSApiClient(baseUrl: 'http://127.0.0.1:8787', client: client);

    await api.answerWithMemory('question');

    expect(body?['question'], 'question');
    expect(body?.containsKey('provider'), isFalse);
  });
}
