import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_owner_special/src/update_center.dart';

void main() {
  testWidgets('Update Center renders verification policy and safe default state', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: Scaffold(body: UpdateCenterPage())));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('update-center')), findsOneWidget);
    expect(find.text('Notification & Update Center'), findsOneWidget);
    expect(find.text('Verified update policy'), findsOneWidget);
    expect(find.text('Memory & owner data'), findsOneWidget);
    expect(find.textContaining('SHA-256'), findsOneWidget);
  });
}
