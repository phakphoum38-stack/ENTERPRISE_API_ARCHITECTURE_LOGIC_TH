import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:research_os_flutter/src/api/research_os_stream_client.dart';

void main() {
  test('stream client parses meta, delta, and done events', () async {
    final client = MockClient((request) async {
      expect(request.method, 'POST');
      expect(request.url.path, '/v1/ai/stream');
      return http.Response(
        '${'{"type":"meta","memory_count":2}'}\n'
        '${'{"type":"delta","provider":"mock","model":"mock-v1","text":"Hello "}'}\n'
        '${'{"type":"delta","provider":"mock","model":"mock-v1","text":"world"}'}\n'
        '${'{"type":"done","provider":"mock","model":"mock-v1","memory_count":2}'}\n',
        200,
        headers: <String, String>{
          'content-type': 'application/x-ndjson; charset=utf-8',
        },
      );
    });

    final streamClient = ResearchOSStreamClient(
      baseUrl: 'http://research-os.test',
      client: client,
    );
    final handle = await streamClient.start(
      prompt: 'hello',
      useMemory: true,
      provider: 'mock',
    );

    final events = await handle.events.toList();
    expect(events.map((event) => event.type), <String>[
      'meta',
      'delta',
      'delta',
      'done',
    ]);
    expect(events.where((event) => event.isDelta).map((event) => event.text).join(), 'Hello world');
    expect(events.first.memoryCount, 2);
    expect(events.last.provider, 'mock');
    expect(events.last.isDone, isTrue);
  });
}
