import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:research_os_flutter/src/api/local_service_startup_probe.dart';
import 'package:research_os_flutter/src/api/research_os_api_client.dart';

void main() {
  test('app probe proves health and providers before assembly', () async {
    final paths = <String>[];
    final api = ResearchOSApiClient(
      baseUrl: 'http://127.0.0.1:8787',
      client: MockClient((request) async {
        paths.add(request.url.path);
        switch (request.url.path) {
          case '/health':
            return http.Response(
              jsonEncode(<String, Object?>{'status': 'ok'}),
              200,
            );
          case '/v1/providers':
            return http.Response(
              jsonEncode(<String, Object?>{'providers': <Object?>[]}),
              200,
            );
          default:
            return http.Response('not found', 404);
        }
      }),
    );

    try {
      final proved = await LocalServiceStartupProbe.run(
        client: api,
        attempts: 1,
        retryDelay: Duration.zero,
        requestTimeout: const Duration(seconds: 1),
      );

      expect(proved, isTrue);
      expect(paths, <String>['/health', '/v1/providers']);
    } finally {
      api.close();
    }
  });

  test('app probe retries only the service part that is not ready', () async {
    var healthCalls = 0;
    var providerCalls = 0;
    final api = ResearchOSApiClient(
      baseUrl: 'http://127.0.0.1:8787',
      client: MockClient((request) async {
        if (request.url.path == '/health') {
          healthCalls += 1;
          return http.Response(
            jsonEncode(<String, Object?>{'status': 'ok'}),
            200,
          );
        }
        if (request.url.path == '/v1/providers') {
          providerCalls += 1;
          if (providerCalls == 1) {
            return http.Response('starting', 503);
          }
          return http.Response(
            jsonEncode(<String, Object?>{'providers': <Object?>[]}),
            200,
          );
        }
        return http.Response('not found', 404);
      }),
    );

    try {
      final proved = await LocalServiceStartupProbe.run(
        client: api,
        attempts: 2,
        retryDelay: Duration.zero,
        requestTimeout: const Duration(seconds: 1),
      );

      expect(proved, isTrue);
      expect(healthCalls, 1);
      expect(providerCalls, 2);
    } finally {
      api.close();
    }
  });
}
