import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:research_os_owner_special/src/native_core_workspace_page.dart';
import 'package:research_os_owner_special/src/owner_api.dart';

final class _FakeOwnerFriendApi implements OwnerFriendApi {
  @override
  Future<Map<String, dynamic>> health() async => <String, dynamic>{'status': 'ok'};

  @override
  Future<Map<String, dynamic>> status() async => <String, dynamic>{
    'brain_profiles': <String, dynamic>{'default': 'standard'},
    'helper_scheduler': <String, dynamic>{
      'max_active_workers': 4,
      'max_logical_helpers': 100,
    },
    'capabilities': <String>['runtime', 'identity', 'research', 'provider'],
  };

  @override
  Future<Map<String, dynamic>> memory() async => <String, dynamic>{'items': <Object>[]};

  @override
  Future<Map<String, dynamic>> providerStatus() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> configureProvider({
    required String baseUrl,
    required String model,
    String? apiKey,
  }) async => <String, dynamic>{'ok': true};

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
  }) async => <String, dynamic>{
    'text': text,
    'decision': <String, dynamic>{'scale': 'test', 'capacity': 1},
    'helpers': <String, dynamic>{},
    'factory': <String, dynamic>{'stages': <String>[]},
  };
}

void main() {
  testWidgets('Control Center exposes live operating environment panels', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: NativeCoreWorkspacePage(api: _FakeOwnerFriendApi()),
        ),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Native Core Workspace'), findsOneWidget);
    expect(find.text('System Map'), findsOneWidget);
    expect(find.text('Failures'), findsOneWidget);
    expect(find.text('History'), findsOneWidget);
    expect(find.text('Simulation'), findsOneWidget);

    await tester.tap(find.text('System Map'));
    await tester.pumpAndSettle();
    expect(find.text('Live System Map'), findsOneWidget);
    expect(find.text('ROOT'), findsOneWidget);
    expect(find.text('ASSURANCE'), findsOneWidget);

    await tester.tap(find.text('Failures'));
    await tester.pumpAndSettle();
    expect(find.text('No failure feed exposed'), findsOneWidget);

    await tester.tap(find.text('History'));
    await tester.pumpAndSettle();
    expect(find.text('Runtime status observed'), findsOneWidget);
  });
}
