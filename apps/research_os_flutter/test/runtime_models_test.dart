import 'package:flutter_test/flutter_test.dart';

import 'package:research_os_flutter/src/features/chat/runtime_models.dart';

void main() {
  test('normalizes nested run envelope and flexible identifiers', () {
    final run = OrchestrationRun.fromResponse(<String, dynamic>{
      'run': <String, dynamic>{
        'id': 'legacy-id',
        'objective': 'legacy objective',
        'state': 'running',
        'steps': <Map<String, dynamic>>[
          <String, dynamic>{'step_id': 'verify'},
        ],
      },
    });

    expect(run.id, 'legacy-id');
    expect(run.objective, 'legacy objective');
    expect(run.state, RuntimeState.executing);
    expect(run.steps, hasLength(1));
  });

  test('accepts top-level orchestration response', () {
    final run = OrchestrationRun.fromResponse(<String, dynamic>{
      'run_id': 'top-level-id',
      'status': 'succeeded',
      'objective': 'ship it',
    });

    expect(run.id, 'top-level-id');
    expect(run.state, RuntimeState.completed);
  });

  test('normalizes timeline aliases and terminal states', () {
    final evidence = RuntimeEvidence.fromResponse(<String, dynamic>{
      'timeline': <Map<String, dynamic>>[
        <String, dynamic>{'event_type': 'run.created', 'run_status': 'running'},
        <String, dynamic>{'event_type': 'run.completed', 'run_status': 'done'},
      ],
    });

    expect(evidence.state, RuntimeState.completed);
    expect(evidence.events, hasLength(2));
    expect(evidence.state.isTerminal, isTrue);
  });
}
