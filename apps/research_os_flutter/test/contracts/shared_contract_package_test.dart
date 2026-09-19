import 'package:flutter_test/flutter_test.dart';
import 'package:research_os_contracts/research_os_contracts.dart';

void main() {
  test('shared contract package exposes stable capability types', () {
    expect(RuntimeStatusCapability, isNotNull);
    expect(ProviderCapability, isNotNull);
    expect(IdentityCapability, isNotNull);
    expect(MemoryCapability, isNotNull);
    expect(ResearchCapability, isNotNull);
    expect(GitHubCapability, isNotNull);
    expect(OrchestrationCapability, isNotNull);
    expect(ResearchOSCapabilities, isNotNull);
  });
}
