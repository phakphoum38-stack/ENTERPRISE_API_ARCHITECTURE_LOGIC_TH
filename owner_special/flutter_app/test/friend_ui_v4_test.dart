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
  Future<Map<String, dynamic>> testProvider() async => <Map<String, dynamic>>{'connected': true};

  @override
  Future<Map<String, dynamic>> chat(String text, {int complexity = 4, int risk = 2, int parallelism = 2, int helperBudget = 0, List<String> requestedSkills = const <String>[], List<String> requestedTools = const <String>[]}) async {
    this.requestedTools = List<String>.from(requestedTools);
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

    final webTool = find.textContaining('Web · implemented');
    final pythonTool = find.textContaining('Python · implemented');
    expect(webTool, findsOneWidget);
    expect(pythonTool, findsOneWidget);

    // Keep the assertion independent of the test viewport size. The tools live
    // in a scrollable panel, so first bring the target into the hit-testable
    // viewport instead of assuming a fixed chip coordinate.
    await tester.ensureVisible(webTool);
    await tester.pumpAndSettle();
    expect(tester.getTopLeft(webTool).dy, greaterThanOrEqualTo(0));
    expect(tester.getBottomRight(webTool).dy, lessThanOrEqualTo(tester.binding.renderView.size.height));
    await tester.tap(webTool);

    await tester.enterText(find.byKey(const Key('friend-v4-input')), 'ทดสอบเครื่องมือ');
    await tester.tap(find.byKey(const Key('friend-v4-send')));
    await tester.pumpAndSettle();

    expect(api.requestedTools, contains('web'));
    expect(find.text('friend:ทดสอบเครื่องมือ'), findsOneWidget);
  });
}
