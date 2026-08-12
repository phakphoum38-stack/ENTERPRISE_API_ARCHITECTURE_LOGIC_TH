import 'api_endpoint_store.dart';
import 'research_os_api_client.dart';

Future<bool> probeLocalCompanionService({ResearchOSApiClient? client}) async {
  final ownsClient = client == null;
  final probeClient = client ??
      ResearchOSApiClient(baseUrl: ApiEndpointStore.localDefault);

  try {
    final results = await Future.wait<Map<String, dynamic>>(
      <Future<Map<String, dynamic>>>[
        probeClient.getHealth(),
        probeClient.getProviders(),
      ],
    );
    return results[0]['status']?.toString() == 'ok';
  } on Object {
    return false;
  } finally {
    if (ownsClient) {
      probeClient.close();
    }
  }
}
