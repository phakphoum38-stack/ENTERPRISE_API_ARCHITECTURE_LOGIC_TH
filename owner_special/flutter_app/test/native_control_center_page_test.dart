import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:research_os_owner_special/src/native_control_center_page.dart';
import 'package:research_os_owner_special/src/owner_api.dart';

class _FakeApi extends OwnerFriendApi {
  @override
  Future<Map<String, dynamic>> health() async => const <String, dynamic>{'status': 'ok'};

  @override
  Future<Map<String, dynamic>> memory() async => const <String, dynamic>{'items': <Object>[]};

  @override
  Future<Map<String, dynamic>> providerStatus() async => const <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> configureProvider({required String baseUrl, required String model, String? apiKey}) async => const <String, dynamic>{'ok': true};

  @override
  Future<Map<String, dynamic>> testProvider() async => const <String, dynamic>{'connected': true};

  @override
  Future<Map<String, dynamic>> chat(String text, {int complexity = 4, int risk = 2, int parallelism = 2, int helperBudget = 0, List<String> requestedSkills = const <String>[], List<String> requestedTools = const <String>[]}) async => const <String, dynamic>{'text': 'ok', 'decision': <String, dynamic>{}, 'helpers': <String, dynamic>{}, 'factory': <String, dynamic>{'stages': <Object>[]}};
  @override
  Future<Map<String, dynamic>> status() async => {
    'brain_profiles': {'default': 1},
    'helper_scheduler': {'max_active_workers': 12, 'max_logical_helpers': 100},
    'capabilities': ['brain', 'memory', 'evidence'],
  };
}

void main() {
  testWidgets('control center exposes command center and inspector', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: NativeControlCenterPage(api: _FakeApi()),
    ));
    await tester.pumpAndSettle();

    expect(find.text('Control Center'), findsOneWidget);
    expect(find.text('System Map'), findsOneWidget);
    expect(find.text('Human Control Boundary'), findsOneWidget);
    expect(find.text('Universal Inspector'), findsOneWidget);
    expect(find.text('Ctrl/⌘ K'), findsOneWidget);
    expect(find.text('Approve — human'), findsOneWidget);
  });

  testWidgets('inspector records selected object without granting authority', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: NativeControlCenterPage(api: _FakeApi()),
    ));
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField).last, 'EV-001');
    await tester.tap(find.text('Inspect'));
    await tester.pump();

    expect(find.text('EV-001'), findsOneWidget);
    expect(find.textContaining('Provenance'), findsOneWidget);
  });
}
