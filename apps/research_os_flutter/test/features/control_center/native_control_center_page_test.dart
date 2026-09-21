import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/control_center/native_control_center_page.dart';

class _FakeClient extends http.BaseClient {
  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final payload = switch (request.url.path) {
      '/health' => <String, Object?>{
          'status': 'ok',
          'capabilities': <Object>['brain', 'evidence'],
        },
      '/v1/brain/capacity' => <String, Object?>{
          'skills': <Object>['analysis'],
        },
      '/v1/providers' => <String, Object?>{
          'providers': <Object>['owner-mock'],
        },
      '/v1/agents' => <String, Object?>{
          'agents': <Object>['friend'],
        },
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
  testWidgets('Control Center exposes the live operating environment',
      (tester) async {
    var navigated = -1;
    final api = ResearchOSApiClient(
      baseUrl: 'http://127.0.0.1:8787',
      client: _FakeClient(),
    );

    await tester.pumpWidget(
      MaterialApp(
        home: NativeControlCenterPage(
          apiClient: api,
          onNavigate: (index) => navigated = index,
        ),
      ),
    );
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Research OS • Control Center'), findsOneWidget);
    expect(find.text('Overview'), findsOneWidget);
    expect(find.text('System Map'), findsOneWidget);
    expect(find.text('Failures'), findsOneWidget);
    expect(find.text('Resources'), findsOneWidget);
    expect(find.text('Control'), findsOneWidget);
    expect(find.text('Design'), findsOneWidget);
    expect(find.text('LIVE'), findsNWidgets(2));
    expect(find.text('ROOT Closure Mesh'), findsOneWidget);
    expect(find.text('CLOSED 0/15'), findsOneWidget);
    expect(find.text('AUTHORITY'), findsOneWidget);
    expect(find.text('UNKNOWN 14'), findsOneWidget);

    final failures = find.text('Failures');
    await tester.ensureVisible(failures);
    await tester.tap(failures);
    await tester.pump(const Duration(milliseconds: 400));
    expect(find.text('Failure Center'), findsOneWidget);
    expect(find.textContaining('UNKNOWN is preserved'), findsOneWidget);

    final control = find.text('Control');
    await tester.ensureVisible(control);
    await tester.tap(control);
    await tester.pump(const Duration(milliseconds: 400));
    expect(find.text('Human authority required'), findsOneWidget);

    final design = find.text('Design');
    await tester.ensureVisible(design);
    await tester.tap(design);
    await tester.pump(const Duration(milliseconds: 300));
    expect(find.text('Native Design Studio'), findsOneWidget);
    expect(find.text('Canvas'), findsOneWidget);

    final friendAction = find.widgetWithText(OutlinedButton, 'Friend');
    expect(friendAction, findsOneWidget);
    await tester.tap(friendAction);
    expect(navigated, 1);

    api.close();
  });

  testWidgets('command search navigates without executing live work',
      (tester) async {
    final api = ResearchOSApiClient(
      baseUrl: 'http://127.0.0.1:8787',
      client: _FakeClient(),
    );

    await tester.pumpWidget(
      MaterialApp(home: NativeControlCenterPage(apiClient: api)),
    );
    await tester.pump(const Duration(milliseconds: 100));

    final commandField = find.byType(TextField);
    expect(commandField, findsOneWidget);
    await tester.enterText(commandField, 'show resources');
    await tester.pump();

    final suggestion = find.text('Show resources', skipOffstage: false);
    expect(suggestion, findsOneWidget);
    await tester.tap(suggestion);
    await tester.pump(const Duration(milliseconds: 350));

    // The command palette owns navigation; verify the selected destination
    // without depending on an offstage tab lookup.
    expect(find.text('Resource Center', skipOffstage: false), findsOneWidget);
    expect(
      find.textContaining('Runtime resource telemetry', skipOffstage: false),
      findsOneWidget,
    );

    api.close();
  });
}
