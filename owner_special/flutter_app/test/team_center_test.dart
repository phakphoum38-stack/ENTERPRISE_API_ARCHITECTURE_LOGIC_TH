import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:research_os_owner_special/src/team_center.dart';

void main() {
  testWidgets('owner can switch teams and emits team context', (tester) async {
    TeamWorkspace? selected;
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: TeamCenter(onChanged: (team) => selected = team),
      ),
    ));

    expect(find.text('Research Team'), findsOneWidget);
    await tester.tap(find.byKey(const Key('team-switcher')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Engineering Team').last);
    await tester.pumpAndSettle();

    expect(find.text('Engineering Team'), findsOneWidget);
    expect(selected?.id, 'engineering');
  });

  testWidgets('owner can create a team and selects it', (tester) async {
    TeamWorkspace? selected;
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: TeamCenter(onChanged: (team) => selected = team),
      ),
    ));

    await tester.tap(find.byTooltip('Create Team'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'New Research Team');
    await tester.tap(find.text('Create'));
    await tester.pumpAndSettle();

    expect(find.text('New Research Team'), findsWidgets);
    expect(selected?.name, 'New Research Team');
    expect(selected?.id.startsWith('team-'), isTrue);
  });
}
