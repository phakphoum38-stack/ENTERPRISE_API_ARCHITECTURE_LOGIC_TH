import 'dart:async';

import 'api_endpoint_store.dart';
import 'research_os_api_client.dart';

Future<bool> probeLocalCompanionService({
  ResearchOSApiClient? client,
  int attempts = 20,
  Duration retryDelay = const Duration(milliseconds: 500),
}) async {
  final ownsClient = client == null;
  final probeClient = client ??
      ResearchOSApiClient(baseUrl: ApiEndpointStore.localDefault);

  try {
    for (var attempt = 0; attempt < attempts; attempt++) {
      try {
        final results = await Future.wait<Map<String, dynamic>>(
          <Future<Map<String, dynamic>>>[
            probeClient.getHealth(),
            probeClient.getProviders(),
          ],
        );
        if (results[0]['status']?.toString() == 'ok') {
          return true;
        }
      } on Object {
        // The local companion may still be starting. Retry without changing the
        // user-selected API endpoint; this probe is deliberately non-fatal.
      }
      if (attempt + 1 < attempts) {
        await Future<void>.delayed(retryDelay);
      }
    }
    return false;
  } finally {
    if (ownsClient) {
      probeClient.close();
    }
  }
}
