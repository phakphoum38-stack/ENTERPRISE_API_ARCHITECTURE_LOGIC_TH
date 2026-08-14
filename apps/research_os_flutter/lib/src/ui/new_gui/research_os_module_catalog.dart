import 'package:flutter/material.dart';

enum ResearchOSModuleSection { main, workspace, system }

enum ResearchOSModuleId {
  home,
  chat,
  agents,
  memory,
  skills,
  tools,
  factory,
  providers,
  files,
  repositories,
  github,
  drive,
  runtime,
  installer,
  backup,
  restore,
  shell,
}

class ResearchOSModuleDefinition {
  const ResearchOSModuleDefinition({
    required this.id,
    required this.section,
    required this.label,
    required this.icon,
    required this.availability,
    this.legacyPageIndex,
    this.backendSource,
  });

  final ResearchOSModuleId id;
  final ResearchOSModuleSection section;
  final String label;
  final IconData icon;

  /// `existing` means the current Flutter shell already has a feature page.
  /// `adapter` means the capability exists but needs a new dedicated surface.
  /// `planned` means implementation evidence still needs to be established.
  final String availability;

  /// Existing page index from the current ResearchOSAppShell when available.
  final int? legacyPageIndex;

  /// Human-readable source of truth used while wiring the new shell.
  final String? backendSource;
}

const researchOSNewGuiModules = <ResearchOSModuleDefinition>[
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.home,
    section: ResearchOSModuleSection.main,
    label: 'Home',
    icon: Icons.home_outlined,
    availability: 'existing',
    legacyPageIndex: 0,
    backendSource: 'features/home + /health',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.chat,
    section: ResearchOSModuleSection.main,
    label: 'Chat AI',
    icon: Icons.chat_bubble_outline_rounded,
    availability: 'existing',
    legacyPageIndex: 1,
    backendSource: 'features/chat + /v1/ai/answer-with-memory',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.agents,
    section: ResearchOSModuleSection.main,
    label: 'Agents',
    icon: Icons.smart_toy_outlined,
    availability: 'existing',
    legacyPageIndex: 2,
    backendSource: 'features/agents + /v1/agents',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.memory,
    section: ResearchOSModuleSection.main,
    label: 'Memory',
    icon: Icons.memory_outlined,
    availability: 'adapter',
    backendSource: '/v1/memory/search + memory/evidence runtime',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.skills,
    section: ResearchOSModuleSection.main,
    label: 'Skills',
    icon: Icons.psychology_alt_outlined,
    availability: 'adapter',
    backendSource: 'skill registry/runtime',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.tools,
    section: ResearchOSModuleSection.main,
    label: 'Tools',
    icon: Icons.build_circle_outlined,
    availability: 'adapter',
    backendSource: 'tool registry/runtime',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.factory,
    section: ResearchOSModuleSection.main,
    label: 'Factory',
    icon: Icons.account_tree_outlined,
    availability: 'adapter',
    backendSource: '/v1/agents/orchestrations',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.providers,
    section: ResearchOSModuleSection.main,
    label: 'Providers',
    icon: Icons.hub_outlined,
    availability: 'adapter',
    backendSource: '/v1/providers',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.files,
    section: ResearchOSModuleSection.workspace,
    label: 'Files',
    icon: Icons.folder_outlined,
    availability: 'adapter',
    backendSource: 'library/workspace capabilities',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.repositories,
    section: ResearchOSModuleSection.workspace,
    label: 'Repositories',
    icon: Icons.source_outlined,
    availability: 'adapter',
    backendSource: 'workspace + GitHub capabilities',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.github,
    section: ResearchOSModuleSection.workspace,
    label: 'GitHub',
    icon: Icons.account_tree_outlined,
    availability: 'existing',
    legacyPageIndex: 5,
    backendSource: 'features/github + /v1/github/dashboard',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.drive,
    section: ResearchOSModuleSection.workspace,
    label: 'Drive',
    icon: Icons.cloud_outlined,
    availability: 'existing',
    legacyPageIndex: 6,
    backendSource: 'features/google_workspace',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.runtime,
    section: ResearchOSModuleSection.system,
    label: 'Runtime',
    icon: Icons.dns_outlined,
    availability: 'existing',
    legacyPageIndex: 7,
    backendSource: 'features/local_api + /health',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.installer,
    section: ResearchOSModuleSection.system,
    label: 'Installer',
    icon: Icons.install_desktop_outlined,
    availability: 'planned',
    backendSource: 'installer service/scripts',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.backup,
    section: ResearchOSModuleSection.system,
    label: 'Backup',
    icon: Icons.backup_outlined,
    availability: 'planned',
    backendSource: 'backup service/scripts',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.restore,
    section: ResearchOSModuleSection.system,
    label: 'Restore',
    icon: Icons.restore_outlined,
    availability: 'planned',
    backendSource: 'restore service/scripts',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.shell,
    section: ResearchOSModuleSection.system,
    label: 'Shell',
    icon: Icons.terminal_outlined,
    availability: 'planned',
    backendSource: 'controlled local command surface',
  ),
];
