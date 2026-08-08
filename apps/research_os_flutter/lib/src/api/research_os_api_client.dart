import 'dart:convert';

import 'package:http/http.dart' as http;

import 'provider_selection_store.dart';

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
  Future<Map<String, dynamic>> getKnowledgeArtifacts() =>
      _getJson('/v1/knowledge/artifacts');
  Future<Map<String, dynamic>> getKnowledgeGraph() =>
      _getJson('/v1/knowledge/graph');

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

  Future<Map<String, dynamic>> generateText(
    String prompt, {
    String? provider,
  }) {
    return _postJson('/v1/ai/generate', <String, Object?>{
      'provider': provider ?? selectedProviderState.value,
      'prompt': prompt,
    });
  }

  Future<Map<String, dynamic>> answerWithMemory(
    String question, {
    String? provider,
  }) {
    return _postJson('/v1/ai/answer-with-memory', <String, Object?>{
      'provider': provider ?? selectedProviderState.value,
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
        'X-Research-OS-Sync-Key': syncKey,
      },
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
      final detail = decoded['detail'] ?? decoded['error'] ?? 'Unknown error';
      throw ResearchOSApiException(
        'Research OS API error ${response.statusCode}: $detail',
      );
    }
    return decoded;
  }

  void close() => _client.close();
}
