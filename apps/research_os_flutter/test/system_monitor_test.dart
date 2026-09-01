import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/monitor/system_monitor_page.dart';

class FakeSystemMonitorApiClient extends ResearchOSApiClient {
  FakeSystemMonitorApiClient() : super(baseUrl: 'http://127.0.0.1:8787');

  @override
  Future<Map<String, dynamic>> getHealth() async => <String, dynamic>{
        'status': 'ok',
        'service': 'research-os-api',
        'memory': true,
      };

  @override
  Future<Map<String, dynamic>> getProviders() async => <String, dynamic>{
        'active': 'gemini',
        'providers': <String>['mock', 'gemini'],
      };

  @override
  Future<Map<String, dynamic>> getGitHubDashboard({String? repository}) async =>
      <String, dynamic>{
        'workflow_runs': <Map<String, dynamic>>[
          <String, dynamic>{
            'name': 'Research OS Flutter',
            'status': 'completed',
            'conclusion': 'success',
          },
        ],
      };

  @override
  void close() {}
}

void main() {
  testWidgets('system monitor shows service health and workflow',
      (tester) async {
    tester.view.physicalSize = const Size(1200, 900);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: SystemMonitorPage(apiClient: FakeSystemMonitorApiClient()),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.text('ศูนย์ตรวจสอบระบบ'), findsOneWidget);
    expect(find.text('API'), findsOneWidget);
    expect(find.text('ok'), findsOneWidget);
    expect(find.text('Provider'), findsOneWidget);
    expect(find.text('gemini'), findsOneWidget);
    expect(find.text('Memory'), findsOneWidget);
    expect(find.text('ready'), findsOneWidget);
    expect(find.text('Response Time'), findsOneWidget);
    expect(find.text('Research OS Flutter'), findsOneWidget);
    expect(find.textContaining('ผลลัพธ์: success'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
