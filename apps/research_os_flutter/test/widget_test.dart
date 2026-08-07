import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/home/home_page.dart';

class FakeResearchOSApiClient extends ResearchOSApiClient {
  FakeResearchOSApiClient() : super(baseUrl: 'http://127.0.0.1:8787');

  @override
  Future<Map<String, dynamic>> getHealth() async => <String, dynamic>{
        'status': 'ok',
        'memory': true,
      };

  @override
  Future<Map<String, dynamic>> getProviders() async => <String, dynamic>{
        'active': 'gemini',
        'providers': <String>['mock', 'gemini'],
      };

  @override
  void close() {}
}

void main() {
  testWidgets('home dashboard shows Research OS status', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: HomePage(apiClient: FakeResearchOSApiClient()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('บ้านของเรา'), findsOneWidget);
    expect(find.text('ok'), findsOneWidget);
    expect(find.text('gemini'), findsOneWidget);
    expect(find.text('ready'), findsOneWidget);
  });
}
