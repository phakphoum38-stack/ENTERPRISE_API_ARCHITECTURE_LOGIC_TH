import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';

void main() {
  test('AI requests defer to service active provider by default', () async {
    final requests = <http.Request>[];
    final client = MockClient((request) async {
      requests.add(request);
      return http.Response(
        jsonEncode(<String, Object?>{
          'provider': 'gemini',
          'model': 'test-model',
          'text': 'ok',
          'memory_hits': <Object?>[],
        }),
        200,
        headers: <String, String>{'content-type': 'application/json'},
      );
    });
    final api = ResearchOSApiClient(
      baseUrl: 'http://127.0.0.1:8787',
      client: client,
    );

    await api.generateText('hello');
    await api.answerWithMemory('remember this');

    expect(requests, hasLength(2));
    final generate = jsonDecode(requests[0].body) as Map<String, dynamic>;
    final memory = jsonDecode(requests[1].body) as Map<String, dynamic>;
    expect(generate['prompt'], 'hello');
    expect(memory['question'], 'remember this');
    expect(generate.containsKey('provider'), isFalse);
    expect(memory.containsKey('provider'), isFalse);
    api.close();
  });

  test('explicit preferred provider is preserved when requested', () async {
    late http.Request captured;
    final client = MockClient((request) async {
      captured = request;
      return http.Response(
        jsonEncode(<String, Object?>{
          'provider': 'openai-compatible',
          'model': 'test-model',
          'text': 'ok',
        }),
        200,
      );
    });
    final api = ResearchOSApiClient(
      baseUrl: 'http://127.0.0.1:8787',
      client: client,
      preferredProvider: 'openai-compatible',
    );

    await api.generateText('hello');

    final payload = jsonDecode(captured.body) as Map<String, dynamic>;
    expect(payload['provider'], 'openai-compatible');
    expect(payload['prompt'], 'hello');
    api.close();
  });
}
