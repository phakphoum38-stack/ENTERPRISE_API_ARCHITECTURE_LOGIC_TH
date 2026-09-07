import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../lib/src/friend_app_shell.dart';
import '../lib/src/friend_theme.dart';
import '../lib/src/mission_control_desktop_page.dart';

Widget _host(Widget child) => MaterialApp(theme: FriendTheme.build(), home: Scaffold(body: child));

void main() {
  testWidgets('empty projection is explicit and read-only', (tester) async {
    await tester.pumpWidget(_host(const MissionControlDesktopPage()));

    expect(find.text('Mission Control'), findsOneWidget);
    expect(find.text('Waiting for a validated Phase 4I projection'), findsOneWidget);
    expect(find.text('Mission Control is waiting for validated state.'), findsOneWidget);
    expect(find.text('No execution action is available from this surface.'), findsOneWidget);
    expect(find.text('INVALID PROJECTION'), findsOneWidget);
  });

  testWidgets('renders bounded panel types and explicit states', (tester) async {
    final projection = <String, dynamic>{
      'schema': 'research-os-mission-control-ui-projection/v1',
      'owner_id': 'owner-special',
      'read_only': true,
      'state_summary': <String, dynamic>{
        'gate_status': 'FAILED',
        'build_identity_status': 'PENDING',
        'read_only': true,
      },
      'truncation': <String, dynamic>{'timeline': true},
      'panels': <Map<String, dynamic>>[
        <String, dynamic>{'id': 'metric', 'type': 'metric', 'title': 'Run count', 'value': '12'},
        <String, dynamic>{'id': 'status', 'type': 'status', 'title': 'Gate', 'value': 'PENDING'},
        <String, dynamic>{'id': 'table', 'type': 'table', 'title': 'Evidence', 'rows': <Object>['row 1']},
        <String, dynamic>{'id': 'timeline', 'type': 'timeline', 'title': 'Timeline', 'steps': <Object>['step 1']},
        <String, dynamic>{'id': 'health', 'type': 'capability-health', 'title': 'Health', 'items': <Object>['healthy']},
        <String, dynamic>{'id': 'text', 'type': 'text', 'title': 'Trace', 'value': 'read-only trace'},
      ],
    };

    await tester.pumpWidget(_host(MissionControlDesktopPage(projection: projection)));

    expect(find.text('Owner: owner-special'), findsOneWidget);
    expect(find.text('READ ONLY'), findsOneWidget);
    expect(find.text('FAILED'), findsWidgets);
    expect(find.text('PENDING'), findsWidgets);
    expect(find.text('12'), findsOneWidget);
    expect(find.text('row 1'), findsOneWidget);
    expect(find.text('step 1'), findsOneWidget);
    expect(find.text('healthy'), findsOneWidget);
    expect(find.text('read-only trace'), findsOneWidget);
    expect(find.byKey(const Key('mission-control-truncation')), findsOneWidget);
  });

  testWidgets('unsafe or unknown status is fail-closed to UNKNOWN', (tester) async {
    final projection = <String, dynamic>{
      'read_only': true,
      'owner_id': 'owner-special',
      'state_summary': <String, dynamic>{
        'gate_status': 'NOT_A_REAL_STATUS',
        'build_identity_status': 'EXECUTE_NOW',
      },
    };

    await tester.pumpWidget(_host(MissionControlDesktopPage(projection: projection)));

    expect(find.byKey(const Key('mission-status-UNKNOWN')), findsNWidgets(2));
    expect(find.text('NOT_A_REAL_STATUS'), findsNothing);
    expect(find.text('EXECUTE_NOW'), findsNothing);
  });

  testWidgets('shell exposes Mission Control without adding an execution callback', (tester) async {
    var selected = -1;
    await tester.pumpWidget(_host(FriendAppShell(
      index: 0,
      onIndexChanged: (value) => selected = value,
      pages: const <Widget>[Text('Friend page')],
      teamCenter: const SizedBox.shrink(),
      status: const Text('status'),
    )));

    expect(find.text('Mission Control'), findsOneWidget);
    expect(find.text('Mission Control is waiting for validated state.'), findsOneWidget);
    await tester.tap(find.text('Mission Control'));
    await tester.pump();
    expect(selected, 0);
  });
}
