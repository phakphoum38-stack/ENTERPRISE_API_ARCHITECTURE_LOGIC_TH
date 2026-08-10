import 'dart:convert';
import 'dart:io';

abstract interface class V3Api {
  Future<Map<String, dynamic>> health();
  Future<Map<String, dynamic>> providers();
  Future<Map<String, dynamic>> master({int tasks = 1});
}

final class HttpV3Api implements V3Api {
  HttpV3Api({
    required String baseUrl,
    this.timeout = const Duration(seconds: 2),
  }) : baseUrl = baseUrl.endsWith('/')
            ? baseUrl.substring(0, baseUrl.length - 1)
            : baseUrl;

  final String baseUrl;
  final Duration timeout;

  @override
  Future<Map<String, dynamic>> health() => _get('/health');

  @override
  Future<Map<String, dynamic>> providers() => _get('/v3/providers');

  @override
  Future<Map<String, dynamic>> master({int tasks = 1}) =>
      _get('/v3/master?tasks=$tasks');

  Future<Map<String, dynamic>> _get(String path) async {
    final client = HttpClient();
    final uri = Uri.parse('$baseUrl$path');
    try {
      final request = await client.getUrl(uri).timeout(timeout);
      request.headers.set(HttpHeaders.acceptHeader, 'application/json');
      final response = await request.close().timeout(timeout);
      final body = await utf8.decoder.bind(response).join().timeout(timeout);
      if (response.statusCode != HttpStatus.ok) {
        throw HttpException(
          'Research OS V3 returned HTTP ${response.statusCode}',
          uri: uri,
        );
      }
      final decoded = jsonDecode(body);
      if (decoded is! Map) {
        throw const FormatException(
          'Research OS V3 response must be a JSON object',
        );
      }
      return Map<String, dynamic>.from(decoded);
    } finally {
      client.close(force: true);
    }
  }
}
