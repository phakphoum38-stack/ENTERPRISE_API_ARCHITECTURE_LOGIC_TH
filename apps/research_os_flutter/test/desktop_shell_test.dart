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
  Future<Map<String, dynamic>> getGoogleWorkspaceDashboard() async =>
      <String, dynamic>{
        'oauth_configured': false,
        'connected': false,
        'app_access': false,
        'local_account_accepted': false,
        'account_mode': 'none',
        'services': <Map<String, dynamic>>[],
      };

  @override
  Future<Map<String, dynamic>> getBrowserUseStatus() async =>
      <String, dynamic>{
        'provider': 'browser_use_cloud',
        'api_key_configured': false,
        'connected': false,
        'token_storage': 'backend_env_only',
      };

  @override
  void close() {}
}

void main() {
  testWidgets('desktop shell shows organized enterprise sidebar', (tester) async {
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
    await tester.pump(const Duration(milliseconds: 150));

    expect(find.byKey(const Key('enterprise-sidebar')), findsOneWidget);
    expect(find.byKey(const Key('desktop-navigation-list')), findsOneWidget);
    expect(find.byKey(const Key('desktop-content-pane')), findsOneWidget);
    expect(find.byKey(const Key('desktop-status-bar')), findsOneWidget);
    expect(find.byKey(const Key('desktop-nav-1')), findsOneWidget);
    expect(find.byKey(const Key('desktop-nav-9')), findsOneWidget);

    final compactWidth =
        tester.getSize(find.byKey(const Key('enterprise-sidebar'))).width;
    final contentWidth =
        tester.getSize(find.byKey(const Key('desktop-content-pane'))).width;

    expect(compactWidth, 76);
    expect(find.byKey(const Key('desktop-shell-title')), findsNothing);

    await tester.tap(find.byKey(const Key('toggle-desktop-sidebar')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 250));

    final expandedWidth =
        tester.getSize(find.byKey(const Key('enterprise-sidebar'))).width;
    final contentWidthWhileExpanded =
        tester.getSize(find.byKey(const Key('desktop-content-pane'))).width;

    expect(expandedWidth, 244);
    expect(expandedWidth, greaterThan(compactWidth));
    expect(contentWidthWhileExpanded, contentWidth);
    expect(find.byKey(const Key('desktop-shell-title')), findsOneWidget);
    expect(find.text('WORKSPACE'), findsWidgets);
    expect(find.text('KNOWLEDGE'), findsWidgets);
    expect(find.text('CONNECTIONS'), findsWidgets);
    expect(find.text('SYSTEM'), findsWidgets);
    expect(find.byKey(const Key('desktop-sidebar-dismiss')), findsOneWidget);

    await tester.tap(find.byKey(const Key('desktop-sidebar-dismiss')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 250));

    expect(
      tester.getSize(find.byKey(const Key('enterprise-sidebar'))).width,
      compactWidth,
    );
    expect(
      tester.getSize(find.byKey(const Key('desktop-content-pane'))).width,
      contentWidth,
    );
    expect(find.byKey(const Key('desktop-sidebar-dismiss')), findsNothing);
    expect(find.byKey(const Key('desktop-nav-1')), findsOneWidget);
    expect(find.byKey(const Key('desktop-nav-9')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
