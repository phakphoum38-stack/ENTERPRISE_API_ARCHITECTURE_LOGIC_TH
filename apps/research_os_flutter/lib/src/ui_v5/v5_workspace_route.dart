import 'package:flutter/material.dart';

import 'v5_capability.dart';

@immutable
class ResearchOSWorkspaceRoute {
  const ResearchOSWorkspaceRoute({
    required this.workspace,
    required this.route,
    required this.label,
    required this.icon,
    required this.capability,
  });

  final ResearchOSWorkspace workspace;
  final String route;
  final String label;
  final IconData icon;
  final ResearchOSCapability capability;
}

class ResearchOSWorkspaceRoutes {
  const ResearchOSWorkspaceRoutes();

  static const all = <ResearchOSWorkspaceRoute>[
    ResearchOSWorkspaceRoute(
      workspace: ResearchOSWorkspace.friend,
      route: 'friend',
      label: 'Friend',
      icon: Icons.support_agent_outlined,
      capability: ResearchOSCapability.friend,
    ),
    ResearchOSWorkspaceRoute(
      workspace: ResearchOSWorkspace.research,
      route: 'research',
      label: 'Research',
      icon: Icons.search_outlined,
      capability: ResearchOSCapability.research,
    ),
    ResearchOSWorkspaceRoute(
      workspace: ResearchOSWorkspace.developer,
      route: 'developer',
      label: 'Develop',
      icon: Icons.code_outlined,
      capability: ResearchOSCapability.github,
    ),
    ResearchOSWorkspaceRoute(
      workspace: ResearchOSWorkspace.brain,
      route: 'brain',
      label: 'Brain',
      icon: Icons.psychology_alt_outlined,
      capability: ResearchOSCapability.brainSkills,
    ),
    ResearchOSWorkspaceRoute(
      workspace: ResearchOSWorkspace.factory,
      route: 'factory',
      label: 'Factory',
      icon: Icons.account_tree_outlined,
      capability: ResearchOSCapability.factory,
    ),
    ResearchOSWorkspaceRoute(
      workspace: ResearchOSWorkspace.memory,
      route: 'memory',
      label: 'Memory',
      icon: Icons.memory_outlined,
      capability: ResearchOSCapability.memory,
    ),
    ResearchOSWorkspaceRoute(
      workspace: ResearchOSWorkspace.library,
      route: 'library',
      label: 'Library',
      icon: Icons.local_library_outlined,
      capability: ResearchOSCapability.library,
    ),
    ResearchOSWorkspaceRoute(
      workspace: ResearchOSWorkspace.evidence,
      route: 'evidence',
      label: 'Evidence',
      icon: Icons.fact_check_outlined,
      capability: ResearchOSCapability.evidence,
    ),
    ResearchOSWorkspaceRoute(
      workspace: ResearchOSWorkspace.identity,
      route: 'identity',
      label: 'Identity',
      icon: Icons.admin_panel_settings_outlined,
      capability: ResearchOSCapability.identity,
    ),
    ResearchOSWorkspaceRoute(
      workspace: ResearchOSWorkspace.owner,
      route: 'owner',
      label: 'Owner',
      icon: Icons.shield_outlined,
      capability: ResearchOSCapability.owner,
    ),
    ResearchOSWorkspaceRoute(
      workspace: ResearchOSWorkspace.settings,
      route: 'settings',
      label: 'Settings',
      icon: Icons.settings_outlined,
      capability: ResearchOSCapability.settings,
    ),
  ];

  ResearchOSWorkspaceRoute forWorkspace(ResearchOSWorkspace workspace) {
    return all.firstWhere((item) => item.workspace == workspace);
  }

  ResearchOSWorkspaceRoute forRoute(String route) {
    return all.firstWhere((item) => item.route == route);
  }

  List<ResearchOSWorkspaceRoute> visibleFor(ResearchOSUserLevel level) {
    const registry = ResearchOSCapabilityRegistry();
    return all
        .where((item) => registry.canAccess(level, item.capability))
        .toList(growable: false);
  }
}
