import 'package:research_os_contracts/research_os_contracts.dart';

import 'owner_friend_capability_adapter.dart';

/// Capability composition boundary for the canonical Control Center.
///
/// The shell owns navigation and presentation; each subsystem remains behind
/// its own adapter. Missing capabilities are represented as absent slots
/// rather than replaced with fake implementations.
final class ControlCenterCapabilities {
  ControlCenterCapabilities({
    required this.owner,
    this.research,
    this.v3,
  });

  final OwnerFriendCapabilityAdapter owner;
  final ResearchOSCapabilities? research;
  final RuntimeStatusCapability? v3;

  RuntimeStatusCapability get runtime => owner;

  IdentityCapability get identity => owner;

  MemoryCapability? get memory => research;

  ProviderCapability? get providers => research;

  ResearchCapability? get researchCapabilities => research;

  GitHubCapability? get github => research;

  OrchestrationCapability? get orchestration => research;

  /// Returns stable capability names for diagnostics and Control Center UI.
  Set<String> get availableCapabilities => <String>{
        'runtime',
        'identity',
        if (memory != null) 'memory',
        if (providers != null) 'provider',
        if (researchCapabilities != null) 'research',
        if (github != null) 'github',
        if (orchestration != null) 'orchestration',
        if (v3 != null) 'v3-runtime',
      };
}
