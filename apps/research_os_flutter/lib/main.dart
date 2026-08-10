import 'dart:async';

import 'package:flutter/material.dart';

import 'src/api/api_endpoint_store.dart';
import 'src/api/research_os_api_client.dart';
import 'src/research_os_app.dart';

void main() {
  // Warm the local-first service as soon as the installed Flutter binary starts.
  // This is intentionally best-effort and non-blocking: the UI still opens when
  // the service is unavailable, while Windows Candidate can prove that the
  // installed app itself reaches /health and /v1/providers.
  unawaited(_warmLocalService());
  runApp(const ResearchOSApp());
}

Future<void> _warmLocalService() async {
  final client = ResearchOSApiClient(baseUrl: ApiEndpointStore.localDefault);
  try {
    await Future.wait<Map<String, dynamic>>(<Future<Map<String, dynamic>>>[
      client.getHealth(),
      client.getProviders(),
    ]).timeout(const Duration(seconds: 3));
  } on Object {
    // Startup probing must never prevent the desktop app from opening.
  } finally {
    client.close();
  }
}
