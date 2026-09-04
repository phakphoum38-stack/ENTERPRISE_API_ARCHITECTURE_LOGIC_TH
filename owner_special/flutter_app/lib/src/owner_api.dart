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

  Future<Map<String, dynamic>> authStatus() => Future<Map<String, dynamic>>.error(UnsupportedError('Research OS identity is not implemented by this API client'));
  Future<Map<String, dynamic>> startGoogleIdentity() => Future<Map<String, dynamic>>.error(UnsupportedError('Google Identity is not implemented by this API client'));
  Future<Map<String, dynamic>> exchangeGoogleIdentityHandoff(String state) => Future<Map<String, dynamic>>.error(UnsupportedError('Google Identity handoff is not implemented by this API client'));
  Future<Map<String, dynamic>> signOut() => Future<Map<String, dynamic>>.error(UnsupportedError('Research OS sign-out is not implemented by this API client'));
  void setSession(String token) {}
  void clearSession() {}
}

String _normalizeBaseUrl(String value) => value.endsWith('/') ? value.substring(0, value.length - 1) : value;

final class HttpOwnerFriendApi implements OwnerFriendApi {
  HttpOwnerFriendApi({required String baseUrl, required this.ownerId, this.profileId = 'default', this.sessionId = 'desktop', String researchOsBaseUrl = 'http://127.0.0.1:8787', this.timeout = const Duration(seconds: 5), this.chatTimeout = const Duration(seconds: 30)})
      : baseUrl = _normalizeBaseUrl(baseUrl),
        researchOsBaseUrl = _normalizeBaseUrl(researchOsBaseUrl);
  final String baseUrl;
  final String ownerId;
  final String profileId;
  final String sessionId;
  final String researchOsBaseUrl;
  final Duration timeout;
  final Duration chatTimeout;
  String? _sessionToken;

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
  Future<Map<String, dynamic>> chat(String text, {int complexity = 4, int risk = 2, int parallelism = 2, int helperBudget = 0, List<String> requestedSkills = const <String>[], List<String> requestedTools = const <String>[]}) => _request('POST', '/owner/chat', timeoutOverride: chatTimeout, body: <String, dynamic>{'text': text, 'complexity': complexity, 'risk': risk, 'parallelism': parallelism, 'helper_budget': helperBudget, 'requested_skills': requestedSkills, 'requested_tools': requestedTools});

  @override
  Future<Map<String, dynamic>> authStatus() => _researchRequest('GET', '/v1/auth/status', authenticated: _sessionToken != null);

  @override
  Future<Map<String, dynamic>> startGoogleIdentity() => _researchRequest('POST', '/v1/auth/google/start', authenticated: false);

  @override
  Future<Map<String, dynamic>> exchangeGoogleIdentityHandoff(String state) => _researchRequest('POST', '/v1/auth/google/handoff', authenticated: false, headers: <String, String>{'X-Research-OS-OAuth-State': state});

  @override
  Future<Map<String, dynamic>> signOut() => _researchRequest('POST', '/v1/auth/signout', authenticated: _sessionToken != null);

  @override
  void setSession(String token) {
    final value = token.trim();
    _sessionToken = value.isEmpty ? null : value;
  }

  @override
  void clearSession() => _sessionToken = null;

  Stream<Map<String, dynamic>> launchDesk(String text) async* {
    final client = HttpClient();
    final uri = Uri.parse('$baseUrl/v1/launch-desk/run');
    try {
      final request = await client.postUrl(uri).timeout(chatTimeout);
      request.headers.set(HttpHeaders.acceptHeader, 'text/event-stream');
      request.headers.set(HttpHeaders.contentTypeHeader, 'application/json; charset=utf-8');
      request.headers.set('X-Research-OS-Owner', ownerId);
      request.headers.set('X-Research-OS-Profile', profileId);
      request.headers.set('X-Research-OS-Session', _sessionToken ?? sessionId);
      final payload = utf8.encode(jsonEncode(<String, dynamic>{'text': text}));
      request.contentLength = payload.length;
      request.add(payload);
      final response = await request.close().timeout(chatTimeout);
      if (response.statusCode != HttpStatus.ok) {
        final responseBody = await utf8.decoder.bind(response).join().timeout(chatTimeout);
        throw HttpException('Launch Desk returned HTTP ${response.statusCode}: $responseBody', uri: uri);
      }
      await for (final line in utf8.decoder.bind(response).transform(const LineSplitter()).timeout(chatTimeout)) {
        if (!line.startsWith('data: ')) continue;
        final decoded = jsonDecode(line.substring(6));
        if (decoded is Map) yield Map<String, dynamic>.from(decoded);
      }
    } finally {
      client.close(force: true);
    }
  }

  Future<Map<String, dynamic>> _request(String method, String path, {bool authenticated = true, Map<String, dynamic>? body, Map<String, String>? headers, Duration? timeoutOverride}) async {
    final client = HttpClient();
    final requestTimeout = timeoutOverride ?? timeout;
    final uri = Uri.parse('$baseUrl$path');
    try {
      final request = method == 'POST' ? await client.postUrl(uri).timeout(requestTimeout) : await client.getUrl(uri).timeout(requestTimeout);
      request.headers.set(HttpHeaders.acceptHeader, 'application/json');
      if (authenticated) {
        request.headers.set('X-Research-OS-Owner', ownerId);
        request.headers.set('X-Research-OS-Profile', profileId);
        request.headers.set('X-Research-OS-Session', _sessionToken ?? sessionId);
      }
      headers?.forEach(request.headers.set);
      if (body != null) {
        final payload = utf8.encode(jsonEncode(body));
        request.headers.set(HttpHeaders.contentTypeHeader, 'application/json; charset=utf-8');
        request.contentLength = payload.length;
        request.add(payload);
      }
      final response = await request.close().timeout(requestTimeout);
      return _decodeResponse(response, uri, requestTimeout);
    } finally {
      client.close(force: true);
    }
  }

  Future<Map<String, dynamic>> _researchRequest(String method, String path, {bool authenticated = true, Map<String, String>? headers}) async {
    final client = HttpClient();
    final uri = Uri.parse('$researchOsBaseUrl$path');
    try {
      final request = method == 'POST' ? await client.postUrl(uri).timeout(timeout) : await client.getUrl(uri).timeout(timeout);
      request.headers.set(HttpHeaders.acceptHeader, 'application/json');
      if (authenticated && _sessionToken != null) request.headers.set('X-Research-OS-Session', _sessionToken!);
      headers?.forEach(request.headers.set);
      request.headers.set(HttpHeaders.contentTypeHeader, 'application/json; charset=utf-8');
      request.contentLength = 2;
      request.add(const <int>[123, 125]);
      final response = await request.close().timeout(timeout);
      return _decodeResponse(response, uri, timeout);
    } finally {
      client.close(force: true);
    }
  }

  Future<Map<String, dynamic>> _decodeResponse(HttpClientResponse response, Uri uri, Duration requestTimeout) async {
    final responseBody = await utf8.decoder.bind(response).join().timeout(requestTimeout);
    final decoded = jsonDecode(responseBody);
    if (decoded is! Map) throw const FormatException('Research OS response must be a JSON object');
    final result = Map<String, dynamic>.from(decoded);
    if (response.statusCode != HttpStatus.ok) throw HttpException('Research OS returned HTTP ${response.statusCode}: ${result['error']}', uri: uri);
    return result;
  }
}
