import 'package:flutter_test/flutter_test.dart';

import 'package:research_os_flutter/src/contracts/research_os_capabilities.dart';

final class _FakeCapabilities implements ResearchOSCapabilities {
  @override
  Future<Map<String, dynamic>> runtimeStatus() async =>
      {'status': 'ok', 'version': 'test'};

  @override
  Future<Map<String, dynamic>> providers() async =>
      {'providers': <Map<String, dynamic>>[]};

  @override
  Future<Map<String, dynamic>> providerStatus() async =>
      {'status': 'ok'};

  @override
  Future<Map<String, dynamic>> identityStatus() async =>
      {'authenticated': false};

  @override
  Future<Map<String, dynamic>> signIn() async =>
      {'status': 'started'};

  @override
  Future<Map<String, dynamic>> signOut() async =>
      {'status': 'signed_out'};

  @override
  Future<Map<String, dynamic>> searchMemory(String query) async =>
      {'query': query, 'hits': <dynamic>[]};

  @override
  Future<Map<String, dynamic>> commitMemory(
    String syncKey, {
    required String title,
    required List<Map<String, Object?>> conversation,
  }) async =>
      {'status': 'ok'};

  @override
  Future<Map<String, dynamic>> knowledgeArtifacts() async =>
      {'artifacts': <dynamic>[]};

  @override
  Future<Map<String, dynamic>> knowledgeGraph() async =>
      {'nodes': <dynamic>[], 'edges': <dynamic>[]};

  @override
  Future<Map<String, dynamic>> agents() async =>
      {'agents': <dynamic>[]};

  @override
  Future<Map<String, dynamic>> agentReadiness() async =>
      {'ready': true};

  @override
  Future<Map<String, dynamic>> brainCapacity() async =>
      {'capacity': 0};

  @override
  Future<Map<String, dynamic>> brainSkills() async =>
      {'skills': <dynamic>[]};

  @override
  Future<Map<String, dynamic>> dashboard({String? repository}) async =>
      {'repository': repository};

  @override
  Future<Map<String, dynamic>> listOrchestrations({
    String? status,
    String? query,
    String? agent,
    int? limit,
  }) async =>
      {'runs': <dynamic>[]};

  @override
  Future<Map<String, dynamic>> orchestration(String runId) async =>
      {'run_id': runId};

  @override
  Future<Map<String, dynamic>> createOrchestration({
    required String objective,
    required List<Map<String, Object?>> steps,
  }) async =>
      {'objective': objective, 'steps': steps};

  @override
  Future<Map<String, dynamic>> executeOrchestration(
    String runId, {
    bool confirmed = false,
  }) async =>
      {'run_id': runId, 'confirmed': confirmed};
}

void main() {
  test('canonical capability contract is implementable without transport', () async {
    final capabilities = _FakeCapabilities();

    expect((await capabilities.runtimeStatus())['status'], 'ok');
    expect((await capabilities.identityStatus())['authenticated'], false);
    expect((await capabilities.searchMemory('hello'))['query'], 'hello');
    expect((await capabilities.orchestration('run-1'))['run_id'], 'run-1');
  });
}
