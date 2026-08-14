import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_v3_flutter/src/api/v3_api.dart';

void main() {
  test('chat sends explicit UTF-8 Content-Length to the local V3 service', () async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    final observed = Completer<Map<String, dynamic>>();

    server.listen((request) async {
      final bodyBytes = <int>[];
      await for (final chunk in request) {
        bodyBytes.addAll(chunk);
      }
      observed.complete(<String, dynamic>{
        'method': request.method,
        'path': request.uri.path,
        'contentLength': request.contentLength,
        'transferEncoding':
            request.headers.value(HttpHeaders.transferEncodingHeader),
        'contentType': request.headers.contentType?.mimeType,
        'charset': request.headers.contentType?.charset,
        'user': request.headers.value('X-Research-OS-User'),
        'profile': request.headers.value('X-Research-OS-Profile'),
        'bodyBytes': bodyBytes,
      });

      request.response.statusCode = HttpStatus.ok;
      request.response.headers.contentType = ContentType.json;
      request.response.write(jsonEncode(<String, dynamic>{
        'contract': 'research-os-v3-chat-v1',
        'text': 'mock:ok',
        'provider': 'mock',
      }));
      await request.response.close();
    });

    try {
      final api = HttpV3Api(
        baseUrl: 'http://${server.address.address}:${server.port}',
        userId: 'alice',
        profileId: 'default',
      );
      final response = await api.chat(
        'สวัสดี Research OS',
        sessionId: 'framing-test',
      );
      final captured = await observed.future.timeout(const Duration(seconds: 5));
      final bytes = List<int>.from(captured['bodyBytes'] as List);
      final decoded = jsonDecode(utf8.decode(bytes)) as Map<String, dynamic>;

      expect(response['contract'], 'research-os-v3-chat-v1');
      expect(captured['method'], 'POST');
      expect(captured['path'], '/v3/chat');
      expect(captured['contentLength'], bytes.length);
      expect(captured['contentLength'], greaterThan(0));
      expect(captured['transferEncoding'], isNull);
      expect(captured['contentType'], 'application/json');
      expect(captured['charset'], 'utf-8');
      expect(captured['user'], 'alice');
      expect(captured['profile'], 'default');
      expect(decoded['message'], 'สวัสดี Research OS');
      expect(decoded['session_id'], 'framing-test');
      expect(decoded['provider'], 'auto');
    } finally {
      await server.close(force: true);
    }
  });
}
