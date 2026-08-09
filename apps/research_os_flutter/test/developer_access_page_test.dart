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
      if (request.url.path == '/v2/developer/access-requests') {
        expect(request.url.queryParameters['view'], 'owner');
        expect(request.url.queryParameters['status'], 'pending');
        return http.Response(
          jsonEncode(<String, Object?>{
            'api_version': 'v2',
            'items': <Object?>[
              <String, Object?>{
                'request_id': 'request-1',
                'developer_id': 'dev:alice',
                'owner_id': 'user:owner',
                'workspace_id': 'workspace-1',
                'resource_id': 'file-1',
                'resource_name': 'Owner file.md',
                'requested_scopes': <String>['read', 'write'],
                'purpose': 'Fix approved issue',
                'status': 'pending',
              },
            ],
          }),
          200,
        );
      }
      if (request.url.path == '/v2/developer/grants') {
        expect(request.url.queryParameters['view'], 'owner');
        return http.Response(
          jsonEncode(<String, Object?>{
            'api_version': 'v2',
            'items': <Object?>[
              <String, Object?>{
                'grant_id': 'grant-1',
                'developer_id': 'dev:bob',
                'owner_id': 'user:owner',
                'workspace_id': 'workspace-2',
                'resource_id': 'file-2',
                'resource_name': 'Approved file.md',
                'scopes': <String>['read'],
                'active': true,
                'owner_access_unchanged': true,
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
          client: DeveloperAccessApiClient(
            baseUrl: 'https://developer.example.test',
            client: client,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('developer-access-page')), findsOneWidget);
    expect(find.text('user:owner'), findsOneWidget);
    expect(find.textContaining('คำขอที่รออนุมัติ (1)'), findsOneWidget);
    expect(find.text('Owner file.md'), findsOneWidget);
    expect(find.textContaining('สิทธิ์ที่กำลังใช้งาน (1)'), findsOneWidget);
    expect(find.text('Approved file.md'), findsOneWidget);
    expect(find.text('Revoke'), findsOneWidget);
  });

  testWidgets('owner inbox degrades safely when developer API is offline', (tester) async {
    final client = MockClient((request) async {
      throw const http.ClientException('offline');
    });

    await tester.pumpWidget(
      MaterialApp(
        home: DeveloperAccessPage(
          client: DeveloperAccessApiClient(
            baseUrl: 'http://127.0.0.1:8790',
            client: client,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('ต้องลงชื่อเข้าใช้ในฐานะเจ้าของไฟล์'), findsOneWidget);
    expect(find.textContaining('เชื่อม Developer API ไม่สำเร็จ'), findsOneWidget);
  });
}
