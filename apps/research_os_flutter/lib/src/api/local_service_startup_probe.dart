import 'dart:async';

import 'api_endpoint_store.dart';
import 'research_os_api_client.dart';

/// Best-effort local-service startup probe for the installed desktop app.
///
/// The probe retries both required app-to-service requests instead of relying
/// on a single startup attempt. It never blocks app startup permanently and it
/// never exposes provider credentials.
class LocalServiceStartupProbe {
  LocalServiceStartupProbe._();

  static Future<bool> run({
    ResearchOSApiClient? client,
    int attempts = 30,
    Duration retryDelay = const Duration(milliseconds: 500),
    Duration requestTimeout = const Duration(seconds: 2),
  }) async {
    final ownedClient = client == null;
    final api = client ?? ResearchOSApiClient(baseUrl: ApiEndpointStore.localDefault);

    var healthConfirmed = false;
    var providersConfirmed = false;

    try {
      for (var attempt = 0; attempt < attempts; attempt++) {
        if (!healthConfirmed) {
          try {
            final health = await api.getHealth().timeout(requestTimeout);
            healthConfirmed = health['status'] == 'ok';
          } on Object {
            // Service may still be starting. Retry below.
          }
        }

        if (!providersConfirmed) {
          try {
            final providers = await api.getProviders().timeout(requestTimeout);
            providersConfirmed = providers['providers'] is List<dynamic>;
          } on Object {
            // Service may still be starting. Retry below.
          }
        }

        if (healthConfirmed && providersConfirmed) {
          return true;
        }

        if (attempt + 1 < attempts) {
          await Future<void>.delayed(retryDelay);
        }
      }

      return false;
    } finally {
      if (ownedClient) {
        api.close();
      }
    }
  }
}
