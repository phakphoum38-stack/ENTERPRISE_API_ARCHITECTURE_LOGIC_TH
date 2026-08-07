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
  testWidgets('desktop shell shows workspace chrome and collapsible sidebar',
      (tester) async {
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
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.byKey(const Key('desktop-shell-title')), findsOneWidget);
    expect(find.text('Research OS Desktop'), findsOneWidget);
    expect(find.byKey(const Key('desktop-workspace-title')), findsOneWidget);
    expect(find.text('Home Dashboard'), findsOneWidget);
    expect(find.byKey(const Key('desktop-navigation-rail')), findsOneWidget);
    expect(find.byKey(const Key('desktop-status-bar')), findsOneWidget);

    await tester.tap(find.byKey(const Key('toggle-desktop-sidebar')));
    await tester.pump();

    final rail = tester.widget<NavigationRail>(
      find.byKey(const Key('desktop-navigation-rail')),
    );
    expect(rail.extended, isFalse);
    expect(tester.takeException(), isNull);
  });
}
