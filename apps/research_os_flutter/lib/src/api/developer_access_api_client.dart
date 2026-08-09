import 'dart:convert';

import 'package:http/http.dart' as http;

class DeveloperAccessApiException implements Exception {
  const DeveloperAccessApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

class DeveloperAccessApiClient {
  DeveloperAccessApiClient({String? baseUrl, http.Client? client})
      : baseUrl = baseUrl ??
            const String.fromEnvironment(
              'RESEARCH_OS_DEVELOPER_API_BASE_URL',
              defaultValue: 'http://127.0.0.1:8790',
            ),
        _client = client ?? http.Client();

  final String baseUrl;
  final http.Client _client;

  Uri _uri(String path) => Uri.parse('$baseUrl$path');

  Future<Map<String, dynamic>> getSession() => _get('/v2/developer/session');

  Future<Map<String, dynamic>> getOwnerRequests({String? status}) async {
    final uri = _uri('/v2/developer/access-requests').replace(
      queryParameters: <String, String>{
        'view': 'owner',
        if (status != null && status.trim().isNotEmpty) 'status': status.trim(),
      },
    );
    return _decode(await _client.get(uri));
  }

  Future<Map<String, dynamic>> approveRequest(
    String requestId, {
    required List<String> scopes,
    int? expiresInSeconds,
  }) =>
      _post(
        '/v2/developer/access-requests/${Uri.encodeComponent(requestId)}/approve',
        <String, Object?>{
          'scopes': scopes,
          if (expiresInSeconds != null) 'expires_in_seconds': expiresInSeconds,
        },
      );

  Future<Map<String, dynamic>> rejectRequest(
    String requestId, {
    String reason = '',
  }) =>
      _post(
        '/v2/developer/access-requests/${Uri.encodeComponent(requestId)}/reject',
        <String, Object?>{'reason': reason},
      );

  Future<Map<String, dynamic>> _get(String path) async {
    return _decode(await _client.get(_uri(path)));
  }

  Future<Map<String, dynamic>> _post(
    String path,
    Map<String, Object?> payload,
  ) async {
    return _decode(
      await _client.post(
        _uri(path),
        headers: const <String, String>{'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      ),
    );
  }

  Map<String, dynamic> _decode(http.Response response) {
    final Object? decoded;
    try {
      decoded = jsonDecode(response.body);
    } on FormatException {
      throw DeveloperAccessApiException(
        'Developer API returned invalid JSON (${response.statusCode}).',
        statusCode: response.statusCode,
      );
    }
    if (decoded is! Map<String, dynamic>) {
      throw DeveloperAccessApiException(
        'Developer API returned an unexpected response shape.',
        statusCode: response.statusCode,
      );
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final rawError = decoded['error'];
      final detail = rawError is Map
          ? rawError['message'] ?? rawError['code'] ?? 'Unknown error'
          : decoded['detail'] ?? rawError ?? 'Unknown error';
      throw DeveloperAccessApiException(
        'Developer API error ${response.statusCode}: $detail',
        statusCode: response.statusCode,
      );
    }
    return decoded;
  }

  void close() => _client.close();
}
