import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_owner_special/src/friend_app.dart';
import 'package:research_os_owner_special/src/owner_api.dart';

class FakeOwnerFriendApi implements OwnerFriendApi {
  @override
  Future<Map<String, dynamic>> health() async => <String, dynamic>{'status': 'ok'};
  @override
  Future<Map<String, dynamic>> status() async => <String, dynamic>{'brain_profiles': <String, int>{'1^3': 1, '3^3': 27, '6^3': 216, '6^6': 46656, 'fast-1m': 1000000}, 'helper_scheduler': <String, int>{'max_logical_helpers': 1000000, 'max_active_workers': 128}, 'capabilities': <String>['brain', 'skills', 'persistent-memory', 'factory']};
  @override
  Future<Map<String, dynamic>> memory() async => <String, dynamic>{'count': 0, 'items': <Object>[]};
  @override
  Future<Map<String, dynamic>> providerStatus() async => <String, dynamic>{'enabled': false, 'credential_present': false, 'secret_backend': 'test', 'base_url': '', 'model': ''};
  @override
  Future<Map<String, dynamic>> configureProvider({required String baseUrl, required String model, String? apiKey}) async => <String, dynamic>{'enabled': true, 'credential_present': true, 'secret_backend': 'test', 'base_url': baseUrl, 'model': model};
  @override
  Future<Map<String, dynamic>> testProvider() async => <String, dynamic>{'connected': true};
  @override
  Future<Map<String, dynamic>> chat(String text, {int complexity = 4, int risk = 2, int parallelism = 2, int helperBudget = 0, List<String> requestedSkills = const <String>[], List<String> requestedTools = const <String>[]}) async => <String, dynamic>{'text': 'friend:$text', 'decision': <String, dynamic>{'scale': helperBudget >= 1000000 ? 'fast-1m' : '6^6', 'capacity': helperBudget >= 1000000 ? 1000000 : 46656}, 'helpers': <String, dynamic>{'active_workers': 128, 'batches': 7813}, 'factory': <String, dynamic>{'stages': <String>['master', 'factory', 'team', 'tests', 'release']}};
}

void main() {
  testWidgets('Owner Friend desktop uses bounded million-helper mode', (tester) async {
    await tester.pumpWidget(OwnerFriendApp(api: FakeOwnerFriendApi()));
    await tester.enterText(find.byKey(const Key('friend-input')), 'hello');
    await tester.tap(find.byKey(const Key('friend-send')));
    await tester.pumpAndSettle();
    expect(find.text('friend:hello'), findsOneWidget);
    expect(find.text('Brain scale: fast-1m'), findsOneWidget);
    expect(find.text('Logical capacity: 1000000'), findsOneWidget);
    expect(find.text('Active workers: 128'), findsOneWidget);
    expect(find.textContaining('master → factory → team → tests → release'), findsOneWidget);
  });
}
