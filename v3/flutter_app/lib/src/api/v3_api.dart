import 'dart:convert';
import 'dart:io';

abstract interface class V3Api {
  Future<Map<String, dynamic>> health();
  Future<Map<String, dynamic>> providers();
  Future<Map<String, dynamic>> master({int tasks = 1});
  Future<Map<String, dynamic>> user();
  Future<Map<String, dynamic>> chat(
    String message, {
    String sessionId = 'default',
    String provider = 'auto',
    String mode = 'answer',
  });
}

final class HttpV3Api implements V3Api {
  HttpV3Api({
    required String baseUrl,
    required this.userId,
    this.profileId = 'default',
    this.timeout = const Duration(seconds: 2),
    this.chatTimeout = const Duration(seconds: 45),
  }) : baseUrl = baseUrl.endsWith('/')
            ? baseUrl.substring(0, baseUrl.length - 1)
            : baseUrl;

  final String baseUrl;
  final String userId;
  final String profileId;
  final Duration timeout;
  final Duration chatTimeout;

  @override
  Future<Map<String, dynamic>> health() => _get('/health');

  @override
  Future<Map<String, dynamic>> providers() => _get('/v3/providers');

  @override
  Future<Map<String, dynamic>> master({int tasks = 1}) =>
      _get('/v3/master?tasks=$tasks');

  @override
  Future<Map<String, dynamic>> user() => _get('/v3/user');

  @override
  Future<Map<String, dynamic>> chat(
    String message, {
    String sessionId = 'default',
    String provider = 'auto',
    String mode = 'answer',
  }) {
    return _post(
      '/v3/chat',
      <String, Object?>{
        'message': message,
        'session_id': sessionId,
        'provider': provider,
        'mode': mode,
      },
      requestTimeout: chatTimeout,
    );
  }

  void _applyHeaders(HttpClientRequest request) {
    request.headers.set(HttpHeaders.acceptHeader, 'application/json');
    request.headers.set('X-Research-OS-User', userId);
    request.headers.set('X-Research-OS-Profile', profileId);
  }

  Future<Map<String, dynamic>> _get(String path) async {
    final client = HttpClient();
    final uri = Uri.parse('$baseUrl$path');
    try {
      final request = await client.getUrl(uri).timeout(timeout);
      _applyHeaders(request);
      final response = await request.close().timeout(timeout);
      final body = await utf8.decoder.bind(response).join().timeout(timeout);
      return _decode(uri, response.statusCode, body);
    } finally {
      client.close(force: true);
    }
  }

  Future<Map<String, dynamic>> _post(
    String path,
    Map<String, Object?> payload, {
    required Duration requestTimeout,
  }) async {
    final client = HttpClient();
    final uri = Uri.parse('$baseUrl$path');
    try {
      final request = await client.postUrl(uri).timeout(requestTimeout);
      _applyHeaders(request);
      request.headers.contentType = ContentType.json;
      request.write(jsonEncode(payload));
      final response = await request.close().timeout(requestTimeout);
      final body = await utf8.decoder
          .bind(response)
          .join()
          .timeout(requestTimeout);
      return _decode(uri, response.statusCode, body);
    } finally {
      client.close(force: true);
    }
  }

  Map<String, dynamic> _decode(Uri uri, int statusCode, String body) {
    final Object? decoded;
    try {
      decoded = jsonDecode(body);
    } on FormatException catch (error) {
      throw FormatException(
        'Research OS V3 returned invalid JSON (HTTP $statusCode): $error',
      );
    }
    if (decoded is! Map) {
      throw const FormatException(
        'Research OS V3 response must be a JSON object',
      );
    }
    final result = Map<String, dynamic>.from(decoded);
    if (statusCode < HttpStatus.ok || statusCode >= HttpStatus.multipleChoices) {
      final detail = result['detail'] ?? result['error'] ?? 'unknown error';
      throw HttpException(
        'Research OS V3 returned HTTP $statusCode: $detail',
        uri: uri,
      );
    }
    return result;
  }
}
