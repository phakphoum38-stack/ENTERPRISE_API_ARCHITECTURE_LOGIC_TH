import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/chat/chat_page.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ChatFlowApiClient extends ResearchOSApiClient {
  ChatFlowApiClient() : super(baseUrl: 'http://127.0.0.1:8787');

  final List<String> questions = <String>[];

  @override
  Future<Map<String, dynamic>> answerWithMemory(String question) async {
    questions.add(question);
    if (questions.length == 1) {
      return <String, dynamic>{
        'text': 'สวัสดีครับเพื่อน แชทของ Research OS ตอบกลับได้แล้ว',
        'memory_hits': <Object?>[],
      };
    }
    return <String, dynamic>{
      'text': 'จำได้ครับ รอบแรกผมตอบว่าระบบแชทตอบกลับได้แล้ว',
      'memory_hits': <Object?>[],
    };
  }

  @override
  void close() {}
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues(<String, Object>{});
  });

  testWidgets('chat sends replies keeps context and restores session', (tester) async {
    final apiClient = ChatFlowApiClient();

    await tester.pumpWidget(
      MaterialApp(home: ChatPage(apiClient: apiClient)),
    );
    await tester.pumpAndSettle();

    final composer = find.byType(TextField);
    expect(composer, findsOneWidget);

    await tester.enterText(composer, 'สวัสดีเพื่อน ทดสอบแชทตัวเอง');
    await tester.tap(find.byTooltip('ส่ง'));
    await tester.pumpAndSettle();

    expect(find.text('สวัสดีเพื่อน ทดสอบแชทตัวเอง'), findsWidgets);
    expect(
      find.text('สวัสดีครับเพื่อน แชทของ Research OS ตอบกลับได้แล้ว'),
      findsOneWidget,
    );
    expect(apiClient.questions, hasLength(1));
    expect(apiClient.questions.first, 'สวัสดีเพื่อน ทดสอบแชทตัวเอง');

    await tester.enterText(composer, 'จำคำตอบรอบแรกได้ไหม');
    await tester.tap(find.byTooltip('ส่ง'));
    await tester.pumpAndSettle();

    expect(
      find.text('จำได้ครับ รอบแรกผมตอบว่าระบบแชทตอบกลับได้แล้ว'),
      findsOneWidget,
    );
    expect(apiClient.questions, hasLength(2));
    final secondPrompt = apiClient.questions.last;
    expect(secondPrompt, contains('User: สวัสดีเพื่อน ทดสอบแชทตัวเอง'));
    expect(
      secondPrompt,
      contains('Assistant: สวัสดีครับเพื่อน แชทของ Research OS ตอบกลับได้แล้ว'),
    );
    expect(secondPrompt, contains('User: จำคำตอบรอบแรกได้ไหม'));

    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString('research_os_chat_sessions_v1');
    expect(raw, isNotNull);
    final sessions = jsonDecode(raw!) as List<dynamic>;
    expect(sessions, isNotEmpty);
    final messages = (sessions.first as Map<String, dynamic>)['messages'] as List<dynamic>;
    expect(messages, hasLength(4));

    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();

    final reopenedClient = ChatFlowApiClient();
    await tester.pumpWidget(
      MaterialApp(home: ChatPage(apiClient: reopenedClient)),
    );
    await tester.pumpAndSettle();

    expect(find.text('สวัสดีเพื่อน ทดสอบแชทตัวเอง'), findsWidgets);
    expect(
      find.text('สวัสดีครับเพื่อน แชทของ Research OS ตอบกลับได้แล้ว'),
      findsOneWidget,
    );
    expect(find.text('จำคำตอบรอบแรกได้ไหม'), findsOneWidget);
    expect(
      find.text('จำได้ครับ รอบแรกผมตอบว่าระบบแชทตอบกลับได้แล้ว'),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
  });
}
