/// Public entry point for the shared Research OS capability contracts.
library;

export 'control_contract.dart';
export 'error_contract.dart';
export 'lifecycle_contract.dart';
export 'migration_contract.dart';
export 'navigation_contract.dart';
export 'observability_contract.dart';
export 'platform_contract.dart';
export 'schema_contract.dart';
export 'state_contract.dart';

abstract interface class RuntimeStatusCapability {
  Future<Map<String, dynamic>> runtimeStatus();
}

abstract interface class ProviderCapability {
  Future<Map<String, dynamic>> providers();
  Future<Map<String, dynamic>> providerStatus();
}

abstract interface class IdentityCapability {
  Future<Map<String, dynamic>> identityStatus();
  Future<Map<String, dynamic>> signIn();
  Future<Map<String, dynamic>> signOut();
}

abstract interface class MemoryCapability {
  Future<Map<String, dynamic>> searchMemory(String query);
  Future<Map<String, dynamic>> commitMemory(
    String syncKey, {
    required String title,
    required List<Map<String, Object?>> conversation,
  });
}

abstract interface class ResearchCapability {
  Future<Map<String, dynamic>> knowledgeArtifacts();
  Future<Map<String, dynamic>> knowledgeGraph();
  Future<Map<String, dynamic>> agents();
  Future<Map<String, dynamic>> agentReadiness();
  Future<Map<String, dynamic>> brainCapacity();
  Future<Map<String, dynamic>> brainSkills();
}

abstract interface class GitHubCapability {
  Future<Map<String, dynamic>> dashboard({String? repository});
}

abstract interface class OrchestrationCapability {
  Future<Map<String, dynamic>> listOrchestrations({
    String? status,
    String? query,
    String? agent,
    int? limit,
  });
  Future<Map<String, dynamic>> orchestration(String runId);
  Future<Map<String, dynamic>> createOrchestration({
    required String objective,
    required List<Map<String, Object?>> steps,
  });
  Future<Map<String, dynamic>> executeOrchestration(
    String runId, {
    bool confirmed = false,
  });
}

abstract interface class ResearchOSCapabilities
    implements
        RuntimeStatusCapability,
        ProviderCapability,
        IdentityCapability,
        MemoryCapability,
        ResearchCapability,
        GitHubCapability,
        OrchestrationCapability {}
