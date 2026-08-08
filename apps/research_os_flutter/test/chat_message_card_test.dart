import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/features/chat/chat_message_card.dart';
import 'package:research_os_flutter/src/features/chat/chat_typing_indicator.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('assistant message shows provider, time, memory and retry', (tester) async {
    var retried = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ChatMessageCard(
            role: 'assistant',
            text: '**พร้อมใช้งาน**',
            provider: 'gemini',
            memoryCount: 2,
            createdAt: DateTime(2026, 8, 8, 20, 30),
            onRetry: () => retried = true,
          ),
        ),
      ),
    );

    expect(find.byKey(const Key('chat-provider-badge')), findsOneWidget);
    expect(find.text('gemini'), findsOneWidget);
    expect(find.text('Memory 2 รายการ'), findsOneWidget);
    expect(find.text('20:30'), findsOneWidget);

    await tester.tap(find.byKey(const Key('chat-retry-response')));
    expect(retried, isTrue);
  });

  testWidgets('user message exposes edit action', (tester) async {
    var edited = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ChatMessageCard(
            role: 'user',
            text: 'แก้ prompt นี้',
            createdAt: DateTime(2026, 8, 8, 20, 31),
            onEdit: () => edited = true,
          ),
        ),
      ),
    );

    expect(find.byKey(const Key('chat-edit-prompt')), findsOneWidget);
    await tester.tap(find.byKey(const Key('chat-edit-prompt')));
    expect(edited, isTrue);
  });

  testWidgets('copy action writes message to clipboard', (tester) async {
    String? clipboardText;
    tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(
      SystemChannels.platform,
      (call) async {
        if (call.method == 'Clipboard.setData') {
          final args = call.arguments as Map<dynamic, dynamic>;
          clipboardText = args['text']?.toString();
        }
        return null;
      },
    );

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: ChatMessageCard(
            role: 'assistant',
            text: 'copy me',
            createdAt: DateTime(2026, 8, 8),
          ),
        ),
      ),
    );

    await tester.tap(find.byKey(const Key('chat-copy-message')));
    await tester.pump();
    expect(clipboardText, 'copy me');
  });

  testWidgets('typing indicator is visible', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(body: ChatTypingIndicator()),
      ),
    );

    expect(find.byKey(const Key('chat-typing-indicator')), findsOneWidget);
    expect(find.text('Research OS กำลังคิด…'), findsOneWidget);
  });
}
