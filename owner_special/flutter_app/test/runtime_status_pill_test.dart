import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_owner_special/src/owner_api.dart';
import 'package:research_os_owner_special/src/runtime_status_pill.dart';

class _FakeOwnerFriendApi extends OwnerFriendApi {
  @override
  Future<Map<String, dynamic>> health() async => <String, dynamic>{'status': 'ok'};

  @override
  Future<Map<String, dynamic>> status() async => <String, dynamic>{
        'skills': <String>['analysis', 'planning'],
        'tools': <String>['github', 'memory', 'launch-desk'],
        'self_learning': <String, dynamic>{'persistent_reusable': 4},
      };

  @override
  Future<Map<String, dynamic>> memory() async => <String, dynamic>{'count': 0, 'items': <Object>[]};

  @override
  Future<Map<String, dynamic>> providerStatus() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> configureProvider({required String baseUrl, required String model, String? apiKey}) async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> testProvider() async => <String, dynamic>{'connected': true};

  @override
  Future<Map<String, dynamic>> chat(
    String text, {
    int complexity = 4,
    int risk = 2,
    int parallelism = 2,
    int helperBudget = 0,
    List<String> requestedSkills = const <String>[],
    List<String> requestedTools = const <String>[],
  }) async => <String, dynamic>{'text': text};
}

void main() {
  testWidgets('live runtime status renders skills tools and reusable learning', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: RuntimeStatusPill(
          api: _FakeOwnerFriendApi(),
          fallback: const Text('fallback'),
        ),
      ),
    );

    await tester.pump();
    await tester.pumpAndSettle();

    expect(find.text('Connected • S2 T3 L4'), findsOneWidget);
    expect(find.text('fallback'), findsNothing);
    expect(find.byTooltip('Friend runtime • 2 skills • 3 tools • 4 reusable learning records'), findsOneWidget);
  });
}
