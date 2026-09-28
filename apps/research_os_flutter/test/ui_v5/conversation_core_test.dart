import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/ui_v5/conversation_core.dart';
import 'package:research_os_flutter/src/ui_v5/v5_capability.dart';

class _FakeConversationBackend implements ResearchOSConversationBackend {
  _FakeConversationBackend({
    this.memoryResponse = const <String, dynamic>{'answer': 'memory answer'},
  });

  final Map<String, dynamic> memoryResponse;
  final Map<String, dynamic> directResponse =
      const <String, dynamic>{'text': 'direct answer'};
  final List<String> memoryPrompts = <String>[];
  final List<String> directPrompts = <String>[];

  @override
  Future<Map<String, dynamic>> answerWithMemory(String question) async {
    memoryPrompts.add(question);
    return memoryResponse;
  }

  @override
  Future<Map<String, dynamic>> generateText(String prompt) async {
    directPrompts.add(prompt);
    return directResponse;
  }
}

void main() {
  test('V5 user levels form a monotonic capability hierarchy', () {
    const ranks = <ResearchOSUserLevel>[
      ResearchOSUserLevel.user,
      ResearchOSUserLevel.powerUser,
      ResearchOSUserLevel.developer,
      ResearchOSUserLevel.owner,
      ResearchOSUserLevel.ownerSpecial,
    ];

    expect(ranks, hasLength(5));
    expect(
      ranks.indexOf(ResearchOSUserLevel.user),
      lessThan(ranks.indexOf(ResearchOSUserLevel.owner)),
    );
    expect(
      ranks.indexOf(ResearchOSUserLevel.owner),
      lessThan(ranks.indexOf(ResearchOSUserLevel.ownerSpecial)),
    );
  });

  test('conversation core uses memory backend and records evidence metadata', () async {
    final backend = _FakeConversationBackend(
      memoryResponse: <String, dynamic>{
        'answer': 'friend memory response',
        'memory_hits': <Object>['m1', 'm2'],
        'evidence_ids': <String>['ev-1', 'ev-2'],
      },
    );
    final controller = ResearchOSConversationController(backend: backend);

    final turn = await controller.sendText('  hello friend  ');

    expect(turn, isNotNull);
    expect(turn!.text, 'friend memory response');
    expect(turn.memoryHits, 2);
    expect(turn.evidenceIds, <String>['ev-1', 'ev-2']);
    expect(backend.memoryPrompts, <String>['hello friend']);
    expect(controller.turns, hasLength(2));
    expect(controller.state, ResearchOSConversationState.idle);
  });

  test('conversation core can switch to direct generation', () async {
    final backend = _FakeConversationBackend();
    final controller = ResearchOSConversationController(backend: backend);
    controller.useMemory = false;

    final turn = await controller.sendText('build a plan');

    expect(turn!.text, 'direct answer');
    expect(backend.directPrompts, <String>['build a plan']);
    expect(backend.memoryPrompts, isEmpty);
  });

  test('conversation core rejects empty prompts without creating a turn', () async {
    final controller = ResearchOSConversationController(
      backend: _FakeConversationBackend(),
    );

    final turn = await controller.sendText('   ');

    expect(turn, isNull);
    expect(controller.turns, isEmpty);
    expect(controller.state, ResearchOSConversationState.idle);
  });

  test('conversation core fails closed on backend errors', () async {
    final backend = _ThrowingConversationBackend();
    final controller = ResearchOSConversationController(backend: backend);

    final turn = await controller.sendText('trigger failure');

    expect(turn, isNull);
    expect(controller.turns, hasLength(1));
    expect(controller.state, ResearchOSConversationState.failed);
    expect(controller.error, contains('backend unavailable'));
  });
}

class _ThrowingConversationBackend implements ResearchOSConversationBackend {
  @override
  Future<Map<String, dynamic>> answerWithMemory(String question) async {
    throw StateError('backend unavailable');
  }

  @override
  Future<Map<String, dynamic>> generateText(String prompt) async {
    throw StateError('backend unavailable');
  }
}
