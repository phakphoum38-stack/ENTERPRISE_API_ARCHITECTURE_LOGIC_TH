import 'package:research_os_contracts/research_os_contracts.dart';

import '../owner_api.dart';

/// Owner Friend transport exposed through stable shared capability contracts.
final class OwnerFriendCapabilityAdapter
    implements
        RuntimeStatusCapability,
        ProviderCapability,
        IdentityCapability,
        MemoryCapability {
  OwnerFriendCapabilityAdapter(this.api);

  final OwnerFriendApi api;

  @override
  Future<Map<String, dynamic>> runtimeStatus() => api.status();

  @override
  Future<Map<String, dynamic>> providers() => api.providerStatus();

  @override
  Future<Map<String, dynamic>> providerStatus() => api.providerStatus();

  @override
  Future<Map<String, dynamic>> memorySearch(String query) => api.memory();

  @override
  Future<Map<String, dynamic>> identityStatus() => api.authStatus();

  @override
  Future<Map<String, dynamic>> signIn() => api.startGoogleIdentity();

  @override
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
