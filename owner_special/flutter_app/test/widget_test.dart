import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_owner_special/src/friend_app.dart';
import 'package:research_os_owner_special/src/owner_api.dart';

class FakeOwnerFriendApi implements OwnerFriendApi {
  @override
  Future<Map<String, dynamic>> health() async => <String, dynamic>{'status': 'ok'};

  @override
  Future<Map<String, dynamic>> status() async => <String, dynamic>{
        'brain_profiles': <String, int>{'1^3': 1, '3^3': 27, '6^3': 216, '6^6': 46656},
        'capabilities': <String>['brain', 'skills', 'persistent-memory', 'factory'],
      };

  @override
  Future<Map<String, dynamic>> memory() async => <String, dynamic>{'count': 0, 'items': <Object>[]};

  @override
  Future<Map<String, dynamic>> chat(
    String text, {
    int complexity = 4,
    int risk = 2,
    int parallelism = 2,
    List<String> requestedSkills = const <String>[],
    List<String> requestedTools = const <String>[],
  }) async => <String, dynamic>{
        'text': 'friend:$text',
        'decision': <String, dynamic>{'scale': '6^6', 'capacity': 46656},
        'factory': <String, dynamic>{'stages': <String>['master', 'factory', 'team', 'tests', 'release']},
      };
}

void main() {
  testWidgets('Owner Friend desktop sends a request and shows runtime scale', (tester) async {
    await tester.pumpWidget(OwnerFriendApp(api: FakeOwnerFriendApi()));
    await tester.enterText(find.byKey(const Key('friend-input')), 'hello');
    await tester.tap(find.byKey(const Key('friend-send')));
    await tester.pumpAndSettle();
    expect(find.text('friend:hello'), findsOneWidget);
    expect(find.text('Brain scale: 6^6'), findsOneWidget);
    expect(find.text('Logical capacity: 46656'), findsOneWidget);
    expect(find.textContaining('master → factory → team → tests → release'), findsOneWidget);
  });
}
