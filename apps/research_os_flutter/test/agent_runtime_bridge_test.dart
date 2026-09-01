import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/chat/agent_runtime_bridge.dart';

void main() {
  testWidgets('Agent Mesh runtime bridge renders plan and execute controls', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AgentRuntimeBridge(
            apiClient: ResearchOSApiClient(baseUrl: 'http://127.0.0.1:8787'),
          ),
        ),
      ),
    );

    expect(find.text('Agent Mesh Runtime'), findsOneWidget);
    expect(find.text('Plan with Agent Mesh'), findsOneWidget);
    expect(find.text('Explicit Execute'), findsOneWidget);
    expect(find.text('Plan first. Execute only through an explicit user action.'), findsOneWidget);
  });
}
