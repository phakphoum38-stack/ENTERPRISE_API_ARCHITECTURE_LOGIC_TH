import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/app_shell.dart';
import 'package:shared_preferences/shared_preferences.dart';

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
  Future<Map<String, dynamic>> getGoogleIdentityStatus() async =>
      <String, dynamic>{
        'oauth_configured': true,
        'connected': true,
        'account': <String, dynamic>{
          'name': 'Phakphum Wiriyaphap',
          'email': 'phakphum54@gmail.com',
        },
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
  setUp(() {
    SharedPreferences.setMockInitialValues(<String, Object>{
      'research_os_chat_sessions_v1': jsonEncode(<Map<String, Object>>[
        <String, Object>{
          'id': 'chat-recent-1',
          'title': 'PR Review Blockers and Fixes',
          'updated_at': '2026-08-11T11:45:00.000',
          'messages': <Map<String, Object>>[],
        },
        <String, Object>{
          'id': 'chat-recent-2',
          'title': 'Owner Installer Watch',
          'updated_at': '2026-08-11T11:40:00.000',
          'messages': <Map<String, Object>>[],
        },
      ]),
    });
  });

  testWidgets('desktop shell shows minimal chat and Google account footer', (
    tester,
  ) async {
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
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.byKey(const Key('desktop-shell-title')), findsOneWidget);
    expect(find.byKey(const Key('enterprise-sidebar')), findsOneWidget);
    expect(find.byKey(const Key('desktop-navigation-list')), findsOneWidget);
    expect(find.byKey(const Key('desktop-main-pane')), findsOneWidget);
    expect(find.byKey(const Key('desktop-status-bar')), findsNothing);
    expect(find.byKey(const Key('desktop-new-chat')), findsOneWidget);
    expect(find.byKey(const Key('desktop-search')), findsOneWidget);
    expect(find.byKey(const Key('desktop-account-footer')), findsOneWidget);
    expect(find.text('Recents'), findsOneWidget);
    expect(find.text('PR Review Blockers and Fixes'), findsOneWidget);
    expect(find.text('Owner Installer Watch'), findsOneWidget);
    expect(find.text('phakphum54@gmail.com'), findsOneWidget);

    final before =
        tester.getSize(find.byKey(const Key('enterprise-sidebar'))).width;
    expect(before, 300);

    await tester.tap(
      find.byKey(const Key('desktop-recent-chat-chat-recent-2')),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 250));
    expect(find.byKey(const Key('minimal-chat-page')), findsOneWidget);
    expect(find.text('AI Workspace'), findsNothing);

    await tester.tap(find.byKey(const Key('desktop-account-footer')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('research-account-sheet')), findsOneWidget);
    expect(find.byKey(const Key('account-email')), findsOneWidget);
    expect(find.text('phakphum54@gmail.com'), findsWidgets);
    expect(find.byKey(const Key('google-sign-out-button')), findsOneWidget);

    await tester.tap(find.byTooltip('ปิด'));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const Key('desktop-new-chat')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 250));

    final prefs = await SharedPreferences.getInstance();
    final stored = jsonDecode(
      prefs.getString('research_os_chat_sessions_v1')!,
    ) as List<dynamic>;
    expect(stored.length, 3);
    expect((stored.first as Map<String, dynamic>)['title'], 'บทสนทนาใหม่');

    await tester.tap(find.byKey(const Key('toggle-desktop-sidebar')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 250));
    final after =
        tester.getSize(find.byKey(const Key('enterprise-sidebar'))).width;

    expect(after, 72);
    expect(after, lessThan(before));
    expect(find.byKey(const Key('desktop-new-chat')), findsNothing);
    expect(find.byKey(const Key('desktop-nav-1')), findsOneWidget);
    expect(find.byKey(const Key('desktop-nav-9')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
