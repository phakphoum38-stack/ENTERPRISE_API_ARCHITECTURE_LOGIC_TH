import 'package:flutter_test/flutter_test.dart';

import 'package:research_os_flutter/src/contracts/research_os_capabilities.dart';

void main() {
  test('capability surface remains grouped by stable domain boundaries', () {
    expect(RuntimeStatusCapability, isNotNull);
    expect(ProviderCapability, isNotNull);
    expect(IdentityCapability, isNotNull);
    expect(MemoryCapability, isNotNull);
    expect(ResearchCapability, isNotNull);
    expect(GitHubCapability, isNotNull);
    expect(OrchestrationCapability, isNotNull);
  });
}
