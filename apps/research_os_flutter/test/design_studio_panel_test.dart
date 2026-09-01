import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/chat/design_studio_panel.dart';

void main() {
  testWidgets('Design Studio renders runtime evidence surface', (tester) async {
    await tester.pumpWidget(MaterialApp(
      home: DesignStudioPanel(
        apiClient: ResearchOSApiClient(baseUrl: 'http://127.0.0.1:8787'),
      ),
    ));
    expect(find.text('Design Studio'), findsOneWidget);
    expect(find.text('Registry & Policy'), findsOneWidget);
    expect(find.text('Evidence'), findsOneWidget);
    expect(find.text('Permission boundary'), findsOneWidget);
  });
}
