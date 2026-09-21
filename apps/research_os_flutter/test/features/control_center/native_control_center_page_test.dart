import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/control_center/native_control_center_page.dart';

class _FakeClient extends http.BaseClient {
  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path;
    final payload = switch (path) {
      '/health' => <String, Object?>{
          'status': 'ok',
          'capabilities': <Object>['brain', 'evidence'],
        },
      '/v1/brain/capacity' => <String, Object?>{'skills': <Object>['analysis']},
      '/v1/providers' => <String, Object?>{'providers': <Object>['owner-mock']},
      '/v1/agents' => <String, Object?>{'agents': <Object>['friend']},
      _ => <String, Object?>{},
    };
    final bytes = utf8.encode(jsonEncode(payload));
    return http.StreamedResponse(
      Stream<List<int>>.value(bytes),
      200,
      request: request,
      headers: const <String, String>{'content-type': 'application/json'},
    );
  }
}

void main() {
  testWidgets('Control Center is reachable from the canonical app feature tree',
      (tester) async {
    final api = ResearchOSApiClient(
      baseUrl: 'http://127.0.0.1:8787',
      client: _FakeClient(),
    );

    await tester.pumpWidget(
      MaterialApp(home: NativeControlCenterPage(apiClient: api)),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 250));

    expect(find.text('Control Center'), findsOneWidget);
    expect(find.text('Overview'), findsOneWidget);
    expect(find.text('System Map'), findsOneWidget);
    expect(find.text('LIVE'), findsOneWidget);

    api.close();
  });
}
