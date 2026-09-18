import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:research_os_owner_special/src/native_core_workspace_page.dart';
import 'package:research_os_owner_special/src/owner_api.dart';

class _FakeApi extends OwnerFriendApi {
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
    await tester.pumpAndSettle();

    expect(find.text('Native Core Workspace'), findsOneWidget);
    expect(find.text('LIVE'), findsOneWidget);
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
    await tester.pumpAndSettle();

    await tester.tap(find.text('Inspector'));
    await tester.pump();
    await tester.enterText(find.byType(TextField).last, 'EV-001');
    await tester.tap(find.text('Inspect'));
    await tester.pump();

    expect(find.text('EV-001'), findsOneWidget);
    expect(find.textContaining('no authority grant'), findsOneWidget);
  });

  testWidgets('simulation mode is explicit and reversible', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: NativeCoreWorkspacePage(api: _FakeApi()),
    ));
    await tester.pumpAndSettle();

    await tester.tap(find.text('LIVE'));
    await tester.pump();
    expect(find.text('SIMULATION'), findsOneWidget);

    await tester.tap(find.text('SIMULATION'));
    await tester.pump();
    expect(find.text('LIVE'), findsOneWidget);
  });
}
