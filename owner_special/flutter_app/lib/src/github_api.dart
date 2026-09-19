import 'dart:convert';
import 'dart:io';

class GitHubApiException implements Exception {
  GitHubApiException(this.statusCode, this.message);

  final int statusCode;
  final String message;

  @override
  String toString() => 'GitHubApiException($statusCode): $message';
}

class GitHubRepositorySnapshot {
  const GitHubRepositorySnapshot({
    required this.fullName,
    required this.defaultBranch,
    required this.privateRepository,
    required this.openIssues,
    required this.htmlUrl,
  });

  final String fullName;
  final String defaultBranch;
  final bool privateRepository;
  final int openIssues;
  final String htmlUrl;

  factory GitHubRepositorySnapshot.fromJson(Map<String, dynamic> json) {
    return GitHubRepositorySnapshot(
      fullName: json['full_name'] as String? ?? '',
      defaultBranch: json['default_branch'] as String? ?? 'main',
      privateRepository: json['private'] as bool? ?? false,
      openIssues: json['open_issues_count'] as int? ?? 0,
      htmlUrl: json['html_url'] as String? ?? '',
    );
  }
}

class GitHubApi {
  GitHubApi({
    HttpClient? client,
    this.baseUrl = 'https://api.github.com',
    String? token,
    this.timeout = const Duration(seconds: 8),
  })  : _client = client ?? HttpClient(),
        _token = token ?? Platform.environment['GITHUB_TOKEN'];

  final HttpClient _client;
  final String baseUrl;
  final String? _token;
  final Duration timeout;

  Future<Map<String, dynamic>> repository(String fullName) =>
      _getObject('/repos/${_encodePath(fullName)}');

  Future<List<dynamic>> issues(String fullName, {String state = 'open'}) =>
      _getList('/repos/${_encodePath(fullName)}/issues?state=${Uri.encodeQueryComponent(state)}');

  Future<List<dynamic>> branches(String fullName) =>
      _getList('/repos/${_encodePath(fullName)}/branches');

  Future<Map<String, dynamic>> file(String fullName, String path, {String? reference}) async {
    final query = reference == null ? '' : '?ref=${Uri.encodeQueryComponent(reference)}';
    final json = await _getObject('/repos/${_encodePath(fullName)}/contents/${_encodePath(path)}$query');
    final encoded = json['content'] as String?;
    if (encoded == null) return json;
    final normalized = encoded.replaceAll(RegExp(r'\\s'), '');
    return <String, dynamic>{
      ...json,
      'decoded_content': utf8.decode(base64Decode(normalized)),
    };
  }

  Future<List<dynamic>> pullRequests(String fullName, {String state = 'open'}) =>
      _getList('/repos/${_encodePath(fullName)}/pulls?state=${Uri.encodeQueryComponent(state)}');

  Future<List<dynamic>> checks(String fullName, String reference) =>
      _getList('/repos/${_encodePath(fullName)}/commits/${Uri.encodeComponent(reference)}/check-runs');

  Future<Map<String, dynamic>> compare(String fullName, String base, String head) =>
      _getObject('/repos/${_encodePath(fullName)}/compare/${Uri.encodeComponent(base)}...${Uri.encodeComponent(head)}');

  Future<List<dynamic>> search(String fullName, String query) =>
      _getList('/search/code?q=${Uri.encodeQueryComponent('$query repo:$fullName')}');

  Future<void> dispose() async => _client.close(force: true);

  Future<Map<String, dynamic>> _getObject(String path) async {
    final decoded = await _request(path);
    if (decoded is! Map) throw const FormatException('GitHub response must be a JSON object');
    return Map<String, dynamic>.from(decoded);
  }

  Future<List<dynamic>> _getList(String path) async {
    final decoded = await _request(path);
    if (decoded is! List) throw const FormatException('GitHub response must be a JSON list');
    return decoded;
  }

  Future<dynamic> _request(String path) async {
    final uri = Uri.parse('$baseUrl$path');
    final request = await _client.getUrl(uri).timeout(timeout);
    request.headers.set(HttpHeaders.acceptHeader, 'application/vnd.github+json');
    request.headers.set('X-GitHub-Api-Version', '2022-11-28');
    request.headers.set(HttpHeaders.userAgentHeader, 'Research-OS-GitHub-Workbench');
    if (_token != null && _token.trim().isNotEmpty) {
      request.headers.set(HttpHeaders.authorizationHeader, 'Bearer ${_token.trim()}');
    }
    final response = await request.close().timeout(timeout);
    final body = await utf8.decoder.bind(response).join().timeout(timeout);
    dynamic decoded;
    try {
      decoded = jsonDecode(body);
    } catch (_) {
      throw GitHubApiException(response.statusCode, body);
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final message = decoded is Map<String, dynamic>
          ? decoded['message']?.toString() ?? 'GitHub request failed'
          : 'GitHub request failed';
      throw GitHubApiException(response.statusCode, message);
    }
    return decoded;
  }

  static String _encodePath(String value) =>
      value.split('/').map(Uri.encodeComponent).join('/');
}
