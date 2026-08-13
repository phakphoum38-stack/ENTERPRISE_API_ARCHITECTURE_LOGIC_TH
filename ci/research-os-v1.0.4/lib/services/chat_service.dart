import 'dart:async';
import 'dart:convert';
import 'dart:io';

import '../models/chat_message.dart';
import '../models/provider_profile.dart';
import 'provider_service.dart';

class ChatService {
  ChatService(this._providerService);

  final ProviderService _providerService;

  Stream<String> streamCompletion({
    required ProviderProfile provider,
    required List<ChatMessage> messages,
  }) async* {
    if (provider.apiStyle != 'openai-compatible') {
      throw UnsupportedError('ตอนนี้รองรับ openai-compatible ก่อน');
    }

    final base = provider.baseUrl.trim().replaceAll(RegExp(r'/+$'), '');
    final uri = Uri.parse('$base/chat/completions');
    final client = HttpClient()..connectionTimeout = const Duration(seconds: 20);

    try {
      final request = await client.postUrl(uri).timeout(const Duration(seconds: 20));
      request.headers.contentType = ContentType.json;
      request.headers.set(HttpHeaders.acceptHeader, 'text/event-stream, application/json');
      final secret = await _providerService.readSecret(provider.id);
      if (secret != null && secret.isNotEmpty) {
        request.headers.set(HttpHeaders.authorizationHeader, 'Bearer $secret');
      }

      request.write(jsonEncode({
        'model': provider.model,
        'messages': messages.map((m) => m.toApiJson()).toList(),
        'stream': true,
      }));

      final response = await request.close().timeout(const Duration(seconds: 60));
      if (response.statusCode < 200 || response.statusCode >= 300) {
        final body = await utf8.decoder.bind(response).join();
        throw StateError('Provider HTTP ${response.statusCode}: ${_short(body)}');
      }

      final contentType = response.headers.contentType?.mimeType ?? '';
      if (contentType.contains('text/event-stream')) {
        await for (final line in response.transform(utf8.decoder).transform(const LineSplitter())) {
          final trimmed = line.trim();
          if (!trimmed.startsWith('data:')) continue;
          final data = trimmed.substring(5).trim();
          if (data == '[DONE]') break;
          if (data.isEmpty) continue;
          try {
            final json = jsonDecode(data) as Map<String, dynamic>;
            final choices = json['choices'] as List<dynamic>?;
            if (choices == null || choices.isEmpty) continue;
            final first = Map<String, dynamic>.from(choices.first as Map);
            final delta = first['delta'];
            if (delta is Map && delta['content'] != null) {
              final text = '${delta['content']}';
              if (text.isNotEmpty) yield text;
            }
          } catch (_) {}
        }
      } else {
        final body = await utf8.decoder.bind(response).join();
        final json = jsonDecode(body) as Map<String, dynamic>;
        final choices = json['choices'] as List<dynamic>?;
        if (choices == null || choices.isEmpty) throw StateError('Provider ไม่ส่ง choices กลับมา');
        final first = Map<String, dynamic>.from(choices.first as Map);
        final message = first['message'];
        if (message is Map && message['content'] != null) yield '${message['content']}';
      }
    } finally {
      client.close(force: true);
    }
  }

  String _short(String value) => value.length > 300 ? '${value.substring(0, 300)}…' : value;
}
