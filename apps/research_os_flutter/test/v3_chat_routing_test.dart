import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';

void main() {
  test('desktop chat routes through the V3 unified chat endpoint', () async {
    final requests = <http.Request>[];
    final client = MockClient((request) async {
      requests.add(request);
      return http.Response(
        jsonEncode(<String, Object?>{
          'text': 'v3-ok',
          'provider': 'mock',
          'model': 'mock',
          'memory_hits': <Object?>[],
        }),
        200,
        headers: <String, String>{'content-type': 'application/json'},
      );
    });
    final api = ResearchOSApiClient(
      baseUrl: 'http://127.0.0.1:8787',
      v3BaseUrl: 'http://127.0.0.1:8788',
      userId: 'desktop-user',
      profileId: 'default',
      client: client,
    );

    final withoutMemory = await api.generateText('hello');
    final withMemory = await api.answerWithMemory('remember this');

    expect(withoutMemory['text'], 'v3-ok');
    expect(withMemory['text'], 'v3-ok');
    expect(requests, hasLength(2));
    for (final request in requests) {
      expect(request.url.toString(), 'http://127.0.0.1:8788/v3/chat');
      expect(request.headers['X-Research-OS-User'], 'desktop-user');
      expect(request.headers['X-Research-OS-Profile'], 'default');
      final body = jsonDecode(request.body) as Map<String, dynamic>;
      expect(body['prompt'], isNotEmpty);
    }
    expect((jsonDecode(requests[0].body) as Map<String, dynamic>)['memory_limit'], 0);
    expect((jsonDecode(requests[1].body) as Map<String, dynamic>)['memory_limit'], 8);
  });
}
