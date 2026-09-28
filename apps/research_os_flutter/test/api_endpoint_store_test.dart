import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/api/api_endpoint_store.dart';

void main() {
  test('build default is supplied by the build contract', () {
    expect(
      ApiEndpointStore.buildDefault,
      'http://127.0.0.1:8787',
    );
  });

  test('local endpoint is a stable profile', () {
    expect(
      ApiEndpointStore.profileUrl(ApiEndpointStore.connectionResearchOs),
      'http://127.0.0.1:8787',
    );
  });
}
