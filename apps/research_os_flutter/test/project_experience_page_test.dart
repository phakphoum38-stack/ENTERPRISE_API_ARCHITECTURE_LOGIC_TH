import 'dart:convert';

import 'package:flutter/material.dart';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/projects/project_experience_page.dart';

void main() {
  test('ResearchOSApiClient reads the canonical project registry endpoint', () async {
    final requests = <http.Request>[];
    final client = MockClient((request) async {
      requests.add(request);
      return http.Response(
        jsonEncode(<String, Object?>{
          'projects': <Object?>[
            <String, Object?>{
              'project_id': 'project-001',
              'display_name': 'Research OS Reference Project',
              'version': '1.0.0',
              'capabilities': <String>['agent', 'control_center'],
              'release_authority': 'FINAL_GATE',
            },
          ],
          'configured_count': 1,
          'supported_project_contexts': 100,
          'scale_levels': <int>[10, 20, 50, 100],
        }),
        200,
      );
    });
    final api = ResearchOSApiClient(baseUrl: 'http://127.0.0.1:8787', client: client);

    final result = await api.getProjects();

    expect(requests.single.url.path, '/v1/projects');
    expect(result['configured_count'], 1);
    expect(result['supported_project_contexts'], 100);
    expect((result['projects'] as List).single['project_id'], 'project-001');
    api.close();
  });

  testWidgets('Project Experience exposes registry and shared platform boundaries', (tester) async {
    final client = MockClient((request) async {
      return http.Response(
        jsonEncode(<String, Object?>{
          'projects': <Object?>[
            <String, Object?>{
              'project_id': 'project-001',
              'display_name': 'Research OS Reference Project',
              'version': '1.0.0',
              'capabilities': <String>['agent'],
              'authorization_policy': 'EXISTING_AUTHORIZATION_BOUNDARY',
              'workflow_profile': 'SHARED_WORKFLOW',
              'evidence_namespace': 'PROJECT:project-001',
              'resource_policy': 'REJECT_ON_CONFLICT',
              'queue_namespace': 'SHARED_QUEUE',
              'evidence_ledger': 'SHARED_EVIDENCE_LEDGER',
              'release_authority': 'FINAL_GATE',
            },
          ],
          'configured_count': 1,
          'supported_project_contexts': 100,
          'release_authority': 'FINAL_GATE',
        }),
        200,
      );
    });
    final api = ResearchOSApiClient(baseUrl: 'http://127.0.0.1:8787', client: client);

    await tester.pumpWidget(
      MaterialApp(home: ProjectExperiencePage(apiClient: api)),
    );
    await tester.pumpAndSettle();

    expect(find.text('Projects'), findsOneWidget);
    expect(find.text('Project Registry'), findsOneWidget);
    expect(find.text('Research OS Reference Project'), findsOneWidget);
    expect(find.text('100'), findsOneWidget);
    expect(find.text('FINAL_GATE'), findsOneWidget);
    api.close();
  });
}
