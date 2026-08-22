import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../lib/src/team_center.dart';

void main() {
  testWidgets('owner can switch teams', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: Scaffold(body: TeamCenter())));
    expect(find.text('Research Team'), findsOneWidget);
    await tester.tap(find.byKey(const Key('team-switcher')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Engineering Team').last);
    await tester.pumpAndSettle();
    expect(find.text('Team ID: engineering'), findsOneWidget);
  });

  testWidgets('owner can create a team', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: Scaffold(body: TeamCenter())));
    await tester.tap(find.byTooltip('Create Team'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'New Research Team');
    await tester.tap(find.text('Create'));
    await tester.pumpAndSettle();
    expect(find.text('Team ID: team-'), findsOneWidget);
    expect(find.text('New Research Team'), findsWidgets);
  });
}
