import 'package:flutter/material.dart';

enum ResearchOSUserLevel {
  user,
  powerUser,
  developer,
  owner,
  ownerSpecial,
}

enum ResearchOSCapability {
  friend,
  voice,
  text,
  sessions,
  memory,
  cloudSync,
  copilot,
  research,
  agents,
  brainSkills,
  orchestrator,
  factory,
  library,
  knowledgeGraph,
  evidence,
  provenance,
  github,
  codespaces,
  googleWorkspace,
  identity,
  localApi,
  monitor,
  settings,
  owner,
  ownerSpecial,
  ciCd,
  release,
}

enum ResearchOSWorkspace {
  friend,
  research,
  developer,
  brain,
  factory,
  memory,
  library,
  evidence,
  identity,
  owner,
  settings,
}

@immutable
class ResearchOSCapabilityDescriptor {
  const ResearchOSCapabilityDescriptor({
    required this.capability,
    required this.minimumLevel,
    required this.workspace,
  });

  final ResearchOSCapability capability;
  final ResearchOSUserLevel minimumLevel;
  final ResearchOSWorkspace workspace;
}

class ResearchOSCapabilityRegistry {
  const ResearchOSCapabilityRegistry();

  static const _levelRank = <ResearchOSUserLevel, int>{
    ResearchOSUserLevel.user: 0,
    ResearchOSUserLevel.powerUser: 1,
    ResearchOSUserLevel.developer: 2,
    ResearchOSUserLevel.owner: 3,
    ResearchOSUserLevel.ownerSpecial: 4,
  };

  static const descriptors = <ResearchOSCapabilityDescriptor>[
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.friend,
      minimumLevel: ResearchOSUserLevel.user,
      workspace: ResearchOSWorkspace.friend,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.voice,
      minimumLevel: ResearchOSUserLevel.user,
      workspace: ResearchOSWorkspace.friend,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.text,
      minimumLevel: ResearchOSUserLevel.user,
      workspace: ResearchOSWorkspace.friend,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.sessions,
      minimumLevel: ResearchOSUserLevel.user,
      workspace: ResearchOSWorkspace.friend,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.memory,
      minimumLevel: ResearchOSUserLevel.user,
      workspace: ResearchOSWorkspace.memory,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.cloudSync,
      minimumLevel: ResearchOSUserLevel.user,
      workspace: ResearchOSWorkspace.friend,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.research,
      minimumLevel: ResearchOSUserLevel.user,
      workspace: ResearchOSWorkspace.research,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.library,
      minimumLevel: ResearchOSUserLevel.user,
      workspace: ResearchOSWorkspace.library,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.knowledgeGraph,
      minimumLevel: ResearchOSUserLevel.powerUser,
      workspace: ResearchOSWorkspace.library,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.agents,
      minimumLevel: ResearchOSUserLevel.powerUser,
      workspace: ResearchOSWorkspace.brain,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.brainSkills,
      minimumLevel: ResearchOSUserLevel.powerUser,
      workspace: ResearchOSWorkspace.brain,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.orchestrator,
      minimumLevel: ResearchOSUserLevel.powerUser,
      workspace: ResearchOSWorkspace.brain,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.factory,
      minimumLevel: ResearchOSUserLevel.powerUser,
      workspace: ResearchOSWorkspace.factory,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.copilot,
      minimumLevel: ResearchOSUserLevel.developer,
      workspace: ResearchOSWorkspace.developer,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.github,
      minimumLevel: ResearchOSUserLevel.developer,
      workspace: ResearchOSWorkspace.developer,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.codespaces,
      minimumLevel: ResearchOSUserLevel.developer,
      workspace: ResearchOSWorkspace.developer,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.googleWorkspace,
      minimumLevel: ResearchOSUserLevel.developer,
      workspace: ResearchOSWorkspace.research,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.ciCd,
      minimumLevel: ResearchOSUserLevel.developer,
      workspace: ResearchOSWorkspace.developer,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.identity,
      minimumLevel: ResearchOSUserLevel.owner,
      workspace: ResearchOSWorkspace.identity,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.evidence,
      minimumLevel: ResearchOSUserLevel.owner,
      workspace: ResearchOSWorkspace.evidence,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.provenance,
      minimumLevel: ResearchOSUserLevel.owner,
      workspace: ResearchOSWorkspace.evidence,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.localApi,
      minimumLevel: ResearchOSUserLevel.owner,
      workspace: ResearchOSWorkspace.identity,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.monitor,
      minimumLevel: ResearchOSUserLevel.owner,
      workspace: ResearchOSWorkspace.identity,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.settings,
      minimumLevel: ResearchOSUserLevel.user,
      workspace: ResearchOSWorkspace.settings,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.owner,
      minimumLevel: ResearchOSUserLevel.owner,
      workspace: ResearchOSWorkspace.owner,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.release,
      minimumLevel: ResearchOSUserLevel.owner,
      workspace: ResearchOSWorkspace.owner,
    ),
    ResearchOSCapabilityDescriptor(
      capability: ResearchOSCapability.ownerSpecial,
      minimumLevel: ResearchOSUserLevel.ownerSpecial,
      workspace: ResearchOSWorkspace.owner,
    ),
  ];

  bool canAccess(ResearchOSUserLevel level, ResearchOSCapability capability) {
    final descriptor = descriptors.firstWhere(
      (item) => item.capability == capability,
    );
    return _levelRank[level]! >= _levelRank[descriptor.minimumLevel]!;
  }

  ResearchOSWorkspace workspaceFor(ResearchOSCapability capability) {
    return descriptors
        .firstWhere((item) => item.capability == capability)
        .workspace;
  }

  List<ResearchOSCapability> capabilitiesFor(ResearchOSUserLevel level) {
    return descriptors
        .where((item) => canAccess(level, item.capability))
        .map((item) => item.capability)
        .toList(growable: false);
  }
}
