import 'dart:convert';

import 'package:http/http.dart' as http;

class ResearchOSApiException implements Exception {
  const ResearchOSApiException(this.message);

  final String message;

  @override
  String toString() => message;
}

class ResearchOSApiClient {
  ResearchOSApiClient({required this.baseUrl, http.Client? client})
      : _client = client ?? http.Client();

  final String baseUrl;
  final http.Client _client;

  Uri _uri(String path) => Uri.parse('$baseUrl$path');

  Future<Map<String, dynamic>> getHealth() => _getJson('/health');
  Future<Map<String, dynamic>> getProviders() => _getJson('/v1/providers');
  Future<Map<String, dynamic>> getProviderGateway() =>
      _getJson('/v2/providers');

  Future<Map<String, dynamic>> getIntelligenceManifest() =>
      _getJson('/v2/intelligence');
  Future<Map<String, dynamic>> getIntelligenceHealth() =>
      _getJson('/v2/intelligence/health');
  Future<Map<String, dynamic>> getIntelligenceCapabilities() =>
      _getJson('/v2/intelligence/capabilities');
  Future<Map<String, dynamic>> getIntelligencePermissions() =>
      _getJson('/v2/intelligence/permissions');
  Future<Map<String, dynamic>> getIntelligenceArchitecture() =>
      _getJson('/v2/intelligence/architecture');
  Future<Map<String, dynamic>> getIntelligenceProjectState() =>
      _getJson('/v2/intelligence/project-state');

  Future<Map<String, dynamic>> getIntelligenceAgents({
    String scope = 'all',
    String? capability,
    String? permission,
    bool readyOnly = true,
  }) => _getIntelligenceCollection(
        '/v2/intelligence/agents',
        scope: scope,
        capability: capability,
        permission: permission,
        readyOnly: readyOnly,
      );

  Future<Map<String, dynamic>> getV2BrainAgents({bool readyOnly = true}) =>
      getIntelligenceAgents(scope: 'brain', readyOnly: readyOnly);

  // V2² is a compatibility-safe helper mode layered on the canonical V2 Brain
  // Team. Agent IDs remain v2_* so orchestration, permissions and persisted runs
  // do not fork into a second source of truth.
  Future<Map<String, dynamic>> getV2SquaredBrainAgents({
    bool readyOnly = true,
  }) =>
      getV2BrainAgents(readyOnly: readyOnly);

  Future<Map<String, dynamic>> getIntelligenceSkills({
    String? capability,
    String? permission,
    bool readyOnly = true,
  }) => _getIntelligenceCollection(
        '/v2/intelligence/skills',
        capability: capability,
        permission: permission,
        readyOnly: readyOnly,
      );

  Future<Map<String, dynamic>> getIntelligenceTools({
    String? capability,
    String? permission,
    bool readyOnly = true,
  }) => _getIntelligenceCollection(
        '/v2/intelligence/tools',
        capability: capability,
        permission: permission,
        readyOnly: readyOnly,
      );

  Future<Map<String, dynamic>> planIntelligence(
    String objective, {
    String? sessionId,
    Map<String, Object?> context = const <String, Object?>{},
  }) => _postJson('/v2/intelligence/plan', <String, Object?>{
        'objective': objective,
        if (sessionId != null && sessionId.trim().isNotEmpty)
          'session_id': sessionId.trim(),
        if (context.isNotEmpty) 'context': context,
      });

  Future<Map<String, dynamic>> _getIntelligenceCollection(
    String path, {
    String? scope,
    String? capability,
    String? permission,
    bool readyOnly = true,
  }) async {
    final params = <String, String>{
      'ready_only': readyOnly ? 'true' : 'false',
      if (scope != null && scope.trim().isNotEmpty) 'scope': scope.trim(),
      if (capability != null && capability.trim().isNotEmpty)
        'capability': capability.trim(),
      if (permission != null && permission.trim().isNotEmpty)
        'permission': permission.trim(),
    };
    final uri = _uri(path).replace(queryParameters: params);
    final response = await _client.get(uri);
    return _decode(response);
  }

  Future<Map<String, dynamic>> getKnowledgeArtifacts() =>
      _getJson('/v1/knowledge/artifacts');
  Future<Map<String, dynamic>> getKnowledgeGraph() =>
      _getJson('/v1/knowledge/graph');
  Future<Map<String, dynamic>> getGoogleWorkspaceDashboard() =>
      _getJson('/v1/google-workspace/dashboard');
  Future<Map<String, dynamic>> getGoogleWorkspaceOAuthStatus() =>
      _getJson('/v1/google-workspace/oauth/status');
  Future<Map<String, dynamic>> startGoogleWorkspaceOAuth() =>
      _postJson('/v1/google-workspace/oauth/start', const <String, Object?>{});
  Future<Map<String, dynamic>> disconnectGoogleWorkspace() =>
      _postJson('/v1/google-workspace/oauth/disconnect', const <String, Object?>{});
  Future<Map<String, dynamic>> setGoogleWorkspaceServices(List<String> services) =>
      _postJson('/v1/google-workspace/services', <String, Object?>{
        'enabled_services': services,
      });

  Future<Map<String, dynamic>> getAgents() => _getJson('/v1/agents');
  Future<Map<String, dynamic>> getAgentReadiness() =>
      _getJson('/v1/agents/readiness');

  Future<Map<String, dynamic>> discoverAgents({String? capability}) async {
    final value = capability?.trim();
    if (value == null || value.isEmpty) {
      return _getJson('/v1/agents/discover');
    }
    final uri = _uri('/v1/agents/discover').replace(
      queryParameters: <String, String>{'capability': value},
    );
    final response = await _client.get(uri);
    return _decode(response);
  }

  Future<Map<String, dynamic>> getV2Workspaces() =>
      _getJson('/v2/workspaces');

  Future<Map<String, dynamic>> searchWorkspaceKnowledge(
    String workspaceId, {
    String query = '',
    int pageSize = 25,
    String? cursor,
  }) async {
    final params = <String, String>{
      'q': query.trim(),
      'page_size': '$pageSize',
      if (cursor != null && cursor.trim().isNotEmpty) 'cursor': cursor.trim(),
    };
    final uri = _uri(
      '/v2/workspaces/${Uri.encodeComponent(workspaceId)}/knowledge',
    ).replace(queryParameters: params);
    final response = await _client.get(uri);
    return _decode(response);
  }

  Future<Map<String, dynamic>> getOrchestrations({
    String? status,
    String? query,
    String? agent,
    int? limit,
  }) async {
    final params = <String, String>{};
    if (status != null && status.trim().isNotEmpty) {
      params['status'] = status.trim();
    }
    if (query != null && query.trim().isNotEmpty) params['q'] = query.trim();
    if (agent != null && agent.trim().isNotEmpty) params['agent'] = agent.trim();
    if (limit != null) params['limit'] = '$limit';
    final uri = _uri('/v1/agents/orchestrations').replace(
      queryParameters: params.isEmpty ? null : params,
    );
    final response = await _client.get(uri);
    return _decode(response);
  }

  Future<Map<String, dynamic>> getOrchestration(String runId) =>
      _getJson('/v1/agents/orchestrations/${Uri.encodeComponent(runId)}');

  Future<Map<String, dynamic>> getOrchestrationTimeline(String runId) =>
      _getJson(
        '/v1/agents/orchestrations/${Uri.encodeComponent(runId)}/timeline',
      );

  Future<Map<String, dynamic>> createOrchestration({
    required String objective,
    required List<Map<String, Object?>> steps,
  }) =>
      _postJson('/v1/agents/orchestrations', <String, Object?>{
        'objective': objective,
        'steps': steps,
      });

  Future<Map<String, dynamic>> executeOrchestration(
    String runId, {
    bool confirmed = false,
  }) =>
      _postJson(
        '/v1/agents/orchestrations/${Uri.encodeComponent(runId)}/execute',
        <String, Object?>{'confirmed': confirmed},
      );

  Future<Map<String, dynamic>> confirmOrchestration(String runId) =>
      _postJson(
        '/v1/agents/orchestrations/${Uri.encodeComponent(runId)}/confirm',
        const <String, Object?>{},
      );

  Future<Map<String, dynamic>> retryOrchestration(
    String runId, {
    String? stepId,
  }) =>
      _postJson(
        '/v1/agents/orchestrations/${Uri.encodeComponent(runId)}/retry',
        <String, Object?>{
          if (stepId != null && stepId.trim().isNotEmpty)
            'step_id': stepId.trim(),
        },
      );

  Future<Map<String, dynamic>> cancelOrchestration(String runId) =>
      _postJson(
        '/v1/agents/orchestrations/${Uri.encodeComponent(runId)}/cancel',
        const <String, Object?>{},
      );

  Future<Map<String, dynamic>> getGitHubDashboard({String? repository}) async {
    final query = repository?.trim();
    if (query == null || query.isEmpty) {
      return _getJson('/v1/github/dashboard');
    }
    final uri = _uri('/v1/github/dashboard').replace(
      queryParameters: <String, String>{'repository': query},
    );
    final response = await _client.get(uri);
    return _decode(response);
  }

  Future<Map<String, dynamic>> searchMemory(String query) async {
    final uri = _uri('/v1/memory/search').replace(
      queryParameters: <String, String>{'q': query, 'limit': '5'},
    );
    final response = await _client.get(uri);
    return _decode(response);
  }

  Future<Map<String, dynamic>> generateText(String prompt) {
    return _postJson('/v1/ai/generate', <String, Object?>{
      'prompt': prompt,
    });
  }

  Future<Map<String, dynamic>> answerWithMemory(String question) {
    return _postJson('/v1/ai/answer-with-memory', <String, Object?>{
      'question': question,
    });
  }

  Future<Map<String, dynamic>> commitMemory(
    String syncKey, {
    required String title,
    required List<Map<String, Object?>> conversation,
  }) async {
    final response = await _client.post(
      _uri('/v1/memory/commit'),
      headers: <String, String>{
        'Content-Type': 'application/json',
        'X-Research-OS-Sync-Key': syncKey,
      },
      body: jsonEncode(<String, Object?>{
        'title': title,
        'conversation': conversation,
        'status': 'hypothesis',
        'tags': <String>['research-os', 'chat-session'],
        'min_quality': 20,
        'confirm': true,
      }),
    );
    return _decode(response);
  }

  Future<Map<String, dynamic>> getCloudConversations(String syncKey) async {
    final response = await _client.get(
      _uri('/v1/conversations/cloud'),
      headers: <String, String>{'X-Research-OS-Sync-Key': syncKey},
    );
    return _decode(response);
  }

  Future<Map<String, dynamic>> syncCloudConversation(
    String syncKey,
    Map<String, Object?> session,
  ) async {
    final response = await _client.post(
      _uri('/v1/conversations/cloud/sync'),
      headers: <String, String>{
        'Content-Type': 'application/json',
        'X-Research-OS-Sync-Key': syncKey,
      },
      body: jsonEncode(<String, Object?>{'session': session}),
    );
    return _decode(response);
  }

  Future<Map<String, dynamic>> deleteCloudConversation(
    String syncKey,
    String sessionId,
  ) async {
    final response = await _client.post(
      _uri('/v1/conversations/cloud/delete'),
      headers: <String, String>{
        'Content-Type': 'application/json',
        'X-Research-OS-Sync-Key': syncKey},
      body: jsonEncode(<String, Object?>{'session_id': sessionId}),
    );
    return _decode(response);
  }

  Future<Map<String, dynamic>> _getJson(String path) async {
    final response = await _client.get(_uri(path));
    return _decode(response);
  }

  Future<Map<String, dynamic>> _postJson(
    String path,
    Map<String, Object?> payload,
  ) async {
    final response = await _client.post(
      _uri(path),
      headers: const <String, String>{'Content-Type': 'application/json'},
      body: jsonEncode(payload),
    );
    return _decode(response);
  }

  Map<String, dynamic> _decode(http.Response response) {
    final Object? decoded;
    try {
      decoded = jsonDecode(response.body);
    } on FormatException {
      throw ResearchOSApiException(
        'Research OS API returned invalid JSON (${response.statusCode}).',
      );
    }
    if (decoded is! Map<String, dynamic>) {
      throw const ResearchOSApiException(
        'Research OS API returned an unexpected response shape.',
      );
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final rawError = decoded['error'];
      final detail = rawError is Map
          ? rawError['message'] ?? rawError['code'] ?? 'Unknown error'
          : decoded['detail'] ?? rawError ?? 'Unknown error';
      throw ResearchOSApiException(
        'Research OS API error ${response.statusCode}: $detail',
      );
    }
    return decoded;
  }

  void close() => _client.close();
}
