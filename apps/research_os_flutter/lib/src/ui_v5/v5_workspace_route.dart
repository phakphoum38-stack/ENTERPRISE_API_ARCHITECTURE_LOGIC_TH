import 'package:flutter/material.dart';

import '../ui/enterprise_navigation.dart';
import 'v5_capability.dart';

@immutable
class ResearchOSWorkspaceRoute {
  const ResearchOSWorkspaceRoute({
    required this.workspace,
    required this.route,
    required this.destinationId,
    required this.capability,
  });

  final ResearchOSWorkspace workspace;
  final String route;
  final String destinationId;
  final ResearchOSCapability capability;

  ResearchNavItem get destination => researchNavigationItems.firstWhere(
        (item) => item.destinationId == destinationId,
      );

  String get label => destination.label;
  IconData get icon => destination.icon;
}

class ResearchOSWorkspaceRoutes {
  const ResearchOSWorkspaceRoutes();

  static List<ResearchOSWorkspaceRoute> get all => <ResearchOSWorkspaceRoute>[
        const ResearchOSWorkspaceRoute(
          workspace: ResearchOSWorkspace.friend,
          route: 'friend',
          destinationId: 'friend_connect',
          capability: ResearchOSCapability.friend,
        ),
        const ResearchOSWorkspaceRoute(
          workspace: ResearchOSWorkspace.research,
          route: 'research',
          destinationId: 'home',
          capability: ResearchOSCapability.research,
        ),
        const ResearchOSWorkspaceRoute(
          workspace: ResearchOSWorkspace.developer,
          route: 'developer',
          destinationId: 'github',
          capability: ResearchOSCapability.github,
        ),
        const ResearchOSWorkspaceRoute(
          workspace: ResearchOSWorkspace.brain,
          route: 'brain',
          destinationId: 'brain_skills',
          capability: ResearchOSCapability.brainSkills,
        ),
        const ResearchOSWorkspaceRoute(
          workspace: ResearchOSWorkspace.factory,
          route: 'factory',
          destinationId: 'workflows',
          capability: ResearchOSCapability.factory,
        ),
        const ResearchOSWorkspaceRoute(
          workspace: ResearchOSWorkspace.memory,
          route: 'memory',
          destinationId: 'library',
          capability: ResearchOSCapability.memory,
        ),
        const ResearchOSWorkspaceRoute(
          workspace: ResearchOSWorkspace.library,
          route: 'library',
          destinationId: 'library',
          capability: ResearchOSCapability.library,
        ),
        const ResearchOSWorkspaceRoute(
          workspace: ResearchOSWorkspace.evidence,
          route: 'evidence',
          destinationId: 'control_center',
          capability: ResearchOSCapability.evidence,
        ),
        const ResearchOSWorkspaceRoute(
          workspace: ResearchOSWorkspace.identity,
          route: 'identity',
          destinationId: 'google_sign_in',
          capability: ResearchOSCapability.identity,
        ),
        const ResearchOSWorkspaceRoute(
          workspace: ResearchOSWorkspace.owner,
          route: 'owner',
          destinationId: 'owner',
          capability: ResearchOSCapability.owner,
        ),
        const ResearchOSWorkspaceRoute(
          workspace: ResearchOSWorkspace.settings,
          route: 'settings',
          destinationId: 'settings',
          capability: ResearchOSCapability.settings,
        ),
      ];

  ResearchOSWorkspaceRoute forWorkspace(ResearchOSWorkspace workspace) =>
      all.firstWhere((item) => item.workspace == workspace);

  ResearchOSWorkspaceRoute forRoute(String route) =>
      all.firstWhere((item) => item.route == route);

  List<ResearchOSWorkspaceRoute> visibleFor(ResearchOSUserLevel level) {
    const registry = ResearchOSCapabilityRegistry();
    return all
        .where((item) => registry.canAccess(level, item.capability))
        .toList(growable: false);
  }
}
