import 'package:research_os_contracts/research_os_contracts.dart';

import '../owner_api.dart';

/// Binds the canonical Research OS API surface to the shared capability
/// contracts using the existing Owner Friend transport boundary.
///
/// This is an adapter only: execution remains owned by the Research OS
/// endpoints and their existing authority/evidence layers.
final class OwnerResearchCapabilityAdapter implements ResearchOSCapabilities {
  OwnerResearchCapabilityAdapter(this.api);

  final OwnerFriendApi api;

  @override
  Future<Map<String, dynamic>> runtimeStatus() => api.researchGet('/health');

  @override
  Future<Map<String, dynamic>> providers() => api.researchGet('/v1/providers');

  @override
  Future<Map<String, dynamic>> providerStatus() =>
      api.researchGet('/v1/brain/providers');

  @override
  Future<Map<String, dynamic>> identityStatus() => api.authStatus();

  @override
  Future<Map<String, dynamic>> signIn() => api.startGoogleIdentity();

  @override
  Future<Map<String, dynamic>> signOut() => api.signOut();

  @override
  Future<Map<String, dynamic>> searchMemory(String query) =>
      api.researchGet('/v1/memory/search', query: <String, String>{'q': query, 'limit': '5'});

  @override
  Future<Map<String, dynamic>> commitMemory(
    String syncKey, {
    required String title,
    required List<Map<String, Object?>> conversation,
  }) =>
      api.researchPost(
        '/v1/memory/commit',
        headers: <String, String>{'X-Research-OS-Sync-Key': syncKey},
        body: <String, dynamic>{
          'title': title,
          'conversation': conversation,
          'status': 'hypothesis',
          'tags': <String>['research-os', 'chat-session'],
          'min_quality': 20,
          'confirm': true,
        },
      );

  @override
  Future<Map<String, dynamic>> knowledgeArtifacts() =>
      api.researchGet('/v1/knowledge/artifacts');

  @override
  Future<Map<String, dynamic>> knowledgeGraph() =>
      api.researchGet('/v1/knowledge/graph');

  @override
  Future<Map<String, dynamic>> agents() => api.researchGet('/v1/agents');

  @override
  Future<Map<String, dynamic>> agentReadiness() =>
      api.researchGet('/v1/agents/readiness');

  @override
  Future<Map<String, dynamic>> brainCapacity() =>
      api.researchGet('/v1/brain/capacity');

  @override
  Future<Map<String, dynamic>> brainSkills() =>
      api.researchGet('/v1/brain/skills');

  @override
  Future<Map<String, dynamic>> dashboard({String? repository}) {
    final value = repository?.trim();
    return api.researchGet(
      '/v1/github/dashboard',
      query: value == null || value.isEmpty
          ? null
          : <String, String>{'repository': value},
    );
  }

  @override
  Future<Map<String, dynamic>> listOrchestrations({
    String? status,
    String? query,
    String? agent,
    int? limit,
  }) =>
      api.researchGet(
        '/v1/agents/orchestrations',
        query: <String, String>{
          if (status != null && status.trim().isNotEmpty) 'status': status.trim(),
          if (query != null && query.trim().isNotEmpty) 'q': query.trim(),
          if (agent != null && agent.trim().isNotEmpty) 'agent': agent.trim(),
          if (limit != null) 'limit': '$limit',
        },
      );

  @override
  Future<Map<String, dynamic>> orchestration(String runId) =>
      api.researchGet('/v1/agents/orchestrations/${Uri.encodeComponent(runId)}');

  @override
  Future<Map<String, dynamic>> createOrchestration({
    required String objective,
    required List<Map<String, Object?>> steps,
  }) =>
      api.researchPost(
        '/v1/agents/orchestrations',
        body: <String, dynamic>{'objective': objective, 'steps': steps},
      );

  @override
  Future<Map<String, dynamic>> executeOrchestration(
    String runId, {
    bool confirmed = false,
  }) =>
      api.researchPost(
        '/v1/agents/orchestrations/${Uri.encodeComponent(runId)}/execute',
        body: <String, dynamic>{'confirmed': confirmed},
      );
}