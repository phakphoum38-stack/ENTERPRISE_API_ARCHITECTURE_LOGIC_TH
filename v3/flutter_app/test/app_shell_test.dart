import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_v3_flutter/src/api/v3_api.dart';
import 'package:research_os_v3_flutter/src/research_os_v3_app.dart';

class FakeApi implements V3Api {
  @override
  Future<Map<String, dynamic>> health() async => {
        'status': 'ok',
        'version': 'v3-full-10x10',
        'maximum_scale': '10^10',
        'maximum_logical_capacity': 10000000000,
      };

  @override
  Future<Map<String, dynamic>> master({
    int tasks = 1,
    int risk = 1,
    int parallelism = 1,
  }) async => {
        'contract': 'unified-master-orchestrator-v3-full',
        'scale': '6^3',
        'maximum_leaf_capacity': 216,
        'system_maximum_scale': '10^10',
        'system_maximum_logical_capacity': 10000000000,
      };

  @override
  Future<Map<String, dynamic>> providers() async => {
        'providers': [
          {
            'name': 'mock',
            'ready': true,
            'connected': true,
            'secret_exposed': false,
          },
        ],
      };

  @override
  Future<Map<String, dynamic>> user() async => {
        'user_id': 'alice',
        'profile_id': 'default',
        'scope': 'users/alice/profiles/default',
        'isolated': true,
      };

  @override
  Future<Map<String, dynamic>> skills() async => {
        'skills': [
          {
            'name': 'chat-runtime',
            'origin': 'v3',
            'capability': 'chat',
            'description': 'Chat execution',
            'native_v3': true,
          },
        ],
      };

  @override
  Future<Map<String, dynamic>> tools() async => {
        'tools': [
          {
            'name': 'echo',
            'capability': 'utility',
            'description': 'Echo',
            'risk': 'read-only',
            'approval_required': false,
          },
        ],
      };

  @override
  Future<Map<String, dynamic>> agents() async => {
        'agents': [
          {
            'name': 'architect',
            'role': 'architecture',
            'description': 'Architect agent',
            'skills': ['adaptive-hierarchy'],
            'tools': ['capacity-inspect'],
          },
        ],
      };

  @override
  Future<Map<String, dynamic>> memory({String query = '', int limit = 20}) async => {
        'memory': <Map<String, dynamic>>[],
      };

  @override
  Future<Map<String, dynamic>> factoryPlan({
    int tasks = 1,
    int risk = 1,
    int parallelism = 1,
  }) async => {
        'scale': '6^3',
        'maximum_leaf_capacity': 216,
        'stage_order': ['master', 'factory', 'team', 'tests', 'release'],
        'decision': {'system_maximum_scale': '10^10'},
      };

  @override
  Future<Map<String, dynamic>> chat(
    String prompt, {
    String? agent,
    String? preferredProvider,
    int memoryLimit = 8,
  }) async => {
        'text': 'answer:$prompt',
        'provider': 'mock',
        'model': 'mock',
        'memory_hits': <Map<String, dynamic>>[],
      };

  @override
  Future<Map<String, dynamic>> addMemory(
    String text, {
    List<String> tags = const <String>[],
  }) async => {
        'memory': {'text': text, 'tags': tags},
      };

  @override
  Future<Map<String, dynamic>> runAgent(String name, String prompt) async => {
        'agent': name,
        'text': 'agent:$prompt',
        'provider': 'mock',
      };

  @override
  Future<Map<String, dynamic>> executeTool(
    String name,
    Map<String, dynamic> arguments, {
    bool approved = false,
  }) async => {
        'tool': name,
        'result': arguments,
      };
}

void main() {
  testWidgets('full-system shell renders 10x10 state and live chat',
      (tester) async {
    await tester.binding.setSurfaceSize(const Size(1440, 900));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    await tester.pumpWidget(ResearchOSV3App(api: FakeApi()));
    await tester.pumpAndSettle();

    expect(find.text('Full System Control Center'), findsOneWidget);
    expect(find.text('10^10'), findsWidgets);
    expect(find.text('10,000,000,000'), findsOneWidget);

    await tester.tap(find.text('Chat'));
    await tester.pumpAndSettle();
    expect(find.text('AI Chat'), findsOneWidget);

    await tester.enterText(find.byType(TextField).last, 'hello');
    await tester.tap(find.byIcon(Icons.arrow_upward));
    await tester.pumpAndSettle();
    expect(find.text('answer:hello'), findsOneWidget);

    await tester.tap(find.text('Providers'));
    await tester.pumpAndSettle();
    expect(find.text('Secrets stay outside the desktop app'), findsOneWidget);
    expect(find.textContaining('secret_exposed=false'), findsOneWidget);
  });
}
