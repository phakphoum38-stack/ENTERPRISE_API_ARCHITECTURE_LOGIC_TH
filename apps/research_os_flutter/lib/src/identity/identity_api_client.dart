import 'dart:convert';

import 'package:http/http.dart' as http;

import '../api/api_endpoint_store.dart';

class IdentityApiException implements Exception {
  const IdentityApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  bool get unauthorized => statusCode == 401 || statusCode == 403;

  @override
  String toString() => message;
}

class IdentityApiClient {
  IdentityApiClient({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  String get baseUrl => ApiEndpointStore.renderDefault;

  Future<Map<String, dynamic>> requestCode(String email) {
    return _post('/v1/identity/request-code', <String, Object?>{'email': email});
  }

  Future<Map<String, dynamic>> verifyCode({
    required String challengeId,
    required String code,
  }) {
    return _post('/v1/identity/verify-code', <String, Object?>{
      'challenge_id': challengeId,
      'code': code,
    });
  }

  Future<Map<String, dynamic>> getProfile(String token) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/v1/identity/profile'),
      headers: <String, String>{'Authorization': 'Bearer $token'},
    );
    return _decode(response);
  }

  Future<Map<String, dynamic>> updatePreferences(
    String token,
    Map<String, Object?> preferences,
  ) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/v1/identity/preferences'),
      headers: <String, String>{
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode(<String, Object?>{'preferences': preferences}),
    );
    return _decode(response);
  }

  Future<Map<String, dynamic>> _post(
    String path,
    Map<String, Object?> body,
  ) async {
    final response = await _client.post(
      Uri.parse('$baseUrl$path'),
      headers: const <String, String>{'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
    return _decode(response);
  }

  Map<String, dynamic> _decode(http.Response response) {
    Object? decoded;
    try {
      decoded = jsonDecode(response.body);
    } on FormatException {
      throw IdentityApiException(
        'Identity service returned invalid JSON (${response.statusCode}).',
        statusCode: response.statusCode,
      );
    }
    if (decoded is! Map<String, dynamic>) {
      throw IdentityApiException(
        'Identity service returned an invalid response.',
        statusCode: response.statusCode,
      );
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = decoded['detail'] ?? decoded['error'] ?? 'Unknown error';
      throw IdentityApiException(
        'Identity error ${response.statusCode}: $detail',
        statusCode: response.statusCode,
      );
    }
    return decoded;
  }

  void close() => _client.close();
}
