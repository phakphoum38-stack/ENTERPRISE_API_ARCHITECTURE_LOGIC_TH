import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/owner/owner_experience_page.dart';

void main() {
  testWidgets('owner experience observes the shared platform and owner authority', (tester) async {
    final client = ResearchOSApiClient(
      baseUrl: 'http://test',
      client: MockClient((request) async {
        final path = request.url.path;
        final payload = switch (path) {
          '/v1/auth/status' => <String, dynamic>{'role': 'owner', 'user_id': 'owner'},
          '/health' => <String, dynamic>{'status': 'ok'},
          '/v1/projects' => <String, dynamic>{'count': 1, 'projects': <dynamic>[]},
          '/v1/agents/orchestrations' => <String, dynamic>{'count': 2, 'runs': <dynamic>[]},
          '/v1/agents' => <String, dynamic>{'count': 3, 'agents': <dynamic>[]},
          '/v1/providers' => <String, dynamic>{'count': 4, 'providers': <dynamic>[]},
          _ => <String, dynamic>{},
        };
        return http.Response(jsonEncode(payload), 200);
      }),
    );

    addTearDown(client.close);

    await tester.pumpWidget(
      MaterialApp(
        home: OwnerExperiencePage(apiClient: client),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Owner Experience'), findsOneWidget);
    expect(find.text('OWNER session verified'), findsOneWidget);
    expect(find.text('Projects configured'), findsOneWidget);
    expect(find.text('1'), findsWidgets);
    expect(find.byKey(const Key('owner-authority-boundary')), findsOneWidget);
    expect(find.textContaining('unrestricted by resource or scope'), findsOneWidget);
  });
}
