import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:research_os_owner_special/src/native_core_workspace_page.dart';
import 'package:research_os_owner_special/src/owner_api.dart';

class _FakeApi extends OwnerFriendApi {
  @override
  Future<Map<String, dynamic>> health() async => {'status': 'ok'};

  @override
  Future<Map<String, dynamic>> memory() async => {};

  @override
  Future<Map<String, dynamic>> providerStatus() async => {};

  @override
  Future<Map<String, dynamic>> configureProvider({required String baseUrl, required String model, String? apiKey}) async => {};

  @override
  Future<Map<String, dynamic>> testProvider() async => {};

  @override
  Future<Map<String, dynamic>> chat(
    String text, {
    int complexity = 4,
    int risk = 2,
    int parallelism = 2,
    int helperBudget = 0,
    List<String> requestedSkills = const <String>[],
    List<String> requestedTools = const <String>[],
  }) async => {'text': text};

  @override
  Future<Map<String, dynamic>> status() async => {
    'brain_profiles': {'default': 1},
    'helper_scheduler': {'max_active_workers': 12, 'max_logical_helpers': 100},
    'capabilities': ['brain', 'memory', 'evidence'],
  };
}

void main() {
  testWidgets('core workspace exposes all operating surfaces', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: NativeCoreWorkspacePage(api: _FakeApi()),
    ));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 350));

    expect(find.text('Native Core Workspace'), findsOneWidget);
    expect(find.widgetWithText(FilterChip, 'LIVE'), findsOneWidget);
    expect(find.text('Overview'), findsOneWidget);
    expect(find.text('Activity'), findsOneWidget);
    expect(find.text('State'), findsOneWidget);
    expect(find.text('Evidence'), findsOneWidget);
    expect(find.text('Inspector'), findsOneWidget);
    expect(find.text('Simulation'), findsOneWidget);
    expect(find.text('12'), findsOneWidget);
  });

  testWidgets('inspector records an object without granting authority', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: NativeCoreWorkspacePage(api: _FakeApi()),
    ));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 350));

    await tester.ensureVisible(find.text('Inspector'));
    await tester.pump();
    await tester.tap(find.text('Inspector'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 350));
    final inspectorField = find.widgetWithText(TextField, 'Object ID');
    expect(inspectorField, findsOneWidget);
    await tester.enterText(inspectorField, 'EV-001');
    await tester.tap(find.text('Inspect'));
    await tester.pump();
    await tester.pump();

    expect(find.widgetWithText(ListTile, 'EV-001'), findsOneWidget);
    expect(find.textContaining('no authority grant'), findsOneWidget);
  });

  testWidgets('simulation mode is explicit and reversible', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: NativeCoreWorkspacePage(api: _FakeApi()),
    ));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 350));

    await tester.tap(find.widgetWithText(FilterChip, 'LIVE'));
    await tester.pump();
    expect(find.widgetWithText(FilterChip, 'SIMULATION'), findsOneWidget);

    await tester.tap(find.widgetWithText(FilterChip, 'SIMULATION'));
    await tester.pump();
    expect(find.widgetWithText(FilterChip, 'LIVE'), findsOneWidget);
  });
}
