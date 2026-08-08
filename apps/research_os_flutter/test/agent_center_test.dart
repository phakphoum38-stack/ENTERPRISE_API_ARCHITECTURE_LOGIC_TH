import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/agents/agent_center_page.dart';

class FakeAgentApiClient extends ResearchOSApiClient {
  FakeAgentApiClient() : super(baseUrl: 'http://127.0.0.1:8787');

  final List<Map<String, dynamic>> runs = <Map<String, dynamic>>[];
  bool executed = false;
  bool confirmed = false;

  @override
  Future<Map<String, dynamic>> getOrchestrations() async =>
      <String, dynamic>{'runs': runs, 'count': runs.length};

  @override
  Future<Map<String, dynamic>> createOrchestration({
    required String objective,
    required List<Map<String, Object?>> steps,
  }) async {
    final run = <String, dynamic>{
      'run_id': 'run-12345678',
      'objective': objective,
      'status': 'planned',
      'steps': steps
          .map((step) => <String, dynamic>{
                ...step,
                'status': 'planned',
                'depends_on': step['depends_on'] ?? <String>[],
              })
          .toList(),
    };
    runs
      ..clear()
      ..add(run);
    return <String, dynamic>{'run': run};
  }

  @override
  Future<Map<String, dynamic>> executeOrchestration(
    String runId, {
    bool confirmed = false,
  }) async {
    executed = true;
    runs.first['status'] = 'awaiting_confirmation';
    return <String, dynamic>{'run': runs.first};
  }

  @override
  Future<Map<String, dynamic>> confirmOrchestration(String runId) async {
    confirmed = true;
    runs.first['status'] = 'completed';
    final steps = runs.first['steps'] as List<dynamic>;
    for (final step in steps.whereType<Map<String, dynamic>>()) {
      step['status'] = 'completed';
    }
    return <String, dynamic>{'run': runs.first};
  }

  @override
  void close() {}
}

void main() {
  testWidgets('Agent Center creates executes and confirms orchestration',
      (tester) async {
    final api = FakeAgentApiClient();
    tester.view.physicalSize = const Size(1200, 1000);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(home: AgentCenterPage(apiClient: api)),
    );
    await tester.pumpAndSettle();

    expect(find.text('No orchestration runs yet'), findsOneWidget);
    await tester.tap(find.byKey(const Key('create-orchestration-button')));
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('orchestration-objective')),
      'Build a research summary',
    );
    await tester.enterText(
      find.byKey(const Key('orchestration-step-1')),
      'Research source material',
    );
    await tester.enterText(
      find.byKey(const Key('orchestration-step-2')),
      'Create final document',
    );
    await tester.tap(find.byKey(const Key('submit-orchestration')));
    await tester.pumpAndSettle();

    expect(find.text('Build a research summary'), findsOneWidget);
    expect(find.text('planned'), findsWidgets);
    expect(api.runs.single['steps'], hasLength(2));

    await tester.tap(find.byKey(const Key('execute-run-12345678')));
    await tester.pumpAndSettle();
    expect(api.executed, isTrue);
    expect(find.text('awaiting_confirmation'), findsOneWidget);

    await tester.tap(find.byKey(const Key('confirm-run-12345678')));
    await tester.pumpAndSettle();
    expect(api.confirmed, isTrue);
    expect(find.text('completed'), findsWidgets);
    expect(tester.takeException(), isNull);
  });
}
