import '../api/research_os_api_client.dart';
import '../contracts/research_os_capabilities.dart';

/// Adapter exposing the existing ResearchOSApiClient through stable
/// capability contracts. Transport and JSON details remain below this layer.
final class ResearchOSApiAdapter implements ResearchOSCapabilities {
  ResearchOSApiAdapter(this.client);

  final ResearchOSApiClient client;

  @override
  Future<Map<String, dynamic>> runtimeStatus() => client.getHealth();

  @override
  Future<Map<String, dynamic>> providers() => client.getProviders();

  @override
  Future<Map<String, dynamic>> providerStatus() =>
      client.getBrainProviders();

  @override
  Future<Map<String, dynamic>> identityStatus() =>
      client.getGoogleIdentityStatus();

  @override
  Future<Map<String, dynamic>> signIn() =>
      client.startGoogleIdentitySignIn();

  @override
  Future<Map<String, dynamic>> signOut() =>
      client.signOutGoogleIdentity();

  @override
  Future<Map<String, dynamic>> searchMemory(String query) =>
      client.searchMemory(query);

  @override
  Future<Map<String, dynamic>> commitMemory(
    String syncKey, {
    required String title,
    required List<Map<String, Object?>> conversation,
  }) =>
      client.commitMemory(
        syncKey,
        title: title,
        conversation: conversation,
      );

  @override
  Future<Map<String, dynamic>> knowledgeArtifacts() =>
      client.getKnowledgeArtifacts();

  @override
  Future<Map<String, dynamic>> knowledgeGraph() =>
      client.getKnowledgeGraph();

  @override
  Future<Map<String, dynamic>> agents() => client.getAgents();

  @override
  Future<Map<String, dynamic>> agentReadiness() =>
      client.getAgentReadiness();

  @override
  Future<Map<String, dynamic>> brainCapacity() =>
      client.getBrainCapacity();

  @override
  Future<Map<String, dynamic>> brainSkills() =>
      client.getBrainSkills();

  @override
  Future<Map<String, dynamic>> dashboard({String? repository}) =>
      client.getGitHubDashboard(repository: repository);

  @override
  Future<Map<String, dynamic>> listOrchestrations({
    String? status,
    String? query,
    String? agent,
    int? limit,
  }) =>
      client.getOrchestrations(
        status: status,
        query: query,
        agent: agent,
        limit: limit,
      );

  @override
  Future<Map<String, dynamic>> orchestration(String runId) =>
      client.getOrchestration(runId);

  @override
  Future<Map<String, dynamic>> createOrchestration({
    required String objective,
    required List<Map<String, Object?>> steps,
  }) =>
      client.createOrchestration(objective: objective, steps: steps);

  @override
  Future<Map<String, dynamic>> executeOrchestration(
    String runId, {
    bool confirmed = false,
  }) =>
      client.executeOrchestration(runId, confirmed: confirmed);
}
