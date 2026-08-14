import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/platform/local_api_manager.dart';
import 'package:research_os_flutter/src/ui/new_gui/backup_module_page.dart';

void main() {
  testWidgets('Backup module reflects real platform support without fake actions', (
    tester,
  ) async {
    const manager = LocalApiManager();

    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData.dark(useMaterial3: true),
        home: const ResearchBackupModulePage(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Backup'), findsOneWidget);
    expect(
      find.text(manager.supported ? 'Windows ready' : 'Windows only'),
      findsOneWidget,
    );
    expect(find.text('ResearchOSData/backups'), findsOneWidget);

    final backup = tester.widget<FilledButton>(
      find.byKey(const Key('new-gui-backup-now')),
    );
    final openData = tester.widget<OutlinedButton>(
      find.byKey(const Key('new-gui-backup-open-data')),
    );

    if (manager.supported) {
      expect(backup.onPressed, isNotNull);
      expect(openData.onPressed, isNotNull);
    } else {
      expect(backup.onPressed, isNull);
      expect(openData.onPressed, isNull);
    }
    expect(tester.takeException(), isNull);
  });
}
