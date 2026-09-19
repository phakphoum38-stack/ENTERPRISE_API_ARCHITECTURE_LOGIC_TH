import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:research_os_owner_special/src/github_workbench_page.dart';

void main() {
  Future<void> revealAuthority(WidgetTester tester) async {
    final navigation = find.byType(ListView).first;
    await tester.scrollUntilVisible(
      find.text('Authority'),
      200,
      scrollable: navigation,
    );
    await tester.pump();
  }

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

    await revealAuthority(tester);
    expect(find.text('Authority'), findsOneWidget);
  });

  testWidgets('Workbench keeps mutating execution unavailable in dry run', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: GitHubWorkbenchPage()));
    await tester.pumpAndSettle();

    expect(find.text('Preview only'), findsOneWidget);
    final button = tester.widget<FilledButton>(find.byKey(const Key('github-execute-approved-action')));
    expect(button.onPressed, isNull);

    await revealAuthority(tester);
    await tester.tap(find.text('Authority'));
    await tester.pump();

    expect(find.text('Approve'), findsOneWidget);
    expect(find.text('Authorize'), findsOneWidget);
    expect(find.text('Release / Merge'), findsOneWidget);
    expect(find.text('Human authority required'), findsNWidgets(3));
  });
}
