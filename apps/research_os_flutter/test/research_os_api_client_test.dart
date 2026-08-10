import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';

void main() {
  test('explicit API search instruction routes Chat to Compound Brain search', () async {
    late http.Request captured;
    final client = ResearchOSApiClient(
      baseUrl: 'http://127.0.0.1:8787',
      client: MockClient((request) async {
        captured = request;
        return http.Response(
          jsonEncode(<String, Object?>{
            'api_version': 'v2',
            'result': <String, Object?>{
              'provider': 'openai-responses',
              'model': 'test-model',
              'text': 'Verified answer',
              'sources': <Object?>[
                <String, String>{
                  'url': 'https://example.com/evidence',
                  'title': 'Evidence',
                },
              ],
            },
            'brain_plan': <String, Object?>{},
          }),
          200,
          headers: const <String, String>{'content-type': 'application/json'},
        );
      }),
    );

    final response = await client.answerWithMemory(
      'Conversation so far:\nAssistant: พร้อมช่วย\n\nUser: เรียก API ค้นเว็บข้อมูลล่าสุด',
    );

    expect(captured.url.path, '/v2/brain/search');
    final payload = jsonDecode(captured.body) as Map<String, dynamic>;
    expect(payload['query'], 'เรียก API ค้นเว็บข้อมูลล่าสุด');
    expect(response['text'], contains('Verified answer'));
    expect(response['text'], contains('[Evidence](https://example.com/evidence)'));
  });

  test('search command in old history does not force later turns to search', () async {
    late http.Request captured;
    final client = ResearchOSApiClient(
      baseUrl: 'http://127.0.0.1:8787',
      client: MockClient((request) async {
        captured = request;
        return http.Response(
          jsonEncode(<String, Object?>{'answer': 'Memory answer'}),
          200,
        );
      }),
    );

    await client.answerWithMemory(
      'Conversation so far:\nUser: เรียก API ค้นเว็บ\nAssistant: ผลค้นหา\n\nUser: อธิบายคำตอบเดิมต่อ',
    );

    expect(captured.url.path, '/v1/ai/answer-with-memory');
  });

  test('ordinary generation lets the service choose the configured provider', () async {
    late http.Request captured;
    final client = ResearchOSApiClient(
      baseUrl: 'http://127.0.0.1:8787',
      client: MockClient((request) async {
        captured = request;
        return http.Response(jsonEncode(<String, Object?>{'text': 'Answer'}), 200);
      }),
    );

    await client.generateText('ช่วยวางแผนโปรเจกต์');

    expect(captured.url.path, '/v1/ai/generate');
    final payload = jsonDecode(captured.body) as Map<String, dynamic>;
    expect(payload['prompt'], 'ช่วยวางแผนโปรเจกต์');
    expect(payload.containsKey('provider'), isFalse);
  });

  test('request header provider supplies fresh headers to every request', () async {
    var callCount = 0;
    final capturedNonces = <String>[];
    final client = ResearchOSApiClient(
      baseUrl: 'http://127.0.0.1:8787',
      requestHeadersProvider: () async {
        callCount += 1;
        return <String, String>{
          'X-ResearchOS-Principal': 'research-os-app',
          'X-ResearchOS-Identity-Nonce': 'nonce-$callCount',
          'X-ResearchOS-Identity-Timestamp': '$callCount',
          'X-ResearchOS-Identity-Signature': 'signature-$callCount',
        };
      },
      client: MockClient((request) async {
        capturedNonces.add(request.headers['X-ResearchOS-Identity-Nonce']!);
        return http.Response(jsonEncode(<String, Object?>{'status': 'ok'}), 200);
      }),
    );

    await client.getHealth();
    await client.getHealth();

    expect(callCount, 2);
    expect(capturedNonces, <String>['nonce-1', 'nonce-2']);
  });
}
