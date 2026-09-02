import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/app_shell.dart';

class DesktopShellApiClient extends ResearchOSApiClient {
  DesktopShellApiClient() : super(baseUrl: 'http://127.0.0.1:8787');

  @override
  Future<Map<String, dynamic>> getHealth() async => <String, dynamic>{
        'status': 'ok',
        'memory': true,
        'google_workspace': true,
        'version': '0.6.0',
      };

  @override
  Future<Map<String, dynamic>> getProviders() async => <String, dynamic>{
        'active': 'gemini',
        'providers': <String>['gemini'],
      };

  @override
  Future<Map<String, dynamic>> getKnowledgeArtifacts() async =>
      <String, dynamic>{'artifacts': <Map<String, dynamic>>[]};

  @override
  Future<Map<String, dynamic>> getKnowledgeGraph() async =>
      <String, dynamic>{
        'nodes': <Map<String, dynamic>>[],
        'edges': <Map<String, dynamic>>[],
      };

  @override
  Future<Map<String, dynamic>> getGitHubDashboard({String? repository}) async =>
      <String, dynamic>{
        'repository': repository,
        'workflow_runs': <Map<String, dynamic>>[],
        'commits': <Map<String, dynamic>>[],
        'pull_requests': <Map<String, dynamic>>[],
      };

  @override
  void close() {}
}

void main() {
  testWidgets('desktop shell shows the futuristic Research OS sidebar', (tester) async {
    tester.view.physicalSize = const Size(1440, 1000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: ResearchOSAppShell(apiClient: DesktopShellApiClient()),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 250));

    expect(find.byKey(const Key('research-os-sidebar-v2')), findsOneWidget);
    expect(find.byKey(const Key('desktop-content-pane')), findsOneWidget);
    expect(find.byKey(const Key('desktop-status-bar')), findsOneWidget);
    expect(find.byKey(const Key('v2-nav-search')), findsOneWidget);
    expect(find.byKey(const Key('v2-nav-new-chat')), findsOneWidget);
    expect(find.byKey(const Key('v2-nav-conversation')), findsOneWidget);
    expect(find.byKey(const Key('v2-nav-settings')), findsOneWidget);
    expect(find.byKey(const Key('v2-nav-account')), findsOneWidget);

    final compactWidth =
        tester.getSize(find.byKey(const Key('research-os-sidebar-v2'))).width;
    expect(compactWidth, 76);

    await tester.tap(find.byKey(const Key('toggle-desktop-sidebar-v2')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 250));

    final expandedWidth =
        tester.getSize(find.byKey(const Key('research-os-sidebar-v2'))).width;
    expect(expandedWidth, 264);
    expect(expandedWidth, greaterThan(compactWidth));
    expect(find.text('WORKSPACE'), findsOneWidget);
    expect(find.text('ACCOUNT'), findsOneWidget);
    expect(find.text('Search'), findsOneWidget);
    expect(find.text('New chat'), findsOneWidget);
    expect(find.text('สนทนา AI'), findsOneWidget);
    expect(find.text('AI Operating Workspace'), findsOneWidget);
    expect(find.text('Settings'), findsOneWidget);

    await tester.tap(find.byKey(const Key('v2-nav-conversation')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 250));

    expect(find.text('สนทนา AI'), findsOneWidget);
    expect(find.text('Voice Conversation • Friend AI • Local-first'), findsOneWidget);
    expect(find.text('พูดกับ Research OS ได้เลย'), findsOneWidget);
    expect(find.byIcon(Icons.mic), findsOneWidget);
    expect(find.text('พร้อมสนทนา'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
