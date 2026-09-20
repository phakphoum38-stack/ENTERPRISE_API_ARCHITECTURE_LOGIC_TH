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

  @override
  Future<Map<String, dynamic>> authStatus() async => <String, dynamic>{'authenticated': false};

  @override
  Future<Map<String, dynamic>> startGoogleIdentity() async => <String, dynamic>{'started': false};

  @override
  Future<Map<String, dynamic>> exchangeGoogleIdentityHandoff(String state) async =>
      <String, dynamic>{'exchanged': false, 'state': state};

  @override
  Future<Map<String, dynamic>> signOut() async => <String, dynamic>{'signed_out': true};

  @override
  void setSession(String token) {}

  @override
  void clearSession() {}
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

    await tester.pump();
    await tester.pump(const Duration(milliseconds: 350));

    expect(find.text('Native Core Workspace'), findsOneWidget);
    expect(find.text('System Map'), findsOneWidget);
    expect(find.text('Failures'), findsOneWidget);
    expect(find.text('History'), findsOneWidget);
    expect(find.text('Simulation'), findsOneWidget);

    await tester.tap(find.text('System Map'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 350));
    expect(find.text('Live System Map'), findsOneWidget);
    expect(find.text('ROOT'), findsOneWidget);
    await tester.drag(find.byType(TabBarView).last, const Offset(0, -300));
    await tester.pump();
    expect(find.text('ASSURANCE'), findsOneWidget);

    await tester.ensureVisible(find.text('Failures'));
    await tester.pump();
    await tester.tap(find.text('Failures'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 350));
    expect(find.text('No failure feed exposed'), findsOneWidget);

    await tester.ensureVisible(find.text('History'));
    await tester.pump();
    await tester.tap(find.text('History'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 350));
    expect(find.text('Runtime status observed'), findsOneWidget);
  });
}
