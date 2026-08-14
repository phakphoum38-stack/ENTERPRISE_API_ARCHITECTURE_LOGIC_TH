import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/ui/new_gui/backup_module_page.dart';

void main() {
  testWidgets('Backup module stays disabled on unsupported platforms', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData.dark(useMaterial3: true),
        home: const ResearchBackupModulePage(),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Backup'), findsOneWidget);
    expect(find.text('Windows only'), findsOneWidget);
    expect(find.text('ResearchOSData/backups'), findsOneWidget);

    final backup = tester.widget<FilledButton>(
      find.byKey(const Key('new-gui-backup-now')),
    );
    final openData = tester.widget<OutlinedButton>(
      find.byKey(const Key('new-gui-backup-open-data')),
    );
    expect(backup.onPressed, isNull);
    expect(openData.onPressed, isNull);
    expect(tester.takeException(), isNull);
  });
}
