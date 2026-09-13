import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_owner_special/src/owner_api.dart';

void main() {
  test('Friend chat calls API Platform with session-scoped JSON', () async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    addTearDown(server.close);

    final handled = server.first.then((request) async {
      expect(request.method, 'POST');
      expect(request.uri.path, '/v1/ai/generate');
      expect(request.headers.value('X-Research-OS-Owner'), isNull);
      expect(request.headers.value('X-Research-OS-Profile'), isNull);
      expect(request.headers.value('X-Research-OS-Session'), 'research-session');

      final declaredLength = int.tryParse(
        request.headers.value(HttpHeaders.contentLengthHeader) ?? '',
      );
      expect(declaredLength, isNotNull);
      expect(declaredLength, greaterThan(0));

      final bodyText = await utf8.decoder.bind(request).join();
      expect(utf8.encode(bodyText).length, declaredLength);
      final body = jsonDecode(bodyText) as Map<String, dynamic>;
      expect(body['prompt'], 'hello friend');
      expect(body['complexity'], 6);
      expect(body['helper_budget'], 1000000);
      expect(body['session_id'], 'desktop-test');

      request.response.statusCode = HttpStatus.ok;
      request.response.headers.contentType = ContentType.json;
      request.response.write(jsonEncode(<String, dynamic>{
        'text': 'hello owner',
        'provider': 'mock',
        'model': 'friend-unified-master',
        'route': 'friend',
        'decision': <String, dynamic>{
          'scale': '6^6',
          'capacity': 46656,
          'plan': <String>[],
          'skills': <String>[],
          'tools': <String>[],
          'summary': 'test',
        },
        'helpers': <String, dynamic>{'active_workers': 1, 'batches': 1},
        'factory': <String, dynamic>{
          'available': true,
          'scale': '6^6',
          'stages': <String>['master', 'factory', 'team', 'tests', 'release'],
        },
        'metadata': <String, dynamic>{'edition': 'owner-special'},
      }));
      await request.response.close();
    });

    final api = HttpOwnerFriendApi(
      baseUrl: 'http://127.0.0.1:9999',
      ownerId: 'owner',
      profileId: 'work',
      sessionId: 'desktop-test',
      researchOsBaseUrl: 'http://127.0.0.1:${server.port}',
    );
    api.setSession('research-session');

    final response = await api.chat(
      'hello friend',
      complexity: 6,
      helperBudget: 1000000,
    );
    expect(response['text'], 'hello owner');
    expect(response['route'], 'friend');
    await handled;
  });
}
