import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';

void main() {
  test('AI Brain health uses read-only V2 intelligence endpoint', () async {
    late Uri requested;
    final client = MockClient((request) async {
      requested = request.url;
      return http.Response(
        jsonEncode(<String, Object?>{
          'api_version': 'v2',
          'ready': true,
          'counts': <String, Object?>{},
        }),
        200,
      );
    });
    final api = ResearchOSApiClient(
      baseUrl: 'http://127.0.0.1:8787',
      client: client,
    );

    await api.getIntelligenceHealth();

    expect(requested.path, '/v2/intelligence/health');
  });

  test('skill and tool discovery encode bounded read-only filters', () async {
    final requested = <Uri>[];
    final client = MockClient((request) async {
      requested.add(request.url);
      return http.Response(
        jsonEncode(<String, Object?>{
          'api_version': 'v2',
          if (request.url.path.endsWith('/skills')) 'skills': <Object?>[],
          if (request.url.path.endsWith('/tools')) 'tools': <Object?>[],
          'count': 0,
        }),
        200,
      );
    });
    final api = ResearchOSApiClient(
      baseUrl: 'http://127.0.0.1:8787',
      client: client,
    );

    await api.getIntelligenceSkills(
      capability: 'debug',
      permission: 'workspace.read',
    );
    await api.getIntelligenceTools(
      capability: 'code_search',
      readyOnly: false,
    );

    expect(requested[0].path, '/v2/intelligence/skills');
    expect(requested[0].queryParameters['capability'], 'debug');
    expect(requested[0].queryParameters['permission'], 'workspace.read');
    expect(requested[0].queryParameters['ready_only'], 'true');
    expect(requested[1].path, '/v2/intelligence/tools');
    expect(requested[1].queryParameters['capability'], 'code_search');
    expect(requested[1].queryParameters['ready_only'], 'false');
  });

  test('Brain plan preview posts objective/context without execute control', () async {
    late Uri requested;
    late Map<String, dynamic> body;
    final client = MockClient((request) async {
      requested = request.url;
      body = jsonDecode(request.body) as Map<String, dynamic>;
      return http.Response(
        jsonEncode(<String, Object?>{
          'api_version': 'v2',
          'read_only': true,
          'execution_performed': false,
          'result': <String, Object?>{
            'plan': <String, Object?>{
              'goal': body['objective'],
              'required_capabilities': <String>['debug'],
            },
          },
        }),
        200,
      );
    });
    final api = ResearchOSApiClient(
      baseUrl: 'http://127.0.0.1:8787',
      client: client,
    );

    final payload = await api.planIntelligence(
      'debug CI',
      sessionId: 'brain-inspector',
      context: const <String, Object?>{'surface': 'agent_center'},
    );

    expect(requested.path, '/v2/intelligence/plan');
    expect(body['objective'], 'debug CI');
    expect(body['session_id'], 'brain-inspector');
    expect((body['context'] as Map)['surface'], 'agent_center');
    expect(body.containsKey('execute'), isFalse);
    expect(body.containsKey('approved'), isFalse);
    expect(payload['execution_performed'], isFalse);
  });
}
