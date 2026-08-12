import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/api/api_endpoint_store.dart';

void main() {
  test('local API default remains the loopback service endpoint', () {
    expect(ApiEndpointStore.localDefault, 'http://127.0.0.1:8787');
  });
}
