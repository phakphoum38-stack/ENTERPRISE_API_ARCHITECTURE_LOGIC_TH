import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:research_os_owner_special/src/native_control_center_page.dart';
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
