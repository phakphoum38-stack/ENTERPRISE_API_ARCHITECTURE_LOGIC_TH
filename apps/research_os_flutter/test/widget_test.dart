import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/app_shell.dart';
import 'package:research_os_flutter/src/features/home/home_page.dart';
import 'package:shared_preferences/shared_preferences.dart';

class FakeResearchOSApiClient extends ResearchOSApiClient {
  FakeResearchOSApiClient() : super(baseUrl: 'http://127.0.0.1:8787');

  @override
  Future<Map<String, dynamic>> getHealth() async => <String, dynamic>{
        'status': 'ok',
        'memory': true,
        'version': '0.6.0',
      };

  @override
  Future<Map<String, dynamic>> getProviders() async => <String, dynamic>{
        'active': 'gemini',
        'providers': <String>['mock', 'gemini'],
      };

  @override
  Future<Map<String, dynamic>> getKnowledgeArtifacts() async => <String, dynamic>{
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
  Future<Map<String, dynamic>> getKnowledgeGraph() async => <String, dynamic>{
        'nodes': <Map<String, dynamic>>[
          <String, dynamic>{'id': 'RES-A', 'title': 'Research Memory', 'status': 'active'},
          <String, dynamic>{'id': 'RES-B', 'title': 'Knowledge Graph', 'status': 'validated'},
        ],
        'edges': <Map<String, dynamic>>[
          <String, dynamic>{'source': 'RES-A', 'relation': 'supports', 'target': 'RES-B'},
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
          <String, dynamic>{'sha': 'abc1234', 'message': 'Add GitHub dashboard', 'author': 'Phakphum'},
        ],
        'pull_requests': <Map<String, dynamic>>[],
      };

  @override
  Future<Map<String, dynamic>> answerWithMemory(String question) async =>
      <String, dynamic>{
        'text': 'คำตอบจาก Gemini ที่ใช้ความรู้ในห้องสมุด',
        'memory_hits': <Map<String, dynamic>>[<String, dynamic>{'artifact_id': 'RES-TEST'}],
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

Future<void> openDesktopDestination(WidgetTester tester, int index) async {
  final finder = find.byKey(Key('desktop-nav-$index'));
  expect(finder, findsOneWidget);
  await tester.ensureVisible(finder);
  await tester.tap(finder);
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 150));
}

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues(<String, Object>{});
  });

  testWidgets('home dashboard shows Research OS status', (tester) async {
    setDesktopTestSize(tester);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(home: HomePage(apiClient: FakeResearchOSApiClient())),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Research OS'), findsOneWidget);
    expect(find.text('System status'), findsOneWidget);
    expect(find.text('Local API'), findsOneWidget);
    expect(find.text('Online'), findsOneWidget);
    expect(find.text('gemini'), findsOneWidget);
    expect(find.text('Ready'), findsOneWidget);
    expect(find.text('0.6.0'), findsWidgets);
    expect(tester.takeException(), isNull);
  });

  testWidgets('AI Chat answers with memory', (tester) async {
    setDesktopTestSize(tester);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(home: ResearchOSAppShell(apiClient: FakeResearchOSApiClient())),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    await openDesktopDestination(tester, 1);

    await tester.enterText(find.byType(TextField).first, 'บ้านเรามีความรู้อะไรบ้าง');
    await tester.tap(find.byTooltip('ส่ง'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    expect(find.text('คำตอบจาก Gemini ที่ใช้ความรู้ในห้องสมุด'), findsOneWidget);
    expect(find.text('Memory 1 รายการ'), findsOneWidget);
    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getString('research_os_chat_sessions_v1'), isNotNull);
    expect(tester.takeException(), isNull);
  });

  testWidgets('library shows knowledge artifacts', (tester) async {
    setDesktopTestSize(tester);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(home: ResearchOSAppShell(apiClient: FakeResearchOSApiClient())),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    await openDesktopDestination(tester, 3);

    expect(find.text('Conversation to Knowledge'), findsOneWidget);
    expect(find.textContaining('active'), findsWidgets);
    expect(tester.takeException(), isNull);
  });

  testWidgets('knowledge graph shows nodes and relationships', (tester) async {
    setDesktopTestSize(tester);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(home: ResearchOSAppShell(apiClient: FakeResearchOSApiClient())),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    await openDesktopDestination(tester, 4);

    expect(find.byKey(const Key('knowledge-graph-heading')), findsOneWidget);
    expect(find.text('Research Memory'), findsOneWidget);
    expect(find.text('Knowledge Graph'), findsWidgets);
    expect(find.text('RES-A → RES-B'), findsOneWidget);
    expect(find.textContaining('supports'), findsWidgets);
    expect(tester.takeException(), isNull);
  });

  testWidgets('GitHub dashboard shows workflows and commits', (tester) async {
    setDesktopTestSize(tester);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(home: ResearchOSAppShell(apiClient: FakeResearchOSApiClient())),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    await openDesktopDestination(tester, 5);

    expect(find.text('Research OS Flutter'), findsOneWidget);
    expect(find.text('Add GitHub dashboard'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('settings shows provider and changes theme mode', (tester) async {
    setDesktopTestSize(tester);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    ThemeMode selectedTheme = ThemeMode.system;

    await tester.pumpWidget(
      MaterialApp(
        home: ResearchOSAppShell(
          apiClient: FakeResearchOSApiClient(),
          themeMode: selectedTheme,
          onThemeModeChanged: (value) => selectedTheme = value,
        ),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    await openDesktopDestination(tester, 8);

    expect(find.text('Active Provider'), findsOneWidget);
    expect(find.text('gemini'), findsWidgets);
    expect(find.text('http://127.0.0.1:8787'), findsOneWidget);

    await tester.tap(find.text('Dark'));
    await tester.pump();
    expect(selectedTheme, ThemeMode.dark);
    expect(tester.takeException(), isNull);
  });
}
