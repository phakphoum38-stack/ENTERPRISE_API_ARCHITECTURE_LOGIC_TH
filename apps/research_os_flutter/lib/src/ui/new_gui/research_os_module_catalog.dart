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

  /// `existing` means a real feature/runtime path is wired to the GUI.
  /// `adapter` means the capability exists but still needs a dedicated surface.
  /// `planned` means implementation evidence still needs to be established.
  final String availability;

  /// Existing page index from the classic ResearchOSAppShell when available.
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
    availability: 'existing',
    backendSource: 'ResearchMemoryModulePage + /v1/memory/search',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.skills,
    section: ResearchOSModuleSection.main,
    label: 'Skills',
    icon: Icons.psychology_alt_outlined,
    availability: 'existing',
    backendSource: '/v1/skills -> Owner/Friend SkillRegistry',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.tools,
    section: ResearchOSModuleSection.main,
    label: 'Tools',
    icon: Icons.build_circle_outlined,
    availability: 'existing',
    backendSource: '/v1/tools -> Owner/Friend ToolRegistry',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.factory,
    section: ResearchOSModuleSection.main,
    label: 'Factory',
    icon: Icons.account_tree_outlined,
    availability: 'existing',
    backendSource:
        'AgentCenterPage + /v1/agents/orchestrations create/execute/confirm/retry/cancel/timeline',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.providers,
    section: ResearchOSModuleSection.main,
    label: 'Providers',
    icon: Icons.hub_outlined,
    availability: 'existing',
    backendSource: 'ResearchProvidersModulePage + /v1/providers',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.files,
    section: ResearchOSModuleSection.workspace,
    label: 'Files',
    icon: Icons.folder_outlined,
    availability: 'existing',
    backendSource: 'LibraryPage + workspace/library services',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.repositories,
    section: ResearchOSModuleSection.workspace,
    label: 'Repositories',
    icon: Icons.source_outlined,
    availability: 'existing',
    backendSource: 'GitHubDashboardPage + /v1/github/dashboard',
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
    availability: 'existing',
    backendSource:
        'LocalApiManager -> installer/output/Research-OS-Setup-*-x64.exe',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.backup,
    section: ResearchOSModuleSection.system,
    label: 'Backup',
    icon: Icons.backup_outlined,
    availability: 'existing',
    backendSource: 'LocalApiManager -> scripts/backup-research-os.ps1',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.restore,
    section: ResearchOSModuleSection.system,
    label: 'Restore',
    icon: Icons.restore_outlined,
    availability: 'existing',
    backendSource: 'LocalApiManager -> scripts/restore-research-os.ps1',
  ),
  ResearchOSModuleDefinition(
    id: ResearchOSModuleId.shell,
    section: ResearchOSModuleSection.system,
    label: 'Shell',
    icon: Icons.terminal_outlined,
    availability: 'existing',
    backendSource:
        'LocalApiManager -> current-user powershell.exe command surface',
  ),
];
