import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/brain_skills/brain_skills_page.dart';

class _BrainTestClient extends ResearchOSApiClient {
  _BrainTestClient()
      : super(
          baseUrl: 'http://127.0.0.1:8787',
        );

  @override
  Future<Map<String, dynamic>> getBrainCapacity() async =>
      <String, dynamic>{'capacity': 36};

  @override
  Future<Map<String, dynamic>> getBrainSkills() async =>
      <String, dynamic>{'skills': <String>['analysis', 'chat', 'research']};

  @override
  Future<Map<String, dynamic>> getBrainProviders() async =>
      <String, dynamic>{'providers': <String>['local', 'cloud']};
}

void main() {
  testWidgets('Brain Skills page loads all three API contracts', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: BrainSkillsPage(apiClient: _BrainTestClient()),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('Brain Skills'), findsOneWidget);
    expect(find.text('36'), findsOneWidget);
    expect(find.text('3'), findsOneWidget);
    expect(find.text('2'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
