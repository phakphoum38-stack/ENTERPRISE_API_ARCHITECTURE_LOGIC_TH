import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/chat/agent_runtime_bridge.dart';

class FakeRuntimeApiClient extends ResearchOSApiClient {
  FakeRuntimeApiClient() : super(baseUrl: 'http://127.0.0.1:8787');

  bool executed = false;
  bool confirmed = false;

  @override
  Future<Map<String, dynamic>> createOrchestration({
    required String objective,
    required List<Map<String, Object?>> steps,
  }) async => <String, dynamic>{
        'run': <String, dynamic>{
          'run_id': 'run-evidence-123',
          'objective': objective,
          'status': 'planned',
          'steps': steps,
        },
      };

  @override
  Future<Map<String, dynamic>> executeOrchestration(
    String runId, {
    bool confirmed = false,
  }) async {
    executed = true;
    this.confirmed = confirmed;
    return <String, dynamic>{
      'run': <String, dynamic>{'run_id': runId, 'status': 'completed'},
    };
  }

  @override
  Future<Map<String, dynamic>> getOrchestrationTimeline(String runId) async =>
      <String, dynamic>{
        'run_id': runId,
        'events': <Map<String, dynamic>>[
          <String, dynamic>{
            'event_type': 'run.created',
            'run_status': executed ? 'completed' : 'planned',
            'step_id': null,
          },
          if (executed)
            <String, dynamic>{
              'event_type': 'run.completed',
              'run_status': 'completed',
              'step_id': 'verify',
            },
        ],
      };

  @override
  void close() {}
}

void main() {
  testWidgets('Agent Mesh runtime bridge renders plan and execute controls',
      (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AgentRuntimeBridge(apiClient: FakeRuntimeApiClient()),
        ),
      ),
    );

    expect(find.text('Agent Mesh Runtime'), findsOneWidget);
    expect(find.text('Plan with Agent Mesh'), findsOneWidget);
    expect(find.text('Explicit Execute'), findsOneWidget);
    expect(find.text('Runtime Evidence'), findsOneWidget);
    expect(
      find.text('Plan first. Execute only through an explicit user action.'),
      findsOneWidget,
    );
  });

  testWidgets('runtime bridge completes plan execute evidence loop',
      (tester) async {
    final api = FakeRuntimeApiClient();
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: AgentRuntimeBridge(apiClient: api)),
      ),
    );

    await tester.enterText(find.byType(TextField), 'ตรวจสอบ workflow');
    await tester.tap(find.text('Plan with Agent Mesh'));
    await tester.pumpAndSettle();

    expect(find.text('Run planned • waiting for explicit execution.'), findsOneWidget);
    // The production UI intentionally truncates long run IDs for compactness.
    expect(find.textContaining('run-evidence'), findsOneWidget);

    await tester.tap(find.text('Explicit Execute'));
    await tester.pumpAndSettle();

    expect(api.executed, isTrue);
    expect(api.confirmed, isTrue);
    expect(find.textContaining('Run completed • run-evidence-'), findsOneWidget);
    expect(find.text('run.completed'), findsOneWidget);
    expect(find.text('completed'), findsWidgets);
    expect(tester.takeException(), isNull);
  });
}
