import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'provider_selection_store.dart';

class ResearchOSStreamEvent {
  const ResearchOSStreamEvent({
    required this.type,
    this.text = '',
    this.provider,
    this.model,
    this.memoryCount,
    this.detail,
  });

  final String type;
  final String text;
  final String? provider;
  final String? model;
  final int? memoryCount;
  final String? detail;

  bool get isDelta => type == 'delta';
  bool get isDone => type == 'done';
  bool get isError => type == 'error';

  factory ResearchOSStreamEvent.fromJson(Map<String, dynamic> json) {
    final memory = json['memory_count'];
    return ResearchOSStreamEvent(
      type: (json['type'] ?? '').toString(),
      text: (json['text'] ?? '').toString(),
      provider: json['provider']?.toString(),
      model: json['model']?.toString(),
      memoryCount: memory is num ? memory.toInt() : null,
      detail: json['detail']?.toString(),
    );
  }
}

class ResearchOSStreamHandle {
  ResearchOSStreamHandle(this.events, this._cancel);

  final Stream<ResearchOSStreamEvent> events;
  final Future<void> Function() _cancel;

  Future<void> cancel() => _cancel();
}

class ResearchOSStreamClient {
  ResearchOSStreamClient({required this.baseUrl, http.Client? client})
      : _client = client ?? http.Client(),
        _ownsClient = client == null;

  final String baseUrl;
  final http.Client _client;
  final bool _ownsClient;

  Future<ResearchOSStreamHandle> start({
    required String prompt,
    required bool useMemory,
    String? provider,
    String? sessionId,
  }) async {
    final request = http.Request('POST', Uri.parse('$baseUrl/v1/ai/stream'))
      ..headers['Content-Type'] = 'application/json'
      ..body = jsonEncode(<String, Object?>{
        'prompt': prompt,
        'memory': useMemory,
        'provider': provider ?? selectedProviderState.value,
        if (sessionId != null) 'session_id': sessionId,
      });

    final response = await _client.send(request);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final body = await response.stream.bytesToString();
      throw StateError(
        'Research OS stream failed (${response.statusCode}): $body',
      );
    }

    late StreamSubscription<List<int>> subscription;
    final controller = StreamController<ResearchOSStreamEvent>();
    final decoder = utf8.decoder.startChunkedConversion(
      _LineStringSink((line) {
        final value = line.trim();
        if (value.isEmpty) return;
        try {
          final decoded = jsonDecode(value);
          if (decoded is Map<String, dynamic>) {
            controller.add(ResearchOSStreamEvent.fromJson(decoded));
          }
        } on FormatException catch (error, stack) {
          controller.addError(error, stack);
        }
      }),
    );

    subscription = response.stream.listen(
      decoder.add,
      onError: controller.addError,
      onDone: () {
        decoder.close();
        controller.close();
      },
      cancelOnError: true,
    );

    return ResearchOSStreamHandle(
      controller.stream,
      () async {
        await subscription.cancel();
        if (!controller.isClosed) await controller.close();
      },
    );
  }

  void close() {
    if (_ownsClient) _client.close();
  }
}

class _LineStringSink implements Sink<String> {
  _LineStringSink(this.onLine);

  final void Function(String line) onLine;
  String _buffer = '';

  @override
  void add(String data) {
    _buffer += data;
    while (true) {
      final index = _buffer.indexOf('\n');
      if (index < 0) break;
      final line = _buffer.substring(0, index);
      _buffer = _buffer.substring(index + 1);
      onLine(line);
    }
  }

  @override
  void close() {
    if (_buffer.trim().isNotEmpty) onLine(_buffer);
    _buffer = '';
  }
}
