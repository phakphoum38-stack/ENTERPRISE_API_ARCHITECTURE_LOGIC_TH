import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/chat/copilot_chat_widget.dart';

class FakeCopilotApiClient extends ResearchOSApiClient {
  FakeCopilotApiClient() : super(baseUrl: 'http://127.0.0.1:8787');

  String? message;
  String? contextQuery;
  List<String>? contextPaths;
  bool contextRequested = false;

  @override
  Future<Map<String, dynamic>> getCopilotContext({
    String? query,
    List<String> paths = const <String>[],
    int memoryLimit = 5,
  }) async {
    contextRequested = true;
    return const <String, dynamic>{};
  }

  @override
  Future<Map<String, dynamic>> chatWithCopilot({
    required String message,
    List<String> paths = const <String>[],
    String? contextQuery,
    int memoryLimit = 5,
  }) async {
    this.message = message;
    this.contextPaths = paths;
    this.contextQuery = contextQuery;
    return <String, dynamic>{
      'reply': 'Copilot พร้อมบริบท enterprise แล้ว',
      'context': <String, dynamic>{
        'repository': 'phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH',
        'memory_count': 2,
        'files': <Map<String, dynamic>>[
          <String, dynamic>{'path': 'README.md'},
          <String, dynamic>{'path': 'tools/research_os_api/README.md'},
        ],
      },
    };
  }

  @override
  void close() {}
}

void main() {
  testWidgets('copilot chat widget sends chat and shows returned context', (
    tester,
  ) async {
    final apiClient = FakeCopilotApiClient();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SizedBox(
            height: 600,
            child: CopilotChatWidget(apiClient: apiClient),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(
      find.byKey(const Key('copilot-chat-input')),
      'ช่วยอธิบาย architecture นี้',
    );
    await tester.tap(find.byKey(const Key('copilot-chat-send')));
    await tester.pumpAndSettle();

    expect(apiClient.contextRequested, isFalse);
    expect(apiClient.contextQuery, 'ช่วยอธิบาย architecture นี้');
    expect(apiClient.message, 'ช่วยอธิบาย architecture นี้');
    expect(apiClient.contextPaths, <String>[
      'README.md',
      'tools/research_os_api/README.md',
    ]);
    expect(find.text('Copilot พร้อมบริบท enterprise แล้ว'), findsOneWidget);
    expect(
      find.text(
        'phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH • 2 files • 2 memory hits',
      ),
      findsOneWidget,
    );
  });
}
