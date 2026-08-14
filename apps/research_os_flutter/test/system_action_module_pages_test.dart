import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/ui/new_gui/system_action_module_pages.dart';

void main() {
  testWidgets('installer page exposes real candidate actions', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: ResearchInstallerModulePage()),
    );
    await tester.pump();

    expect(find.text('Installer'), findsOneWidget);
    expect(find.byKey(const Key('new-gui-installer-open-output')), findsOneWidget);
    expect(find.byKey(const Key('new-gui-installer-run-latest')), findsOneWidget);
    expect(find.textContaining('Research-OS-Setup-*-x64.exe'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('restore page requires an explicit backup archive path', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: ResearchRestoreModulePage()),
    );
    await tester.pump();

    expect(find.text('Restore'), findsOneWidget);
    expect(find.byKey(const Key('new-gui-restore-archive')), findsOneWidget);
    expect(find.byKey(const Key('new-gui-restore-run')), findsOneWidget);
    expect(find.textContaining('restore-research-os.ps1'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('shell page exposes explicit current-user PowerShell command surface', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(home: ResearchShellModulePage()),
    );
    await tester.pump();

    expect(find.text('Shell'), findsOneWidget);
    expect(find.byKey(const Key('new-gui-shell-command')), findsOneWidget);
    expect(find.byKey(const Key('new-gui-shell-run')), findsOneWidget);
    expect(find.textContaining('current Windows user'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
