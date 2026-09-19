import 'package:research_os_contracts/research_os_contracts.dart';

import '../owner_api.dart';

/// Owner Friend transport exposed through stable shared capability contracts.
///
/// Provider and memory operations remain available through the concrete Owner
/// API until their transport semantics can satisfy shared contracts directly.
final class OwnerFriendCapabilityAdapter
    implements RuntimeStatusCapability, IdentityCapability {
  OwnerFriendCapabilityAdapter(this.api);

  final OwnerFriendApi api;

  @override
  Future<Map<String, dynamic>> runtimeStatus() => api.status();

  @override
  Future<Map<String, dynamic>> identityStatus() => api.authStatus();

  @override
  Future<Map<String, dynamic>> signIn() => api.startGoogleIdentity();

  @override
  Future<Map<String, dynamic>> signOut() => api.signOut();

  Future<Map<String, dynamic>> memorySnapshot() => api.memory();

  Future<Map<String, dynamic>> providerStatus() => api.providerStatus();

  Future<Map<String, dynamic>> configureProvider({
    required String baseUrl,
    required String model,
    String? apiKey,
  }) =>
      api.configureProvider(
        baseUrl: baseUrl,
        model: model,
        apiKey: apiKey,
      );

  Future<Map<String, dynamic>> testProvider() => api.testProvider();

  Future<Map<String, dynamic>> chat(
    String message, {
    int complexity = 4,
    int risk = 2,
    int parallelism = 2,
    int helperBudget = 0,
    List<String> requestedSkills = const <String>[],
    List<String> requestedTools = const <String>[],
  }) =>
      api.chat(
        message,
        complexity: complexity,
        risk: risk,
        parallelism: parallelism,
        helperBudget: helperBudget,
        requestedSkills: requestedSkills,
        requestedTools: requestedTools,
      );
}
