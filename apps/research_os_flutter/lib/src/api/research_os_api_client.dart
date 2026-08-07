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
  }) : _client = client ?? http.Client();

  final String baseUrl;
  final http.Client _client;

  Uri _uri(String path) => Uri.parse('$baseUrl$path');

  Future<Map<String, dynamic>> getHealth() async {
    return _getJson('/health');
  }

  Future<Map<String, dynamic>> getProviders() async {
    return _getJson('/v1/providers');
  }

  Future<Map<String, dynamic>> getKnowledgeArtifacts() async {
    return _getJson('/v1/knowledge/artifacts');
  }

  Future<Map<String, dynamic>> searchMemory(String query) async {
    final uri = _uri('/v1/memory/search').replace(
      queryParameters: <String, String>{'q': query, 'limit': '10'},
    );
    final response = await _client.get(uri);
    return _decode(response);
  }

  Future<Map<String, dynamic>> answerWithMemory(String question) async {
    final response = await _client.post(
      _uri('/v1/ai/answer-with-memory'),
      headers: const <String, String>{'Content-Type': 'application/json'},
      body: jsonEncode(<String, Object?>{
        'provider': 'gemini',
        'question': question,
      }),
    );
    return _decode(response);
  }

  Future<Map<String, dynamic>> _getJson(String path) async {
    final response = await _client.get(_uri(path));
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
