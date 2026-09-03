import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_owner_special/src/friend_ui_v4.dart';
import 'package:research_os_owner_special/src/owner_api.dart';

class _FakeApi implements OwnerFriendApi {
  List<String> requestedTools = const <String>[];

  @override
  Future<Map<String, dynamic>> health() async => <String, dynamic>{'status': 'ok'};

  @override
  Future<Map<String, dynamic>> status() async => <String, dynamic>{'capabilities': <String>['brain', 'skills', 'persistent-memory', 'factory']};

  @override
  Future<Map<String, dynamic>> memory() async => <String, dynamic>{'count': 0, 'items': <Object>[]};

  @override
  Future<Map<String, dynamic>> providerStatus() async => <String, dynamic>{'enabled': false};

  @override
  Future<Map<String, dynamic>> configureProvider({required String baseUrl, required String model, String? apiKey}) async => <String, dynamic>{'enabled': true};

  @override
  Future<Map<String, dynamic>> testProvider() async => <String, dynamic>{'connected': true};

  @override
  Future<Map<String, dynamic>> chat(String text, {int complexity = 4, int risk = 2, int parallelism = 2, int helperBudget = 0, List<String> requestedSkills = const <String>[], List<String> requestedTools = const <String>[]}) async {
    requestedTools = List<String>.from(requestedTools);
    this.requestedTools = requestedTools;
    return <String, dynamic>{
      'text': 'friend:$text',
      'provider': 'test-provider',
      'decision': <String, dynamic>{'scale': 'fast-1m', 'tools': requestedTools},
    };
  }
}

void main() {
  testWidgets('V4 always keeps the chat composer visible', (tester) async {
    final api = _FakeApi();
    await tester.pumpWidget(OwnerFriendAppV4(api: api));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('friend-v4-input')), findsOneWidget);
    expect(find.byKey(const Key('friend-v4-send')), findsOneWidget);
    expect(find.text('พิมพ์ข้อความถึง Research OS Friend…'), findsOneWidget);
  });

  testWidgets('V4 exposes unified tools and sends selected tools', (tester) async {
    final api = _FakeApi();
    await tester.pumpWidget(OwnerFriendAppV4(api: api));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('friend-v4-tools-menu')));
    await tester.pumpAndSettle();
    expect(find.textContaining('Web · implemented'), findsOneWidget);
    expect(find.textContaining('Python · implemented'), findsOneWidget);

    await tester.tap(find.textContaining('Web · implemented'));
    await tester.enterText(find.byKey(const Key('friend-v4-input')), 'ทดสอบเครื่องมือ');
    await tester.tap(find.byKey(const Key('friend-v4-send')));
    await tester.pumpAndSettle();

    expect(api.requestedTools, contains('web'));
    expect(find.text('friend:ทดสอบเครื่องมือ'), findsOneWidget);
  });
}
