import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/ui/new_gui/research_os_new_shell.dart';
import 'package:shared_preferences/shared_preferences.dart';

class NewGuiApiClient extends ResearchOSApiClient {
  NewGuiApiClient() : super(baseUrl: 'http://127.0.0.1:8788');

  @override
  Future<Map<String, dynamic>> getHealth() async => <String, dynamic>{
        'status': 'ok',
        'version': '3.2-test',
      };

  @override
  Future<Map<String, dynamic>> getProviders() async => <String, dynamic>{
        'active': 'mock',
        'providers': <String>['mock'],
      };

  @override
  Future<Map<String, dynamic>> getAgents() async => <String, dynamic>{
        'agents': <Map<String, dynamic>>[
          <String, dynamic>{'id': 'planner'},
          <String, dynamic>{'id': 'builder'},
        ],
      };

  @override
  void close() {}
}

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues(<String, Object>{});
  });

  testWidgets('new desktop control center opens on Chat AI with requested greeting', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1600, 1000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData.dark(useMaterial3: true),
        home: ResearchOSNewShell(apiClient: NewGuiApiClient()),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 350));

    expect(find.byKey(const Key('new-gui-shell')), findsOneWidget);
    expect(find.byKey(const Key('new-gui-sidebar')), findsOneWidget);
    expect(find.byKey(const Key('new-gui-navigation-list')), findsOneWidget);
    expect(find.byKey(const Key('new-gui-top-bar')), findsOneWidget);
    expect(find.byKey(const Key('new-gui-main-pane')), findsOneWidget);
    expect(find.byKey(const Key('new-gui-conversation-rail')), findsOneWidget);
    expect(find.byKey(const Key('new-gui-system-inspector')), findsOneWidget);

    expect(find.text('Chat AI'), findsWidgets);
    expect(find.text('สวัสดีเริ่มทำอะไรดี'), findsOneWidget);
    expect(find.text('MAIN'), findsOneWidget);
    expect(find.text('WORKSPACE'), findsOneWidget);
    expect(find.text('Factory'), findsOneWidget);
    expect(find.text('Providers'), findsOneWidget);
    expect(find.text('6^6 ORCHESTRATOR'), findsOneWidget);
    expect(find.text('AMR bounded'), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.tap(find.byKey(const Key('new-gui-nav-providers')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('Live provider data from /v1/providers.'), findsOneWidget);
    expect(find.textContaining('mock'), findsWidgets);
    expect(tester.takeException(), isNull);
  });
}
