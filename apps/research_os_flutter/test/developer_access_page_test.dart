import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:research_os_flutter/src/api/developer_access_api_client.dart';
import 'package:research_os_flutter/src/features/developer_access/developer_access_page.dart';

void main() {
  testWidgets('owner inbox shows pending requests and active grants', (tester) async {
    final client = MockClient((request) async {
      if (request.url.path == '/v2/developer/session') {
        return http.Response(
          jsonEncode(<String, Object?>{
            'api_version': 'v2',
            'authenticated': true,
            'principal': 'user:owner',
          }),
          200,
        );
      }
      if (request.url.path == '/v2/developer/access/pending') {
        return http.Response(
          jsonEncode(<String, Object?>{
            'requests': <Object?>[
              <String, Object?>{
                'id': 'req-1',
                'principal': 'user:developer',
                'resource': 'Owner file.md',
                'requested_at': '2026-09-23T00:00:00Z',
              },
            ],
          }),
          200,
        );
      }
      if (request.url.path == '/v2/developer/access/active') {
        return http.Response(
          jsonEncode(<String, Object?>{
            'grants': <Object?>[
              <String, Object?>{
                'id': 'grant-1',
                'principal': 'user:developer',
                'resource': 'Owner file.md',
                'expires_at': '2026-09-30T00:00:00Z',
              },
            ],
          }),
          200,
        );
      }
      return http.Response('{}', 404);
    });

    await tester.pumpWidget(
      MaterialApp(
        home: DeveloperAccessPage(
          apiClient: DeveloperAccessApiClient(
            baseUrl: 'https://developer.example.test',
            client: client,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('developer-access-page')), findsOneWidget);
    expect(find.text('user:owner'), findsOneWidget);
    final developerAccessScroll = find.descendant(
      of: find.byKey(const Key('developer-access-scroll')),
      matching: find.byType(Scrollable),
    );
    final pendingHeading = find.textContaining('คำขอที่รออนุมัติ (1)');
    await tester.scrollUntilVisible(
      pendingHeading,
      500,
      scrollable: developerAccessScroll,
    );
    expect(pendingHeading, findsOneWidget);
    expect(find.text('Owner file.md'), findsOneWidget);

    final activeHeading = find.textContaining('สิทธิ์ที่กำลังใช้งาน (1)');
    await tester.scrollUntilVisible(
      activeHeading,
      500,
      scrollable: developerAccessScroll,
    );
    expect(activeHeading, findsOneWidget);
  });
}
