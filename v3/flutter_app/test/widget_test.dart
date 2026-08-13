import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_v3_flutter/src/api/v3_api.dart';
import 'package:research_os_v3_flutter/src/research_os_v3_app.dart';

class _WidgetTestApi implements V3Api {
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
      };

  @override
  Future<Map<String, dynamic>> providers() async => {
        'providers': [
          {'name': 'mock', 'ready': true, 'connected': true, 'secret_exposed': false},
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
  Future<Map<String, dynamic>> skills() async => {'skills': <Map<String, dynamic>>[]};

  @override
  Future<Map<String, dynamic>> tools() async => {'tools': <Map<String, dynamic>>[]};

  @override
  Future<Map<String, dynamic>> agents() async => {'agents': <Map<String, dynamic>>[]};

  @override
  Future<Map<String, dynamic>> memory({String query = '', int limit = 20}) async =>
      {'memory': <Map<String, dynamic>>[]};

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
  }) async => {'text': prompt, 'provider': 'mock', 'model': 'mock', 'memory_hits': []};

  @override
  Future<Map<String, dynamic>> addMemory(
    String text, {
    List<String> tags = const <String>[],
  }) async => {'memory': {'text': text}};

  @override
  Future<Map<String, dynamic>> runAgent(String name, String prompt) async =>
      {'agent': name, 'text': prompt};

  @override
  Future<Map<String, dynamic>> executeTool(
    String name,
    Map<String, dynamic> arguments, {
    bool approved = false,
  }) async => {'tool': name, 'result': arguments};
}

void main() {
  testWidgets('V3 Flutter project renders full-system 10x10 control center',
      (tester) async {
    await tester.pumpWidget(ResearchOSV3App(api: _WidgetTestApi()));
    await tester.pumpAndSettle();

    expect(find.text('Full System Control Center'), findsOneWidget);
    expect(find.text('10,000,000,000'), findsOneWidget);
    expect(find.text('6^3'), findsOneWidget);
  });
}
