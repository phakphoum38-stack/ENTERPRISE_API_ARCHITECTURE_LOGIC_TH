import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/features/checkin/check_in_page.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  testWidgets('check-in records local check-in and check-out history', (
    tester,
  ) async {
    SharedPreferences.setMockInitialValues(<String, Object>{});
    tester.view.physicalSize = const Size(1200, 900);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const MaterialApp(home: CheckInPage()));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('checkin-page')), findsOneWidget);
    expect(find.text('Check-in'), findsOneWidget);
    expect(find.text('พร้อมเช็คอิน'), findsOneWidget);

    await tester.enterText(find.byKey(const Key('checkin-note')), 'กะเช้า');
    await tester.tap(find.byKey(const Key('checkin-button')));
    await tester.pumpAndSettle();

    expect(find.text('กำลังเช็คอิน'), findsOneWidget);
    expect(find.text('ACTIVE'), findsOneWidget);
    expect(find.textContaining('กะเช้า'), findsOneWidget);

    await tester.enterText(find.byKey(const Key('checkin-note')), 'เสร็จงาน');
    await tester.tap(find.byKey(const Key('checkout-button')));
    await tester.pumpAndSettle();

    expect(find.text('พร้อมเช็คอิน'), findsOneWidget);
    expect(find.text('DONE'), findsOneWidget);
    expect(find.textContaining('กะเช้า • เสร็จงาน'), findsOneWidget);

    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString('research_os_checkin_records_v1');
    expect(raw, isNotNull);
    final decoded = jsonDecode(raw!) as List<dynamic>;
    expect(decoded, hasLength(1));
    final record = Map<String, dynamic>.from(decoded.single as Map);
    expect(record['check_in'], isNotEmpty);
    expect(record['check_out'], isNotEmpty);
    expect(record['note'], 'กะเช้า • เสร็จงาน');
    expect(tester.takeException(), isNull);
  });

  testWidgets('check-in page is usable on a phone viewport', (tester) async {
    SharedPreferences.setMockInitialValues(<String, Object>{});
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const MaterialApp(home: CheckInPage()));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('checkin-page')), findsOneWidget);
    expect(find.byKey(const Key('checkin-button')), findsOneWidget);
    expect(find.byKey(const Key('checkout-button')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
