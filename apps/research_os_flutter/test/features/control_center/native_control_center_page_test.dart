import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/control_center/native_control_audit_view.dart';
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
      '/v1/brain/capacity' => <String, Object?>{'capacity': 36},
      '/v1/brain/skills' => <String, Object?>{
          'skills': <Object>['analysis'],
        },
      '/v1/providers' => <String, Object?>{'providers': <Object>['owner-mock']},
      '/v1/agents' => <String, Object?>{'agents': <Object>['friend']},
      '/v1/agents/readiness' => <String, Object?>{'status': 'ready'},
      '/v1/agents/orchestrations' => <String, Object?>{
          'orchestrations': <Object>[
            <String, Object?>{'run_id': 'run-1', 'status': 'completed'},
            <String, Object?>{'run_id': 'run-2', 'status': 'running'},
            <String, Object?>{'run_id': 'run-3', 'status': 'failed'},
          ],
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
  testWidgets('Control Center is reachable from the canonical app feature tree',
      (tester) async {
    final api = ResearchOSApiClient(
      baseUrl: 'http://127.0.0.1:8787',
      client: _FakeClient(),
    );

    await tester.pumpWidget(
      MaterialApp(home: NativeControlCenterPage(apiClient: api)),
    );
    await tester.pumpAndSettle();

    expect(find.text('Native Core Workspace'), findsOneWidget);
    expect(find.text('Overview'), findsOneWidget);
    expect(find.text('System Map'), findsOneWidget);
    expect(find.text('LIVE'), findsOneWidget);
    expect(find.text('Agent readiness'), findsOneWidget);
    expect(find.text('Workflow runs'), findsOneWidget);
    expect(find.text('Running'), findsOneWidget);
    expect(find.text('Failed'), findsOneWidget);

    final overview = find.byKey(
      const ValueKey('control-center-overview-scroll'),
    );
    expect(overview, findsOneWidget);

    // ListView is the keyed owner of the overview scroll region. Its actual
    // Scrollable is a child created by ListView, not an ancestor of ListView.
    // Resolve that child so scrollUntilVisible can operate on the correct
    // scroll position without depending on other Scrollables in the page.
    final overviewScrollable = find
        .descendant(
          of: overview,
          matching: find.byType(Scrollable),
        )
        .first;
    expect(overviewScrollable, findsOneWidget);

    await tester.scrollUntilVisible(
      find.byKey(const ValueKey('platform-controls-card')),
      500,
      scrollable: overviewScrollable,
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('platform-controls-card')), findsOneWidget);
    expect(find.text('Platform Controls'), findsOneWidget);
    expect(find.text('Defect Control'), findsOneWidget);
    expect(find.text('Schedule Control'), findsOneWidget);
    expect(find.text('Risk Control'), findsOneWidget);
    expect(find.text('Change Impact Control'), findsOneWidget);
    expect(find.text('CANONICAL'), findsNWidgets(4));

    await tester.scrollUntilVisible(
      find.text('Workflow control surface'),
      500,
      scrollable: overviewScrollable,
    );
    await tester.pumpAndSettle();

    expect(find.text('Workflow control surface'), findsOneWidget);

    api.close();
  });

  testWidgets('Main Final Audit is available inside the existing Control Center',
      (tester) async {
    final api = ResearchOSApiClient(
      baseUrl: 'http://127.0.0.1:8787',
      client: _FakeClient(),
    );

    await tester.pumpWidget(
      MaterialApp(home: NativeControlCenterPage(apiClient: api)),
    );
    await tester.pumpAndSettle();

    expect(find.byIcon(Icons.rule_folder_outlined), findsOneWidget);

    api.close();
  });

  testWidgets('Main Final Audit renders snapshots and preserves deferred state',
      (tester) async {
    final snapshot = NativeControlAuditSnapshot(
      auditId: 'audit-test',
      observedAt: DateTime.utc(2026, 1, 1),
      status: 'DEFERRED',
      checks: <Map<String, String>>[
        <String, String>{
          'check': 'Offline package audit',
          'state': 'DEFERRED',
          'detail': 'Not exposed by the current read-only API surface',
        },
        <String, String>{
          'check': 'Installed baseline',
          'state': 'DEFERRED',
          'detail': 'Not exposed by the current read-only API surface',
        },
      ],
      source: 'test',
    );
    await tester.pumpWidget(
      MaterialApp(
        home: NativeControlAuditView(
          health: const <String, dynamic>{'status': 'ok'},
          brain: const <String, dynamic>{'capacity': 1},
          skills: const <String, dynamic>{'skills': <String>['test']},
          providers: const <String, dynamic>{'providers': <String>['test']},
          agents: const <String, dynamic>{'agents': <String>['test']},
          agentReadiness: const <String, dynamic>{'status': 'ready'},
          orchestrations: const <String, dynamic>{
            'orchestrations': <Map<String, dynamic>>[
              <String, dynamic>{'run_id': 'run-1', 'status': 'completed'},
            ],
          },
          snapshots: <NativeControlAuditSnapshot>[snapshot],
          onRun: () {},
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Main Final Audit'), findsOneWidget);
    expect(find.text('Latest: DEFERRED'), findsOneWidget);
    expect(find.text('Offline package audit'), findsOneWidget);
    expect(find.text('Installed baseline'), findsOneWidget);
    expect(find.text('Export Audit JSON'), findsOneWidget);
  });

}
