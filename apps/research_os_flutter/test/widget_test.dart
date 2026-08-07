import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/app_shell.dart';
import 'package:research_os_flutter/src/features/home/home_page.dart';

class FakeResearchOSApiClient extends ResearchOSApiClient {
  FakeResearchOSApiClient() : super(baseUrl: 'http://127.0.0.1:8787');

  @override
  Future<Map<String, dynamic>> getHealth() async => <String, dynamic>{
        'status': 'ok',
        'memory': true,
      };

  @override
  Future<Map<String, dynamic>> getProviders() async => <String, dynamic>{
        'active': 'gemini',
        'providers': <String>['mock', 'gemini'],
      };

  @override
  Future<Map<String, dynamic>> getKnowledgeArtifacts() async =>
      <String, dynamic>{
        'artifacts': <Map<String, dynamic>>[
          <String, dynamic>{
            'artifact_id': 'RES-20260806-CONVERSATION_TO_KNOWLEDGE',
            'title': 'Conversation to Knowledge',
            'status': 'active',
            'path': 'research/artifacts/example.md',
          },
        ],
      };

  @override
  Future<Map<String, dynamic>> getGitHubDashboard({String? repository}) async =>
      <String, dynamic>{
        'repository': repository,
        'default_branch': 'main',
        'visibility': 'public',
        'open_issues_count': 2,
        'forks_count': 1,
        'workflow_runs': <Map<String, dynamic>>[
          <String, dynamic>{
            'name': 'Research OS Flutter',
            'status': 'completed',
            'conclusion': 'success',
            'branch': 'main',
            'event': 'push',
          },
        ],
        'commits': <Map<String, dynamic>>[
          <String, dynamic>{
            'sha': 'abc1234',
            'message': 'Add GitHub dashboard',
            'author': 'Phakphum',
          },
        ],
        'pull_requests': <Map<String, dynamic>>[],
      };

  @override
  Future<Map<String, dynamic>> answerWithMemory(String question) async =>
      <String, dynamic>{
        'text': 'คำตอบจาก Gemini ที่ใช้ความรู้ในห้องสมุด',
        'memory_hits': <Map<String, dynamic>>[
          <String, dynamic>{'artifact_id': 'RES-TEST'},
        ],
      };

  @override
  Future<Map<String, dynamic>> generateText(String prompt) async =>
      <String, dynamic>{'text': 'คำตอบจาก Gemini โดยตรง'};

  @override
  void close() {}
}

void setDesktopTestSize(WidgetTester tester) {
  tester.view.physicalSize = const Size(1200, 900);
  tester.view.devicePixelRatio = 1.0;
}

void main() {
  testWidgets('home dashboard shows Research OS status', (tester) async {
    setDesktopTestSize(tester);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: HomePage(apiClient: FakeResearchOSApiClient()),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('บ้านของเรา'), findsOneWidget);
    expect(find.text('API Health'), findsOneWidget);
    expect(find.text('ok'), findsOneWidget);
    expect(find.text('Active Provider'), findsOneWidget);
    expect(find.text('gemini'), findsOneWidget);
    expect(find.text('AI Memory'), findsWidgets);
    expect(find.text('ready'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('AI Chat answers with memory', (tester) async {
    setDesktopTestSize(tester);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: ResearchOSAppShell(apiClient: FakeResearchOSApiClient()),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    await tester.tap(find.text('AI Chat'));
    await tester.pump();

    expect(find.text('คุยกับ Gemini'), findsOneWidget);
    expect(find.text('ใช้ Memory'), findsOneWidget);

    await tester.enterText(find.byType(TextField).first, 'บ้านเรามีความรู้อะไรบ้าง');
    await tester.tap(find.byTooltip('ส่ง'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('บ้านเรามีความรู้อะไรบ้าง'), findsOneWidget);
    expect(find.text('คำตอบจาก Gemini ที่ใช้ความรู้ในห้องสมุด'), findsOneWidget);
    expect(find.text('อ้างอิง Memory 1 รายการ'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('library shows knowledge artifacts', (tester) async {
    setDesktopTestSize(tester);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: ResearchOSAppShell(apiClient: FakeResearchOSApiClient()),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    await tester.tap(find.text('ห้องสมุด'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('ห้องสมุดความรู้'), findsOneWidget);
    expect(find.text('Conversation to Knowledge'), findsOneWidget);
    expect(find.text('สถานะ: active'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('GitHub dashboard shows workflows and commits', (tester) async {
    setDesktopTestSize(tester);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: ResearchOSAppShell(apiClient: FakeResearchOSApiClient()),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    await tester.tap(find.text('GitHub'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('ศูนย์ควบคุม GitHub'), findsOneWidget);
    expect(find.text('Research OS Flutter'), findsOneWidget);
    expect(find.text('Add GitHub dashboard'), findsOneWidget);
    expect(find.text('main'), findsWidgets);
    expect(tester.takeException(), isNull);
  });
}
