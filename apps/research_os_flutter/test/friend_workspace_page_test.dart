import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/chat/friend_workspace_page.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() {
    SharedPreferences.setMockInitialValues(<String, Object>{});
  });

  testWidgets('wide layout exposes the Friend Workspace context inspector', (tester) async {
    tester.view.physicalSize = const Size(1440, 1000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: FriendWorkspacePage(
          apiClient: ResearchOSApiClient(baseUrl: 'http://127.0.0.1:8787'),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Context Inspector'), findsOneWidget);
    expect(find.text('Current intent'), findsOneWidget);
    expect(find.text('Agent Mesh'), findsOneWidget);
    expect(find.text('Permission boundary'), findsOneWidget);
    expect(find.text('6^6 ORCHESTRATOR'), findsOneWidget);
    expect(find.text('Runtime capacity not loaded'), findsOneWidget);
  });
}
