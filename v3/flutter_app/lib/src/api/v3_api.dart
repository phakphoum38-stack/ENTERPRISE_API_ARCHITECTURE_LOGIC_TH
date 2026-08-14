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
    String message, {
    String sessionId = 'default',
    String provider = 'auto',
    String mode = 'answer',
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
    this.timeout = const Duration(seconds: 2),
    this.chatTimeout = const Duration(seconds: 45),
    this.executionTimeout = const Duration(seconds: 30),
  }) : baseUrl = baseUrl.endsWith('/')
            ? baseUrl.substring(0, baseUrl.length - 1)
            : baseUrl;

  final String baseUrl;
  final String userId;
  final String profileId;
  final Duration timeout;
  final Duration chatTimeout;
  final Duration executionTimeout;

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
      _get('/v3/master?tasks=$tasks&risk=$risk&parallelism=$parallelism');

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
    String message, {
    String sessionId = 'default',
    String provider = 'auto',
    String mode = 'answer',
    String? agent,
    String? preferredProvider,
    int memoryLimit = 8,
  }) {
    final selectedProvider = preferredProvider?.trim().isNotEmpty == true
        ? preferredProvider!.trim()
        : provider;
    return _post(
      '/v3/chat',
      <String, dynamic>{
        'message': message,
        'session_id': sessionId,
        'provider': selectedProvider,
        'mode': mode,
        'memory_limit': memoryLimit,
        if (agent != null && agent.trim().isNotEmpty) 'agent': agent.trim(),
      },
      requestTimeout: chatTimeout,
    );
  }

  @override
  Future<Map<String, dynamic>> addMemory(
    String text, {
    List<String> tags = const <String>[],
  }) =>
      _post('/v3/memory', <String, dynamic>{'text': text, 'tags': tags});

  @override
  Future<Map<String, dynamic>> runAgent(String name, String prompt) => _post(
        '/v3/agents/run',
        <String, dynamic>{'name': name, 'prompt': prompt},
        requestTimeout: executionTimeout,
      );

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
        requestTimeout: executionTimeout,
      );

  Future<Map<String, dynamic>> _get(String path) => _request('GET', path);

  Future<Map<String, dynamic>> _post(
    String path,
    Map<String, dynamic> payload, {
    bool approved = false,
    Duration? requestTimeout,
  }) =>
      _request(
        'POST',
        path,
        payload: payload,
        approved: approved,
        requestTimeout: requestTimeout,
      );

  Future<Map<String, dynamic>> _request(
    String method,
    String path, {
    Map<String, dynamic>? payload,
    bool approved = false,
    Duration? requestTimeout,
  }) async {
    final operationTimeout = requestTimeout ?? timeout;
    final client = HttpClient();
    final uri = Uri.parse('$baseUrl$path');
    try {
      final request = method == 'POST'
          ? await client.postUrl(uri).timeout(operationTimeout)
          : await client.getUrl(uri).timeout(operationTimeout);
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
      final response = await request.close().timeout(operationTimeout);
      final body = await utf8.decoder
          .bind(response)
          .join()
          .timeout(operationTimeout);
      return _decode(uri, response.statusCode, body);
    } finally {
      client.close(force: true);
    }
  }

  Map<String, dynamic> _decode(Uri uri, int statusCode, String body) {
    final Object? decoded;
    try {
      decoded = body.isEmpty ? <String, dynamic>{} : jsonDecode(body);
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
