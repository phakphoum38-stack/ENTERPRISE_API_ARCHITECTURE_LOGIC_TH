import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:research_os_flutter/src/api/local_companion_probe.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';

void main() {
  test('startup probe calls local health and providers endpoints', () async {
    final paths = <String>[];
    final httpClient = MockClient((request) async {
      paths.add(request.url.path);
      if (request.url.path == '/health') {
        return http.Response(jsonEncode(<String, Object?>{'status': 'ok'}), 200);
      }
      if (request.url.path == '/v1/providers') {
        return http.Response(
          jsonEncode(<String, Object?>{'active': 'mock'}),
          200,
        );
      }
      return http.Response('{}', 404);
    });
    final apiClient = ResearchOSApiClient(
      baseUrl: 'http://127.0.0.1:8787',
      client: httpClient,
    );

    final connected = await probeLocalCompanionService(client: apiClient);

    expect(connected, isTrue);
    expect(paths, contains('/health'));
    expect(paths, contains('/v1/providers'));
    apiClient.close();
  });

  test('startup probe is non-fatal when local service is unavailable', () async {
    final httpClient = MockClient((request) async {
      throw const http.ClientException('service unavailable');
    });
    final apiClient = ResearchOSApiClient(
      baseUrl: 'http://127.0.0.1:8787',
      client: httpClient,
    );

    final connected = await probeLocalCompanionService(client: apiClient);

    expect(connected, isFalse);
    apiClient.close();
  });
}
