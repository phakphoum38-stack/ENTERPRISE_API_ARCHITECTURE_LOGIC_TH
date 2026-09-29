import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/auth/login_page.dart';

void main() {
  testWidgets(
      'shared auth port and user-level controls use the canonical UI contract',
      (tester) async {
    final client = ResearchOSApiClient(
      baseUrl: 'http://research-os.test',
      client: MockClient((request) async {
        if (request.url.path == '/v1/auth/providers') {
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
        }

        fail('Unexpected request: ${request.method} ${request.url}');
        return http.Response('{}', 500);
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

    // PORT is a user-facing label, not a raw endpoint.
    expect(find.text('PORT'), findsOneWidget);
    expect(find.text('PORT 1'), findsOneWidget);
    expect(find.text('127.0.0.1:8787'), findsNothing);
    expect(find.text('127.0.0.1:8790'), findsNothing);

    // LOGIN starts as an explicit selection.
    expect(find.text('LOGIN'), findsOneWidget);
    expect(find.text('Select Login Method'), findsOneWidget);

    // USER LEVEL starts as an explicit selection.
    expect(find.text('USER LEVEL'), findsOneWidget);
    expect(find.text('Select User Level'), findsOneWidget);

    // Provider choices are hidden until the LOGIN dropdown is opened.
    expect(find.text('Windows'), findsNothing);
    expect(find.text('GitHub'), findsNothing);
    expect(find.text('Google'), findsNothing);
    expect(find.text('None'), findsNothing);
    expect(find.text('Custom'), findsNothing);

    // Open LOGIN dropdown.
    await tester.tap(find.byKey(const ValueKey('login-method-dropdown')));
    await tester.pumpAndSettle();

    expect(find.text('Windows'), findsOneWidget);
    expect(find.text('GitHub'), findsOneWidget);
    expect(find.text('Google'), findsOneWidget);
    expect(find.text('None'), findsOneWidget);
    expect(find.text('Custom'), findsOneWidget);

    // Close the menu by selecting Google.
    await tester.tap(find.text('Google'));
    await tester.pumpAndSettle();

    expect(find.text('Google'), findsOneWidget);

    // Open USER LEVEL dropdown.
    await tester.tap(find.byKey(const ValueKey('login-user-level-dropdown')));
    await tester.pumpAndSettle();

    expect(find.text('Owner'), findsOneWidget);
    expect(find.text('Developer'), findsOneWidget);
    expect(find.text('General'), findsOneWidget);

    // Selecting a level is UI context only; authorization remains server-side.
    await tester.tap(find.text('Developer'));
    await tester.pumpAndSettle();

    expect(find.text('Developer'), findsOneWidget);

    // PORT dropdown exposes only PORT labels.
    await tester.tap(find.byKey(const ValueKey('login-port-dropdown')));
    await tester.pumpAndSettle();

    expect(find.text('PORT 1'), findsWidgets);
    expect(find.text('PORT 2'), findsOneWidget);
    expect(find.text('8787'), findsNothing);
    expect(find.text('8790'), findsNothing);
  });
}
