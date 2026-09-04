import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import '../lib/src/api/research_os_api_client.dart';
import '../lib/src/features/api_live/api_live_demo_page.dart';

class _ApiSpyClient extends http.BaseClient {
  String? method;
  Uri? uri;
  String? body;
  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    method = request.method;
    uri = request.url;
    body = request is http.Request ? request.body : null;
    final payload = request.url.path == '/health'
        ? <String, Object?>{'status': 'ok', 'service': 'research-os-api'}
        : <String, Object?>{'text': 'Flutter connected to API Platform'};
    return http.StreamedResponse(Stream<List<int>>.value(utf8.encode(jsonEncode(payload))), 200, request: request, headers: const {'content-type': 'application/json'});
  }
}

void main() {
  testWidgets('GET health sends a real client request', (tester) async {
    final transport = _ApiSpyClient();
    final api = ResearchOSApiClient(baseUrl: 'http://127.0.0.1:8787', client: transport);
    await tester.pumpWidget(MaterialApp(home: ApiLiveDemoPage(apiClient: api)));
    await tester.tap(find.text('GET /health'));
    await tester.pumpAndSettle();
    expect(transport.method, 'GET');
    expect(transport.uri?.toString(), 'http://127.0.0.1:8787/health');
    expect(find.textContaining('STATUS: 200'), findsOneWidget);
    expect(find.textContaining('service: research-os-api'), findsOneWidget);
  });

  testWidgets('AI button sends POST to the API Platform route', (tester) async {
    final transport = _ApiSpyClient();
    final api = ResearchOSApiClient(baseUrl: 'http://127.0.0.1:8787', client: transport);
    await tester.pumpWidget(MaterialApp(home: ApiLiveDemoPage(apiClient: api)));
    await tester.tap(find.text('POST /v1/ai/generate'));
    await tester.pumpAndSettle();
    expect(transport.method, 'POST');
    expect(transport.uri?.toString(), 'http://127.0.0.1:8787/v1/ai/generate');
    expect(transport.body, contains('Flutter'));
    expect(find.textContaining('STATUS: 200'), findsOneWidget);
  });
}
