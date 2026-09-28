import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_flutter/src/api/api_endpoint_store.dart';

void main() {
  test('build default follows the compile-time API contract', () {
    const expected = String.fromEnvironment(
      'RESEARCH_OS_API_BASE_URL',
      defaultValue: ApiEndpointStore.renderDefault,
    );
    expect(ApiEndpointStore.buildDefault, expected);
  });

  test('local endpoint remains a valid explicit profile value', () {
    expect(
      ApiEndpointStore.normalize(ApiEndpointStore.localDefault),
      ApiEndpointStore.localDefault,
    );
  });
}
