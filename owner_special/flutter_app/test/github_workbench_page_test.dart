import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:research_os_owner_special/src/github_workbench_page.dart';

void main() {
  testWidgets('GitHub Workbench exposes native operating surfaces', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: GitHubWorkbenchPage()));
    await tester.pumpAndSettle();

    expect(find.text('GitHub Workbench'), findsOneWidget);
    expect(find.text('DRY RUN'), findsOneWidget);
    expect(find.text('Repository'), findsOneWidget);
    expect(find.text('Issues'), findsOneWidget);
    expect(find.text('Branches'), findsOneWidget);
    expect(find.text('Files'), findsOneWidget);
    expect(find.text('Changes'), findsOneWidget);
    expect(find.text('Pull Request'), findsOneWidget);
    expect(find.text('Checks'), findsOneWidget);
    expect(find.text('Authority'), findsOneWidget);
  });

  testWidgets('Workbench keeps mutating execution unavailable in dry run', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: GitHubWorkbenchPage()));
    await tester.pumpAndSettle();

    expect(find.text('Preview only'), findsOneWidget);
    final button = tester.widget<FilledButton>(find.byType(FilledButton));
    expect(button.onPressed, isNull);

    await tester.tap(find.text('Authority'));
    await tester.pump();

    expect(find.text('Approve'), findsOneWidget);
    expect(find.text('Authorize'), findsOneWidget);
    expect(find.text('Release / Merge'), findsOneWidget);
    expect(find.text('Human authority required'), findsNWidgets(3));
  });
}
