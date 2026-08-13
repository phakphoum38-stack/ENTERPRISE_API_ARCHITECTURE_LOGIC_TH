import 'dart:convert';
import 'dart:io';

abstract interface class V3Api {
  Future<Map<String, dynamic>> health();
  Future<Map<String, dynamic>> providers();
  Future<Map<String, dynamic>> master({
    int tasks = 1,
    int risk = 1,
    int parallelism = 1,
  });
  Future<Map<String, dynamic>> user();
  Future<Map<String, dynamic>> skills();
  Future<Map<String, dynamic>> tools();
  Future<Map<String, dynamic>> agents();
  Future<Map<String, dynamic>> memory({String query = '', int limit = 20});
  Future<Map<String, dynamic>> factoryPlan({
    int tasks = 1,
    int risk = 1,
    int parallelism = 1,
  });
  Future<Map<String, dynamic>> chat(
    String prompt, {
    String? agent,
    String? preferredProvider,
    int memoryLimit = 8,
  });
  Future<Map<String, dynamic>> addMemory(
    String text, {
    List<String> tags = const <String>[],
  });
  Future<Map<String, dynamic>> runAgent(String name, String prompt);
  Future<Map<String, dynamic>> executeTool(
    String name,
    Map<String, dynamic> arguments, {
    bool approved = false,
  });
}

final class HttpV3Api implements V3Api {
  HttpV3Api({
    required String baseUrl,
    required this.userId,
    this.profileId = 'default',
    this.timeout = const Duration(seconds: 30),
  }) : baseUrl = baseUrl.endsWith('/')
            ? baseUrl.substring(0, baseUrl.length - 1)
            : baseUrl;

  final String baseUrl;
  final String userId;
  final String profileId;
  final Duration timeout;

  @override
  Future<Map<String, dynamic>> health() => _get('/health');

  @override
  Future<Map<String, dynamic>> providers() => _get('/v3/providers');

  @override
  Future<Map<String, dynamic>> master({
    int tasks = 1,
    int risk = 1,
    int parallelism = 1,
  }) =>
      _get(
        '/v3/master?tasks=$tasks&risk=$risk&parallelism=$parallelism',
      );

  @override
  Future<Map<String, dynamic>> user() => _get('/v3/user');

  @override
  Future<Map<String, dynamic>> skills() => _get('/v3/skills');

  @override
  Future<Map<String, dynamic>> tools() => _get('/v3/tools');

  @override
  Future<Map<String, dynamic>> agents() => _get('/v3/agents');

  @override
  Future<Map<String, dynamic>> memory({String query = '', int limit = 20}) {
    final q = Uri.encodeQueryComponent(query);
    return _get('/v3/memory?q=$q&limit=$limit');
  }

  @override
  Future<Map<String, dynamic>> factoryPlan({
    int tasks = 1,
    int risk = 1,
    int parallelism = 1,
  }) =>
      _get(
        '/v3/factory/plan?tasks=$tasks&risk=$risk&parallelism=$parallelism',
      );

  @override
  Future<Map<String, dynamic>> chat(
    String prompt, {
    String? agent,
    String? preferredProvider,
    int memoryLimit = 8,
  }) =>
      _post(
        '/v3/chat',
        <String, dynamic>{
          'prompt': prompt,
          'memory_limit': memoryLimit,
          if (agent != null && agent.isNotEmpty) 'agent': agent,
          if (preferredProvider != null && preferredProvider.isNotEmpty)
            'preferred_provider': preferredProvider,
        },
      );

  @override
  Future<Map<String, dynamic>> addMemory(
    String text, {
    List<String> tags = const <String>[],
  }) =>
      _post('/v3/memory', <String, dynamic>{'text': text, 'tags': tags});

  @override
  Future<Map<String, dynamic>> runAgent(String name, String prompt) =>
      _post('/v3/agents/run', <String, dynamic>{'name': name, 'prompt': prompt});

  @override
  Future<Map<String, dynamic>> executeTool(
    String name,
    Map<String, dynamic> arguments, {
    bool approved = false,
  }) =>
      _post(
        '/v3/tools/execute',
        <String, dynamic>{'name': name, 'arguments': arguments},
        approved: approved,
      );

  Future<Map<String, dynamic>> _get(String path) => _request('GET', path);

  Future<Map<String, dynamic>> _post(
    String path,
    Map<String, dynamic> payload, {
    bool approved = false,
  }) =>
      _request('POST', path, payload: payload, approved: approved);

  Future<Map<String, dynamic>> _request(
    String method,
    String path, {
    Map<String, dynamic>? payload,
    bool approved = false,
  }) async {
    final client = HttpClient();
    final uri = Uri.parse('$baseUrl$path');
    try {
      final request = method == 'POST'
          ? await client.postUrl(uri).timeout(timeout)
          : await client.getUrl(uri).timeout(timeout);
      request.headers.set(HttpHeaders.acceptHeader, 'application/json');
      request.headers.set('X-Research-OS-User', userId);
      request.headers.set('X-Research-OS-Profile', profileId);
      if (approved) {
        request.headers.set('X-Research-OS-Approval', 'granted');
      }
      if (payload != null) {
        request.headers.contentType = ContentType.json;
        request.write(jsonEncode(payload));
      }
      final response = await request.close().timeout(timeout);
      final body = await utf8.decoder.bind(response).join().timeout(timeout);
      final decoded = body.isEmpty ? <String, dynamic>{} : jsonDecode(body);
      if (decoded is! Map) {
        throw const FormatException(
          'Research OS V3 response must be a JSON object',
        );
      }
      final result = Map<String, dynamic>.from(decoded);
      if (response.statusCode < 200 || response.statusCode >= 300) {
        final message = result['error']?.toString() ??
            'Research OS V3 returned HTTP ${response.statusCode}';
        throw HttpException(message, uri: uri);
      }
      return result;
    } finally {
      client.close(force: true);
    }
  }
}
