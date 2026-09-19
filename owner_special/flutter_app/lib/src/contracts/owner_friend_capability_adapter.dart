import '../owner_api.dart';
import 'research_os_capabilities.dart';

/// Owner Friend transport exposed through the canonical capability boundary.
final class OwnerFriendCapabilityAdapter {
  OwnerFriendCapabilityAdapter(this.api);

  final OwnerFriendApi api;

  Future<Map<String, dynamic>> runtimeStatus() => api.status();

  Future<Map<String, dynamic>> providerStatus() => api.providerStatus();

  Future<Map<String, dynamic>> memory() => api.memory();

  Future<Map<String, dynamic>> identityStatus() => api.authStatus();

  Future<Map<String, dynamic>> signIn() => api.startGoogleIdentity();

  Future<Map<String, dynamic>> signOut() => api.signOut();

  Future<Map<String, dynamic>> configureProvider(
    String provider,
    String apiKey,
  ) =>
      api.configureProvider(provider, apiKey);

  Future<Map<String, dynamic>> testProvider(String provider) =>
      api.testProvider(provider);

  Future<Map<String, dynamic>> chat({
    required String message,
    String complexity = 'standard',
    String risk = 'low',
    int parallelism = 1,
    int helperBudget = 0,
    List<String> requestedSkills = const [],
    List<String> tools = const [],
    String? session,
  }) =>
      api.chat(
        message: message,
        complexity: complexity,
        risk: risk,
        parallelism: parallelism,
        helperBudget: helperBudget,
        requestedSkills: requestedSkills,
        tools: tools,
        session: session,
      );
}
