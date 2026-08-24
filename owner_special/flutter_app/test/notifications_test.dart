import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_owner_special/src/notifications.dart';

void main() {
  testWidgets('Owner notifications track unread events and clear history', (tester) async {
    final center = OwnerNotificationCenter.instance;
    center.startSession(serviceConnected: true);

    await tester.pumpWidget(MaterialApp(home: Scaffold(body: OwnerNotificationsPage(center: center))));
    await tester.pump();

    expect(find.text('Friend Service connected'), findsOneWidget);
    expect(center.unreadCount, 1);

    center.addSuccess('Provider connected', 'mock-model is ready');
    await tester.pump();
    expect(find.text('Provider connected'), findsOneWidget);
    expect(center.unreadCount, 2);

    await tester.tap(find.byKey(const Key('notifications-mark-read')));
    await tester.pump();
    expect(center.unreadCount, 0);

    await tester.tap(find.byKey(const Key('notifications-clear')));
    await tester.pump();
    expect(find.text('No notifications yet'), findsOneWidget);
  });
}
