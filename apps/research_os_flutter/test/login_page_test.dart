import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:research_os_flutter/src/api/research_os_api_client.dart';
import 'package:research_os_flutter/src/features/auth/login_page.dart';

void main() {
  testWidgets('shared auth surface uses QR pairing instead of login choices', (tester) async {
    var authenticated = 0;
    final client = ResearchOSApiClient(
      baseUrl: 'http://research-os.test',
      client: MockClient((request) async {
        switch (request.url.path) {
          case '/v1/auth/pairing/start':
            return http.Response(
              jsonEncode({
                'pairing_id': 'pair-123',
                'pairing_secret': 'secret-123',
                'expires_at': 9999999999,
                'status': 'PENDING',
                'qr_payload': 'https://research-os.test/v1/auth/pairing/open?pairing_id=pair-123&secret=secret-123',
              }),
              201,
              headers: {'content-type': 'application/json'},
            );
          case '/v1/auth/pairing/status':
            return http.Response(
              jsonEncode({
                'pairing_id': 'pair-123',
                'status': 'CONNECTED',
                'expires_at': 9999999999,
                'connected': true,
                'handoff_ready': true,
                'account': {'user_id': 'github:123', 'email': 'owner@example.com', 'role': 'owner'},
              }),
              200,
              headers: {'content-type': 'application/json'},
            );
          case '/v1/auth/providers/handoff':
            expect(request.headers['x-research-os-oauth-state'], 'secret-123');
            return http.Response(
              jsonEncode({'connected': true, 'session': 'session-token'}),
              200,
              headers: {'content-type': 'application/json'},
            );
          default:
            fail('Unexpected request: ${request.method} ${request.url}');
        }
      }),
    );
    addTearDown(client.close);
    await tester.pumpWidget(
      MaterialApp(
        home: LoginPage(
          apiClient: client,
          connectionProfile: 'research_os',
          onConnectionChanged: (_) async {},
          onAuthenticated: () => authenticated++,
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Research OS'), findsOneWidget);
    expect(find.text('Scan to Connect'), findsOneWidget);
    expect(find.text('PORT'), findsOneWidget);
    expect(find.text('PORT 1'), findsOneWidget);
    expect(find.byKey(const ValueKey('refresh-qr-button')), findsOneWidget);
    expect(find.text('LOGIN'), findsNothing);
    expect(find.text('Select Login Method'), findsNothing);
    expect(find.text('USER LEVEL'), findsNothing);
    expect(find.text('Windows'), findsNothing);
    expect(find.text('GitHub'), findsNothing);
    expect(find.text('Google'), findsNothing);
    expect(find.text('None'), findsNothing);
    expect(find.text('Custom'), findsNothing);
    expect(authenticated, 1);
  });
}
