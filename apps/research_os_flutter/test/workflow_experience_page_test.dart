import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/workflows/workflow_experience_page.dart';

class FakeWorkflowApiClient extends ResearchOSApiClient {
  FakeWorkflowApiClient() : super(baseUrl: 'http://127.0.0.1:8787');

  @override
  Future<Map<String, dynamic>> getOrchestrations({
    String? status,
    String? query,
    String? agent,
    int? limit,
  }) async => {
        'runs': [
          {
            'run_id': 'run-1',
            'objective': 'Research objective',
            'status': 'completed',
            'steps': [
              {'step_id': 'step-1', 'objective': 'Collect evidence', 'status': 'completed'},
              {'step_id': 'step-2', 'objective': 'Write result', 'status': 'completed'},
            ],
          },
        ],
        'count': 1,
      };

  @override
  Future<Map<String, dynamic>> getOrchestrationTimeline(String runId) async => {
        'run_id': runId,
        'events': [
          {'event_type': 'workflow.completed', 'run_status': 'completed', 'step_id': 'step-2'},
        ],
      };
}

void main() {
  testWidgets('Workflow Experience observes existing orchestration and timeline', (tester) async {
    await tester.pumpWidget(
      MaterialApp(home: WorkflowExperiencePage(apiClient: FakeWorkflowApiClient())),
    );
    await tester.pumpAndSettle();

    expect(find.text('Workflow Experience'), findsOneWidget);
    expect(find.byKey(const Key('workflow-run-count')), findsOneWidget);
    expect(find.text('Research objective'), findsOneWidget);

    await tester.tap(find.byKey(const Key('workflow-run-run-1')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('workflow-selected-run')), findsOneWidget);
    expect(find.text('workflow.completed'), findsOneWidget);
    expect(find.byKey(const Key('workflow-lifecycle-INTENT')), findsOneWidget);
    expect(find.byKey(const Key('workflow-lifecycle-RECOVER')), findsOneWidget);
  });
}
