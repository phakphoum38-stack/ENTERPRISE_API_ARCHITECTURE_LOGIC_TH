import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/ui/new_gui/registry_module_page.dart';

class RegistryApiClient extends ResearchOSApiClient {
  RegistryApiClient() : super(baseUrl: 'http://127.0.0.1:8787');

  @override
  Future<Map<String, dynamic>> getSkills() async => <String, dynamic>{
        'skills': <String>['analysis', 'planning', 'coding'],
        'count': 3,
        'source': 'owner-friend',
      };

  @override
  Future<Map<String, dynamic>> getTools() async => <String, dynamic>{
        'tools': <String>['echo', 'summarize'],
        'count': 2,
        'source': 'owner-friend',
      };

  @override
  void close() {}
}

void main() {
  testWidgets('Skills page renders Owner/Friend registry entries', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData.dark(useMaterial3: true),
        home: ResearchRegistryModulePage(
          apiClient: RegistryApiClient(),
          kind: ResearchRegistryKind.skills,
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Skills'), findsOneWidget);
    expect(find.text('analysis'), findsOneWidget);
    expect(find.text('planning'), findsOneWidget);
    expect(find.text('coding'), findsOneWidget);
    expect(find.text('owner-friend'), findsOneWidget);
    expect(find.text('Read only'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('Tools page renders Owner/Friend registry entries', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData.dark(useMaterial3: true),
        home: ResearchRegistryModulePage(
          apiClient: RegistryApiClient(),
          kind: ResearchRegistryKind.tools,
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Tools'), findsOneWidget);
    expect(find.text('echo'), findsOneWidget);
    expect(find.text('summarize'), findsOneWidget);
    expect(find.text('owner-friend'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
