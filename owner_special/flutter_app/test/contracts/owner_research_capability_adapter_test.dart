import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_contracts/research_os_contracts.dart';

import 'package:research_os_owner_special/src/contracts/owner_research_capability_adapter.dart';
import 'package:research_os_owner_special/src/owner_api.dart';

final class _FakeOwnerApi implements OwnerFriendApi {
  final gets = <String>[];
  final posts = <String>[];

  @override
  Future<Map<String, dynamic>> health() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> status() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> memory() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> providerStatus() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> configureProvider({
    required String baseUrl,
    required String model,
    String? apiKey,
  }) async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> testProvider() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> chat(
    String text, {
    int complexity = 4,
    int risk = 2,
    int parallelism = 2,
    int helperBudget = 0,
    List<String> requestedSkills = const <String>[],
    List<String> requestedTools = const <String>[],
  }) async => <String, dynamic>{};

  @override
  Future<List<Map<String, dynamic>>> friendConnections() async => const <Map<String, dynamic>>[];

  @override
  Future<Map<String, dynamic>> saveFriendConnection(Map<String, dynamic> connection) async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> testFriendConnection(String id, {String? password}) async => <String, dynamic>{};

  @override
  void setFriendConnection(String id, {String? password}) {}

  @override
  Future<Map<String, dynamic>> authStatus() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> startGoogleIdentity() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> signOut() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> researchGet(
    String path, {
    Map<String, String>? query,
    Map<String, String>? headers,
  }) async {
    gets.add(query == null || query.isEmpty ? path : '$path?$query');
    return <String, dynamic>{'path': path};
  }

  @override
  Future<Map<String, dynamic>> researchPost(
    String path, {
    Map<String, dynamic>? body,
    Map<String, String>? headers,
  }) async {
    posts.add(path);
    return <String, dynamic>{'path': path};
  }


  @override
  Future<Map<String, dynamic>> exchangeGoogleIdentityHandoff(String state) async =>
      <String, dynamic>{'exchanged': false, 'state': state};

  @override
  void setSession(String token) {}

  @override
  void clearSession() {}
}

void main() {
  test('binds existing Research OS endpoints to shared capability contracts', () async {
    final api = _FakeOwnerApi();
    final adapter = OwnerResearchCapabilityAdapter(api);

    expect(adapter, isA<ResearchOSCapabilities>());

    await adapter.runtimeStatus();
    await adapter.providers();
    await adapter.providerStatus();
    await adapter.searchMemory('root');
    await adapter.knowledgeArtifacts();
    await adapter.knowledgeGraph();
    await adapter.agents();
    await adapter.agentReadiness();
    await adapter.brainCapacity();
    await adapter.brainSkills();
    await adapter.dashboard(repository: 'owner/repo');
    await adapter.listOrchestrations(limit: 5);
    await adapter.orchestration('run-1');
    await adapter.createOrchestration(
      objective: 'inspect',
      steps: const <Map<String, Object?>>[],
    );
    await adapter.executeOrchestration('run-1', confirmed: true);

    expect(api.gets, contains('/health'));
    expect(api.gets, contains('/v1/providers'));
    expect(api.gets, contains('/v1/brain/providers'));
    expect(api.gets, contains('/v1/knowledge/artifacts'));
    expect(api.gets, contains('/v1/knowledge/graph'));
    expect(api.gets, contains('/v1/agents'));
    expect(api.gets, contains('/v1/agents/readiness'));
    expect(api.gets, contains('/v1/brain/capacity'));
    expect(api.gets, contains('/v1/brain/skills'));
    expect(api.gets, contains('/v1/github/dashboard?{repository: owner/repo}'));
    expect(api.posts, contains('/v1/agents/orchestrations'));
    expect(api.posts, contains('/v1/agents/orchestrations/run-1/execute'));
  });
}
