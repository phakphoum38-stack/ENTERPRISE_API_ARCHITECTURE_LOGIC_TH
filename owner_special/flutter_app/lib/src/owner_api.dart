import 'dart:convert';
import 'dart:io';

abstract interface class OwnerFriendApi {
  Future<Map<String, dynamic>> health();
  Future<Map<String, dynamic>> status();
  Future<Map<String, dynamic>> memory();
  Future<Map<String, dynamic>> providerStatus();
  Future<Map<String, dynamic>> configureProvider({required String baseUrl, required String model, String? apiKey});
  Future<Map<String, dynamic>> testProvider();
  Future<Map<String, dynamic>> chat(String text, {int complexity = 4, int risk = 2, int parallelism = 2, int helperBudget = 0, List<String> requestedSkills = const <String>[], List<String> requestedTools = const <String>[]});
}

final class HttpOwnerFriendApi implements OwnerFriendApi {
  HttpOwnerFriendApi({required String baseUrl, required this.ownerId, this.profileId = 'default', this.sessionId = 'desktop', this.timeout = const Duration(seconds: 5)}) : baseUrl = baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl;
  final String baseUrl;
  final String ownerId;
  final String profileId;
  final String sessionId;
  final Duration timeout;

  @override
  Future<Map<String, dynamic>> health() => _request('GET', '/owner/health', authenticated: false);
  @override
  Future<Map<String, dynamic>> status() => _request('GET', '/owner/status');
  @override
  Future<Map<String, dynamic>> memory() => _request('GET', '/owner/memory');
  @override
  Future<Map<String, dynamic>> providerStatus() => _request('GET', '/owner/provider');
  @override
  Future<Map<String, dynamic>> configureProvider({required String baseUrl, required String model, String? apiKey}) => _request('POST', '/owner/provider/config', body: <String, dynamic>{'base_url': baseUrl, 'model': model, if (apiKey != null && apiKey.isNotEmpty) 'api_key': apiKey, 'enabled': true});
  @override
  Future<Map<String, dynamic>> testProvider() => _request('POST', '/owner/provider/test', body: const <String, dynamic>{'test': true});
  @override
  Future<Map<String, dynamic>> chat(String text, {int complexity = 4, int risk = 2, int parallelism = 2, int helperBudget = 0, List<String> requestedSkills = const <String>[], List<String> requestedTools = const <String>[]}) => _request('POST', '/owner/chat', body: <String, dynamic>{'text': text, 'complexity': complexity, 'risk': risk, 'parallelism': parallelism, 'helper_budget': helperBudget, 'requested_skills': requestedSkills, 'requested_tools': requestedTools});

  Future<Map<String, dynamic>> _request(String method, String path, {bool authenticated = true, Map<String, dynamic>? body}) async {
    final client = HttpClient();
    final uri = Uri.parse('$baseUrl$path');
    try {
      final request = method == 'POST' ? await client.postUrl(uri).timeout(timeout) : await client.getUrl(uri).timeout(timeout);
      request.headers.set(HttpHeaders.acceptHeader, 'application/json');
      if (authenticated) {
        request.headers.set('X-Research-OS-Owner', ownerId);
        request.headers.set('X-Research-OS-Profile', profileId);
        request.headers.set('X-Research-OS-Session', sessionId);
      }
      if (body != null) {
        final payload = utf8.encode(jsonEncode(body));
        request.headers.set(HttpHeaders.contentTypeHeader, 'application/json; charset=utf-8');
        request.contentLength = payload.length;
        request.add(payload);
      }
      final response = await request.close().timeout(timeout);
      final responseBody = await utf8.decoder.bind(response).join().timeout(timeout);
      final decoded = jsonDecode(responseBody);
      if (decoded is! Map) throw const FormatException('Owner Friend response must be a JSON object');
      final result = Map<String, dynamic>.from(decoded);
      if (response.statusCode != HttpStatus.ok) {
        final message = result['message']?.toString();
        final suffix = message == null || message.isEmpty ? '' : ': $message';
        throw HttpException('Owner Friend returned HTTP ${response.statusCode}: ${result['error']}$suffix', uri: uri);
      }
      return result;
    } finally {
      client.close(force: true);
    }
  }
}
