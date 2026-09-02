import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/app_shell.dart';
import 'package:research_os_flutter/src/features/github/github_dashboard_page.dart';
import 'package:research_os_flutter/src/features/graph/knowledge_graph_page.dart';
import 'package:research_os_flutter/src/features/home/home_page.dart';
import 'package:shared_preferences/shared_preferences.dart';

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
  Future<Map<String, dynamic>> getGoogleIdentityStatus() async =>
      <String, dynamic>{
        'oauth_configured': false,
        'connected': false,
        'account': <String, dynamic>{},
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
          <String, dynamic>{
            'id': 'RES-A',
            'title': 'Research Memory',
            'status': 'active',
          },
          <String, dynamic>{
            'id': 'RES-B',
            'title': 'Knowledge Graph',
            'status': 'validated',
          },
        ],
        'edges': <Map<String, dynamic>>[
          <String, dynamic>{
            'source': 'RES-A',
            'relation': 'supports',
            'target': 'RES-B',
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

Future<void> pumpShell(WidgetTester tester) async {
  await tester.pumpWidget(
    MaterialApp(
      home: ResearchOSAppShell(apiClient: FakeResearchOSApiClient()),
    ),
  );
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 250));
}

Future<void> openSidebarDestination(
  WidgetTester tester,
  String keyName,
) async {
  final finder = find.byKey(Key('v2-nav-$keyName'));
  expect(finder, findsOneWidget);
  await tester.ensureVisible(finder);
  await tester.tap(finder);
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 250));
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
    expect(tester.takeException(), isNull);
  });

  testWidgets('AI voice conversation workspace opens', (tester) async {
    setDesktopTestSize(tester);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await pumpShell(tester);
    await openSidebarDestination(tester, 'conversation');

    expect(find.text('สนทนา AI'), findsOneWidget);
    expect(find.text('Voice Conversation • Friend AI • Local-first'), findsOneWidget);
    expect(find.text('พูดกับ Research OS ได้เลย'), findsOneWidget);
    expect(find.byIcon(Icons.mic), findsOneWidget);
    expect(find.text('พร้อมสนทนา'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('library shows knowledge artifacts', (tester) async {
    setDesktopTestSize(tester);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await pumpShell(tester);
    await openSidebarDestination(tester, 'library');

    expect(find.text('Conversation to Knowledge'), findsOneWidget);
    expect(find.textContaining('active'), findsWidgets);
    expect(tester.takeException(), isNull);
  });

  testWidgets('knowledge graph shows nodes and relationships', (tester) async {
    setDesktopTestSize(tester);
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      MaterialApp(home: KnowledgeGraphPage(apiClient: FakeResearchOSApiClient())),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 150));

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
      MaterialApp(
        home: Scaffold(
          body: GitHubDashboardPage(apiClient: FakeResearchOSApiClient()),
        ),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 150));

    expect(find.text('GitHub Control Center'), findsOneWidget);
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
    await tester.pump(const Duration(milliseconds: 250));
    await openSidebarDestination(tester, 'settings');

    expect(find.text('Active Provider'), findsOneWidget);
    expect(find.text('gemini'), findsWidgets);
    expect(find.text('http://127.0.0.1:8787'), findsOneWidget);

    await tester.tap(find.text('Dark'));
    await tester.pump();
    expect(selectedTheme, ThemeMode.dark);
    expect(tester.takeException(), isNull);
  });
}
