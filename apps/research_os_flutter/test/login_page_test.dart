import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/auth/login_page.dart';

void main() {
  testWidgets('login keeps providers inside the collapsed Login tab', (tester) async {
    final client = ResearchOSApiClient(
      baseUrl: 'http://research-os.test',
      client: MockClient((request) async {
        expect(request.url.path, '/v1/auth/providers');
        return http.Response(
          jsonEncode({
            'providers': [
              {'id': 'google', 'name': 'Google', 'available': true},
              {'id': 'microsoft', 'name': 'Microsoft', 'available': true},
              {'id': 'github', 'name': 'GitHub', 'available': true},
            ],
          }),
          200,
          headers: {'content-type': 'application/json'},
        );
      }),
    );

    addTearDown(client.close);

    await tester.pumpWidget(
      MaterialApp(
        home: LoginPage(
          apiClient: client,
          connectionProfile: 'research_os',
          onConnectionChanged: (_) async {},
          onAuthenticated: () {},
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Login'), findsOneWidget);
    expect(find.text('Continue with Google'), findsNothing);
    expect(find.text('Continue with Microsoft'), findsNothing);
    expect(find.text('Continue with GitHub'), findsNothing);
    expect(find.text('Research OS'), findsOneWidget);
    expect(find.text('Developer Runtime'), findsNothing);

    await tester.tap(find.text('Login'));
    await tester.pumpAndSettle();

    expect(find.text('Continue with Google'), findsOneWidget);
    expect(find.text('Continue with Microsoft'), findsOneWidget);
    expect(find.text('Continue with GitHub'), findsOneWidget);

    // Connection details are collapsed by default and expose names only.
    expect(find.text('Developer Runtime'), findsNothing);
    await tester.tap(find.text('Connection'));
    await tester.pumpAndSettle();
    expect(find.text('Developer Runtime'), findsOneWidget);
    expect(find.text('127.0.0.1:8787'), findsNothing);
    expect(find.text('127.0.0.1:8790'), findsNothing);
  });
}
