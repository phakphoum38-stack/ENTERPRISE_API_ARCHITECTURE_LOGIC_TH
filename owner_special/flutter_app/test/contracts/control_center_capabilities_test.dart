import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_contracts/research_os_contracts.dart';

import 'package:research_os_owner_special/src/contracts/control_center_capabilities.dart';
import 'package:research_os_owner_special/src/contracts/owner_friend_capability_adapter.dart';
import 'package:research_os_owner_special/src/owner_api.dart';

final class _FakeOwnerApi implements OwnerFriendApi {
  @override
  Future<Map<String, dynamic>> health() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> status() async => <String, dynamic>{'status': 'ok'};

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
  }) async =>
      <String, dynamic>{};


  @override
  Future<Map<String, dynamic>> researchGet(
    String path, {
    Map<String, String>? query,
    Map<String, String>? headers,
  }) async =>
      <String, dynamic>{'path': path};

  @override
  Future<Map<String, dynamic>> researchPost(
    String path, {
    Map<String, dynamic>? body,
    Map<String, String>? headers,
  }) async =>
      <String, dynamic>{'path': path};

  @override
  void setSession(String token) {}

  @override
  void clearSession() {}

  @override
  Future<Map<String, dynamic>> authStatus() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> startGoogleIdentity() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> exchangeGoogleIdentityHandoff(String state) async =>
      <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> signOut() async => <String, dynamic>{};
}

final class _FakeResearch implements ResearchOSCapabilities {
  @override
  Future<Map<String, dynamic>> runtimeStatus() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> providers() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> providerStatus() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> identityStatus() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> signIn() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> signOut() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> searchMemory(String query) async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> commitMemory(
    String syncKey, {
    required String title,
    required List<Map<String, Object?>> conversation,
  }) async =>
      <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> knowledgeArtifacts() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> knowledgeGraph() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> agents() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> agentReadiness() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> brainCapacity() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> brainSkills() async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> dashboard({String? repository}) async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> listOrchestrations({
    String? status,
    String? query,
    String? agent,
    int? limit,
  }) async =>
      <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> orchestration(String runId) async => <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> createOrchestration({
    required String objective,
    required List<Map<String, Object?>> steps,
  }) async =>
      <String, dynamic>{};

  @override
  Future<Map<String, dynamic>> executeOrchestration(
    String runId, {
    bool confirmed = false,
  }) async =>
      <String, dynamic>{};
}

void main() {
  test('composes Owner, Research, and optional V3 capability planes', () {
    final owner = OwnerFriendCapabilityAdapter(_FakeOwnerApi());
    final composition = ControlCenterCapabilities(
      owner: owner,
      research: _FakeResearch(),
      v3: owner,
    );

    expect(composition.runtime, same(owner));
    expect(composition.identity, same(owner));
    expect(composition.memory, isA<MemoryCapability>());
    expect(composition.providers, isA<ProviderCapability>());
    expect(composition.github, isA<GitHubCapability>());
    expect(composition.orchestration, isA<OrchestrationCapability>());
    expect(
      composition.availableCapabilities,
      containsAll(<String>[
        'runtime',
        'identity',
        'memory',
        'provider',
        'research',
        'github',
        'orchestration',
        'v3-runtime',
      ]),
    );
  });

  test('does not invent unavailable subsystem capabilities', () {
    final composition = ControlCenterCapabilities(
      owner: OwnerFriendCapabilityAdapter(_FakeOwnerApi()),
    );

    expect(composition.availableCapabilities, <String>{'runtime', 'identity'});
    expect(composition.memory, isNull);
    expect(composition.github, isNull);
    expect(composition.orchestration, isNull);
  });
}
