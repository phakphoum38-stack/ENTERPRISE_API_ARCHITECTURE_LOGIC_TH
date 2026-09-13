import 'dart:convert';

import 'package:http/http.dart' as http;

class ResearchOSApiException implements Exception {
  const ResearchOSApiException(this.message);

  final String message;

  @override
  String toString() => message;
}

class ResearchOSApiClient {
  ResearchOSApiClient({
    required this.baseUrl,
    http.Client? client,
    this.preferredProvider,
  }) : _client = client ?? http.Client();

  final String baseUrl;
  final String? preferredProvider;
  final http.Client _client;

  Uri _uri(String path) => Uri.parse('$baseUrl$path');

  Future<Map<String, dynamic>> getHealth() => _getJson('/health');
  Future<Map<String, dynamic>> getProviders() => _getJson('/v1/providers');
  Future<Map<String, dynamic>> getKnowledgeArtifacts() =>
      _getJson('/v1/knowledge/artifacts');
  Future<Map<String, dynamic>> getKnowledgeGraph() =>
      _getJson('/v1/knowledge/graph');

  Future<Map<String, dynamic>> getBrainCapacity() =>
      _getJson('/v1/brain/capacity');
  Future<Map<String, dynamic>> getBrainSkills() =>
      _getJson('/v1/brain/skills');
  Future<Map<String, dynamic>> getBrainProviders() =>
      _getJson('/v1/brain/providers');

  Future<Map<String, dynamic>> _getJson(String path) async {
    final response = await _client.get(_uri(path));
    return _decode(response);
  }

  Map<String, dynamic> _decode(http.Response response) {
    final dynamic decoded = jsonDecode(response.body);
    if (decoded is! Map<String, dynamic>) {
      throw const ResearchOSApiException('Research OS API returned a non-object response.');
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ResearchOSApiException(
        decoded['detail']?.toString() ??
            decoded['error']?.toString() ??
            'Research OS API request failed with HTTP ${response.statusCode}.',
      );
    }
    return decoded;
  }

  Future<Map<String, dynamic>> searchMemory(String query) async {
    final uri = _uri('/v1/memory/search').replace(
      queryParameters: <String, String>{'q': query, 'limit': '5'},
    );
    final response = await _client.get(uri);
    return _decode(response);
  }

  Future<Map<String, dynamic>> getCopilotContext({
    String? query,
    List<String> paths = const <String>[],
    int memoryLimit = 5,
  }) async {
    final queryParts = <String>[
      if (query != null && query.trim().isNotEmpty)
        'query=${Uri.encodeQueryComponent(query.trim())}',
      for (final path in paths) 'path=${Uri.encodeQueryComponent(path)}',
      'memory_limit=${Uri.encodeQueryComponent('$memoryLimit')}',
    ];
    final uri = _uri('/v1/copilot/context?${queryParts.join('&')}');
    final response = await _client.get(uri);
    return _decode(response);
  }

  Future<Map<String, dynamic>> chatWithCopilot({
    required String message,
    List<String> paths = const <String>[],
    String? contextQuery,
    int memoryLimit = 5,
  }) async {
    final response = await _client.post(
      _uri('/v1/copilot/chat'),
      headers: const <String, String>{'Content-Type': 'application/json'},
      body: jsonEncode(<String, dynamic>{
        'message': message,
        'paths': paths,
        'context_query': contextQuery,
        'memory_limit': memoryLimit,
      }),
    );
    return _decode(response);
  }
}
