import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/memory/memory_inspector_page.dart';

void main() {
  testWidgets('Memory Inspector renders local runtime memories', (tester) async {
    final client = ResearchOSApiClient(
      baseUrl: 'http://research-os.test',
      client: MockClient((request) async {
        expect(request.url.path, '/v1/runtime-memory');
        return http.Response(
          jsonEncode(<String, Object?>{
            'count': 1,
            'records': <Map<String, Object?>>[
              <String, Object?>{
                'id': 'mem_test',
                'type': 'conversation',
                'content': 'Local-first memory content',
                'title': 'Assistant response',
                'source': 'chat',
                'provider': 'mock',
                'tags': <String>['chat', 'assistant'],
              },
            ],
          }),
          200,
          headers: <String, String>{'content-type': 'application/json'},
        );
      }),
    );

    await tester.pumpWidget(
      MaterialApp(home: MemoryInspectorPage(apiClient: client)),
    );
    await tester.pumpAndSettle();

    expect(find.text('Memory Inspector'), findsWidgets);
    expect(find.text('Local-first memory content'), findsOneWidget);
    expect(find.text('conversation'), findsOneWidget);
    expect(find.text('source: chat'), findsOneWidget);

    client.close();
  });
}
