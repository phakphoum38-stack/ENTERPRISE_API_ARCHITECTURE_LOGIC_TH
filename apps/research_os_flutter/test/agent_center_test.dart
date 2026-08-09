import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/agents/agent_center_page.dart';

class FakeAgentApiClient extends ResearchOSApiClient {
  FakeAgentApiClient() : super(baseUrl: 'http://127.0.0.1:8787');

  final List<Map<String, dynamic>> runs = <Map<String, dynamic>>[];
  bool executed = false;
  bool confirmed = false;
  bool cancelled = false;
  bool retried = false;
  bool knowledgeSearched = false;
  bool brainPlanPreviewed = false;

  @override
  Future<Map<String, dynamic>> getOrchestrations({
    String? status,
    String? query,
    String? agent,
    int? limit,
  }) async => <String, dynamic>{'runs': runs, 'count': runs.length};

  @override
  Future<Map<String, dynamic>> getV2Workspaces() async => <String, dynamic>{
        'api_version': 'v2',
        'workspaces': <Map<String, dynamic>>[
          <String, dynamic>{'workspace_id': 'research', 'name': 'Research workspace'},
        ],
        'count': 1,
      };

  @override
  Future<Map<String, dynamic>> searchWorkspaceKnowledge(
    String workspaceId, {
    String query = '',
    int pageSize = 25,
    String? cursor,
  }) async {
    knowledgeSearched = true;
    return <String, dynamic>{
      'api_version': 'v2',
      'workspace_id': workspaceId,
      'items': <Map<String, dynamic>>[
        <String, dynamic>{
          'record_id': 'research_artifact:art-1',
          'title': 'Evidence Note',
          'kind': 'research_artifact',
          'score': 3,
          'provenance': <String, dynamic>{
            'source_type': 'research_artifact',
            'source_id': 'art-1',
          },
        },
      ],
      'page': <String, dynamic>{
        'page_size': pageSize,
        'returned': 1,
        'next_cursor': null,
      },
    };
  }

  @override
  Future<Map<String, dynamic>> getIntelligenceHealth() async =>
      <String, dynamic>{
        'api_version': 'v2',
        'ready': true,
        'counts': <String, dynamic>{
          'operational_agents': 6,
          'operational_agents_ready': 6,
          'brain_agents': 12,
          'brain_agents_ready': 12,
          'skills': 34,
          'skills_ready': 34,
          'tools': 8,
          'tools_ready': 5,
          'mutating_tools_ready': 0,
        },
      };

  @override
  Future<Map<String, dynamic>> getIntelligenceCapabilities() async =>
      <String, dynamic>{
        'api_version': 'v2',
        'capabilities': <Map<String, dynamic>>[
          <String, dynamic>{
            'capability': 'debug',
            'known': true,
            'routable': true,
            'skill_supported': true,
            'executable': false,
          },
          <String, dynamic>{
            'capability': 'code_search',
            'known': true,
            'routable': true,
            'skill_supported': true,
            'executable': true,
          },
        ],
        'count': 2,
      };

  @override
  Future<Map<String, dynamic>> getIntelligenceSkills({
    String? capability,
    String? permission,
    bool readyOnly = true,
  }) async => <String, dynamic>{
        'api_version': 'v2',
        'skills': <Map<String, dynamic>>[
          <String, dynamic>{
            'skill_id': 'software.debug-diagnosis',
            'ready': true,
          },
          <String, dynamic>{
            'skill_id': 'github.ci-diagnosis',
            'ready': true,
          },
        ],
        'count': 2,
      };

  @override
  Future<Map<String, dynamic>> getIntelligenceTools({
    String? capability,
    String? permission,
    bool readyOnly = true,
  }) async => <String, dynamic>{
        'api_version': 'v2',
        'tools': <Map<String, dynamic>>[
          <String, dynamic>{
            'tool_id': 'workspace.code.search',
            'ready': true,
          },
        ],
        'count': 1,
      };

  @override
  Future<Map<String, dynamic>> planIntelligence(
    String objective, {
    String? sessionId,
    Map<String, Object?> context = const <String, Object?>{},
  }) async {
    brainPlanPreviewed = true;
    return <String, dynamic>{
      'api_version': 'v2',
      'read_only': true,
      'execution_performed': false,
      'result': <String, dynamic>{
        'plan': <String, dynamic>{
          'goal': objective,
          'required_capabilities': <String>['debug', 'code'],
          'blocked_reasons': <String>[],
        },
      },
    };
  }

  @override
  Future<Map<String, dynamic>> getV2SquaredBrainAgents({bool readyOnly = true}) async =>
      <String, dynamic>{
        'api_version': 'v2',
        'brain_team': <Map<String, dynamic>>[
          <String, dynamic>{
            'agent_id': 'v2_brain_coordinator',
            'name': 'AI Brain Coordinator',
            'permission_profile': 'standard',
            'health': <String, dynamic>{'status': 'ready', 'ready': true},
          },
          <String, dynamic>{
            'agent_id': 'v2_brain_reviewer',
            'name': 'Independent AI Brain Reviewer',
            'permission_profile': 'read_only',
            'health': <String, dynamic>{'status': 'ready', 'ready': true},
          },
        ],
        'count': 2,
      };

  @override
  Future<Map<String, dynamic>> getOrchestrationTimeline(String runId) async =>
      <String, dynamic>{
        'run_id': runId,
        'events': <Map<String, dynamic>>[
          <String, dynamic>{
            'event_type': 'run.created',
            'run_status': 'planned',
            'step_id': null,
          },
        ],
      };

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
  Future<Map<String, dynamic>> cancelOrchestration(String runId) async {
    cancelled = true;
    runs.first['status'] = 'cancelled';
    return <String, dynamic>{'run': runs.first};
  }

  @override
  Future<Map<String, dynamic>> retryOrchestration(
    String runId, {
    String? stepId,
  }) async {
    retried = true;
    runs.first['status'] = 'planned';
    return <String, dynamic>{'run': runs.first};
  }

  @override
  void close() {}
}

void configureView(WidgetTester tester, {double height = 2600}) {
  tester.view.physicalSize = Size(1200, height);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
}

Widget testApp(ResearchOSApiClient api) => MaterialApp(
      home: Scaffold(
        body: AgentCenterPage(apiClient: api),
      ),
    );

void main() {
  testWidgets('Agent Center V2 squared creates executes and confirms orchestration',
      (tester) async {
    final api = FakeAgentApiClient();
    configureView(tester);

    await tester.pumpWidget(testApp(api));
    await tester.pumpAndSettle();

    expect(find.text('Agent Center V2²'), findsOneWidget);
    expect(find.text('No orchestration runs yet'), findsOneWidget);
    await tester.tap(find.byKey(const Key('create-orchestration-button')));
    await tester.pumpAndSettle();

    expect(find.text('Create orchestration • V2² helpers'), findsOneWidget);
    expect(find.text('v2_brain_coordinator'), findsOneWidget);
    expect(find.text('v2_brain_reviewer'), findsOneWidget);

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
    expect(find.byKey(const Key('orchestration-dependency-graph')), findsOneWidget);
    expect(find.text('planned'), findsWidgets);
    expect(api.runs.single['steps'], hasLength(2));
    final createdSteps = api.runs.single['steps'] as List<dynamic>;
    expect(createdSteps.first['requested_agent'], 'v2_brain_coordinator');
    expect(createdSteps.last['requested_agent'], 'v2_brain_reviewer');

    await tester.ensureVisible(find.byKey(const Key('execute-run-12345678')));
    await tester.tap(find.byKey(const Key('execute-run-12345678')));
    await tester.pumpAndSettle();
    expect(api.executed, isTrue);
    expect(find.text('awaiting_confirmation'), findsOneWidget);
    expect(find.byKey(const Key('approval-run-12345678')), findsOneWidget);

    await tester.ensureVisible(find.byKey(const Key('confirm-run-12345678')));
    await tester.tap(find.byKey(const Key('confirm-run-12345678')));
    await tester.pumpAndSettle();
    expect(api.confirmed, isTrue);
    expect(find.text('completed'), findsWidgets);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Agent Center V2 exposes workspace knowledge with provenance',
      (tester) async {
    final api = FakeAgentApiClient();
    configureView(tester);
    final semantics = tester.ensureSemantics();

    await tester.pumpWidget(testApp(api));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('workspace-selector')), findsOneWidget);
    expect(find.text('Research workspace'), findsOneWidget);
    expect(find.bySemanticsLabel('Search workspace knowledge'), findsNWidgets(2));

    await tester.enterText(
      find.byKey(const Key('knowledge-search-query')),
      'evidence',
    );
    await tester.tap(find.byKey(const Key('knowledge-search-button')));
    await tester.pumpAndSettle();

    expect(api.knowledgeSearched, isTrue);
    expect(find.text('Evidence Note'), findsOneWidget);
    expect(
      find.text('research_artifact • source: research_artifact / art-1'),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
    semantics.dispose();
  });

  testWidgets('Agent Center exposes read-only AI Brain Inspector and plan preview',
      (tester) async {
    final api = FakeAgentApiClient();
    configureView(tester, height: 3000);

    await tester.pumpWidget(testApp(api));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('brain-inspector')), findsOneWidget);
    expect(find.byKey(const Key('brain-ready-state')), findsOneWidget);
    expect(find.text('Brain runtime ready'), findsOneWidget);
    expect(find.byKey(const Key('brain-capability-debug')), findsOneWidget);
    expect(find.text('software.debug-diagnosis', skipOffstage: false), findsOneWidget);
    expect(find.text('workspace.code.search', skipOffstage: false), findsOneWidget);
    expect(find.byKey(const Key('brain-inspector-safety'), skipOffstage: false), findsOneWidget);

    await tester.ensureVisible(find.byKey(const Key('brain-plan-objective')));
    await tester.enterText(
      find.byKey(const Key('brain-plan-objective')),
      'debug code failure',
    );
    await tester.tap(find.byKey(const Key('brain-plan-preview')));
    await tester.pumpAndSettle();

    expect(api.brainPlanPreviewed, isTrue);
    expect(find.byKey(const Key('brain-plan-result')), findsOneWidget);
    expect(find.text('Required capabilities: debug, code'), findsOneWidget);
    expect(find.text('No execution performed by this preview.'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Agent Center V2 squared exposes Brain Team health and cancellation controls',
      (tester) async {
    final api = FakeAgentApiClient();
    api.runs.add(<String, dynamic>{
      'run_id': 'run-v2controls',
      'objective': 'Validate V2 controls',
      'status': 'planned',
      'steps': <Map<String, dynamic>>[
        <String, dynamic>{
          'step_id': 'step-1',
          'requested_agent': 'v2_brain_coordinator',
          'status': 'planned',
          'depends_on': <String>[],
        },
      ],
    });
    configureView(tester, height: 4200);

    await tester.pumpWidget(testApp(api));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('orchestration-dependency-graph')), findsOneWidget);
    expect(find.byKey(const Key('cancel-run-v2controls')), findsOneWidget);

    await tester.ensureVisible(find.byKey(const Key('load-agent-health')));
    await tester.tap(find.byKey(const Key('load-agent-health')));
    await tester.pumpAndSettle();
    expect(find.text('AI Brain Coordinator'), findsOneWidget);
    expect(find.text('Independent AI Brain Reviewer'), findsOneWidget);
    expect(find.text('ready'), findsWidgets);

    await tester.ensureVisible(find.byKey(const Key('timeline-run-v2controls')));
    await tester.tap(find.byKey(const Key('timeline-run-v2controls')));
    await tester.pumpAndSettle();
    expect(find.text('run.created'), findsOneWidget);
    await tester.tap(find.text('Close'));
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.byKey(const Key('cancel-run-v2controls')));
    await tester.tap(find.byKey(const Key('cancel-run-v2controls')));
    await tester.pumpAndSettle();
    expect(api.cancelled, isTrue);
    expect(find.text('cancelled'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
