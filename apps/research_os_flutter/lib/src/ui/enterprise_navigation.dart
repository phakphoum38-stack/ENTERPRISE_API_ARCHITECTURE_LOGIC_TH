import 'package:flutter/material.dart';

class ResearchNavItem {
  const ResearchNavItem(
    this.section,
    this.label,
    this.icon,
    this.index, {
    required this.destinationId,
    this.capabilityId,
  });

  final String section;
  final String label;
  final IconData icon;
  final int index;
  final String destinationId;

  /// Canonical cross-layer capability identity when this destination is
  /// already bound to an existing capability contract. Null means the
  /// destination is currently shell-only or its capability binding is still
  /// being migrated; it does not grant authority by itself.
  final String? capabilityId;
}

const researchNavigationItems = <ResearchNavItem>[
  ResearchNavItem('Workspace', 'Home', Icons.dashboard_outlined, 0, destinationId: 'home'),
  ResearchNavItem('Workspace', 'AI Chat', Icons.chat_bubble_outline, 1, destinationId: 'ai_chat'),
  ResearchNavItem('Workspace', 'Agent Center', Icons.smart_toy_outlined, 2, destinationId: 'agent_center'),
  ResearchNavItem('AI', 'Brain Skills', Icons.psychology_alt_outlined, 11, destinationId: 'brain_skills'),
  ResearchNavItem('Knowledge', 'Library', Icons.local_library_outlined, 3, destinationId: 'library'),
  ResearchNavItem('Knowledge', 'Knowledge Graph', Icons.hub_outlined, 4, destinationId: 'knowledge_graph'),
  ResearchNavItem('Connections', 'GitHub', Icons.account_tree_outlined, 5, destinationId: 'github'),
  ResearchNavItem('Connections', 'Google Workspace', Icons.apps_outlined, 6, destinationId: 'google_workspace'),
  ResearchNavItem('Connections', 'Friend Connect', Icons.support_agent_outlined, 13, destinationId: 'friend_connect'),
  ResearchNavItem('System', 'Local API & Service', Icons.dns_outlined, 7, destinationId: 'local_api_service'),
  ResearchNavItem('System', 'System Monitor', Icons.monitor_heart_outlined, 8, destinationId: 'system_monitor'),
  ResearchNavItem('System', 'Settings', Icons.settings_outlined, 9, destinationId: 'settings'),
  ResearchNavItem('Access', 'Developer Access', Icons.admin_panel_settings_outlined, 10, destinationId: 'developer_access'),
  ResearchNavItem('Account', 'Google Sign-In', Icons.account_circle_outlined, 12, destinationId: 'google_sign_in'),
  ResearchNavItem('Workspace', 'Projects', Icons.workspaces_outlined, 14, destinationId: 'projects'),
  ResearchNavItem('Workspace', 'Workflows', Icons.account_tree_outlined, 15, destinationId: 'workflows'),
  ResearchNavItem(
    'Control',
    'Control Center',
    Icons.tune_outlined,
    16,
    capabilityId: 'control_center',
    destinationId: 'control_center',
  ),
  ResearchNavItem(
    'System',
    'Owner',
    Icons.shield_outlined,
    17,
    capabilityId: 'owner',
    destinationId: 'owner',
  ),
];

class ResearchSidebar extends StatelessWidget {
  static const compactWidth = 76.0;
  static const expandedWidth = 244.0;
  static const animationDuration = Duration(milliseconds: 220);

  const ResearchSidebar({
    required this.expanded,
    required this.selectedIndex,
    required this.onToggle,
    required this.onSelected,
    super.key,
  });

  final bool expanded;
  final int selectedIndex;
  final VoidCallback onToggle;
  final ValueChanged<int> onSelected;

  List<Widget> _entries(BuildContext context) {
    final widgets = <Widget>[];
    String? section;
    for (final item in researchNavigationItems) {
      if (expanded && section != item.section) {
        section = item.section;
        widgets.add(_SectionLabel(section));
      }
      widgets.add(
        _SidebarDestination(
          item: item,
          expanded: expanded,
          selected: selectedIndex == item.index,
          onTap: () => onSelected(item.index),
        ),
      );
    }
    return widgets;
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return AnimatedContainer(
      key: const Key('enterprise-sidebar'),
      duration: animationDuration,
      curve: Curves.easeOutCubic,
      width: expanded ? expandedWidth : compactWidth,
      color: scheme.surface,
      child: Column(
        children: <Widget>[
          SizedBox(
            height: 72,
            child: LayoutBuilder(
              builder: (context, constraints) {
                final showExpandedHeader =
                    expanded && constraints.maxWidth >= 200;
                if (showExpandedHeader) {
                  return Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 14),
                    child: Row(
                      children: <Widget>[
                        const ResearchBrandMark(),
                        const SizedBox(width: 10),
                        const Expanded(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: <Widget>[
                              Text(
                                'Research OS',
                                key: Key('desktop-shell-title'),
                                style: TextStyle(fontWeight: FontWeight.w800),
                              ),
                              Text('Enterprise Workspace', style: TextStyle(fontSize: 11)),
                            ],
                          ),
                        ),
                        IconButton(
                          key: Key('toggle-desktop-sidebar'),
                          tooltip: 'ย่อ Sidebar',
                          onPressed: onToggle,
                          icon: Icon(Icons.chevron_left),
                        ),
                      ],
                    ),
                  );
                }
                return Center(
                  child: IconButton(
                    key: const Key('toggle-desktop-sidebar'),
                    tooltip: 'ขยาย Sidebar',
                    onPressed: onToggle,
                    icon: const Icon(Icons.chevron_right),
                  ),
                );
              },
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: ListView(
              key: const Key('desktop-navigation-list'),
              padding: const EdgeInsets.symmetric(vertical: 8),
              children: _entries(context),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Container(
              height: 40,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: scheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(12),
              ),
              child: expanded
                  ? Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: <Widget>[
                        Icon(Icons.shield_outlined, size: 16, color: scheme.primary),
                        const SizedBox(width: 8),
                        const Flexible(
                          child: Text(
                            'Local-first & secure',
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(fontSize: 12),
                          ),
                        ),
                      ],
                    )
                  : Icon(Icons.shield_outlined, size: 16, color: scheme.primary),
            ),
          ),
        ],
      ),
    );
  }
}

class ResearchMobileDrawer extends StatelessWidget {
  const ResearchMobileDrawer({
    required this.selectedIndex,
    required this.onSelected,
    super.key,
  });

  final int selectedIndex;
  final ValueChanged<int> onSelected;

  List<Widget> _entries(BuildContext context) {
    final widgets = <Widget>[];
    String? section;
    for (final item in researchNavigationItems) {
      if (section != item.section) {
        section = item.section;
        widgets.add(_SectionLabel(section));
      }
      widgets.add(
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
          child: ListTile(
            key: Key('mobile-nav-${item.index}'),
            selected: selectedIndex == item.index,
            leading: Icon(item.icon),
            title: Text(
              item.label,
              key: Key('mobile-nav-label-${item.index}'),
            ),
            onTap: () => onSelected(item.index),
          ),
        ),
      );
    }
    return widgets;
  }

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: SafeArea(
        child: Column(
          children: <Widget>[
            const Padding(
              padding: EdgeInsets.all(20),
              child: Row(
                children: <Widget>[
                  ResearchBrandMark(),
                  SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'Research OS',
                      style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800),
                    ),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(vertical: 8),
                children: _entries(context),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class ResearchBrandMark extends StatelessWidget {
  const ResearchBrandMark({this.compact = false, super.key});

  final bool compact;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      width: compact ? 30 : 36,
      height: compact ? 30 : 36,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: scheme.primaryContainer,
        borderRadius: BorderRadius.circular(11),
      ),
      child: Text(
        'R',
        style: TextStyle(
          color: scheme.onPrimaryContainer,
          fontWeight: FontWeight.w900,
          fontSize: compact ? 15 : 18,
        ),
      ),
    );
  }
}

class ResearchStatusBar extends StatelessWidget {
  const ResearchStatusBar({super.key});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      key: const Key('desktop-status-bar'),
      height: 30,
      padding: const EdgeInsets.symmetric(horizontal: 14),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerLow,
        border: Border(top: BorderSide(color: Theme.of(context).dividerColor)),
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final compact = constraints.maxWidth < 430;
          final statusItems = compact
              ? const <Widget>[
                  _StatusItem(Icons.smart_toy_outlined, 'Agents', compact: true),
                  _StatusItem(Icons.memory_outlined, 'Memory', compact: true),
                  _StatusItem(Icons.apps_outlined, 'Workspace', compact: true),
                  _StatusItem(Icons.dns_outlined, 'Local API', compact: true),
                ]
              : const <Widget>[
                  _StatusItem(Icons.smart_toy_outlined, 'Agents'),
                  _StatusItem(Icons.memory_outlined, 'Memory'),
                  _StatusItem(Icons.apps_outlined, 'Workspace'),
                  _StatusItem(Icons.dns_outlined, 'Local API'),
                ];
          return Row(
            children: <Widget>[
              Icon(Icons.circle, size: 8, color: scheme.primary),
              const SizedBox(width: 6),
              const Flexible(
                child: Text(
                  'Research OS',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontSize: 12),
                ),
              ),
              const Spacer(),
              ...statusItems,
            ],
          );
        },
      ),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  const _SectionLabel(this.label);
  final String label;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 6),
      child: Text(
        label.toUpperCase(),
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
              fontWeight: FontWeight.w700,
              letterSpacing: .7,
            ),
      ),
    );
  }
}

class _SidebarDestination extends StatelessWidget {
  const _SidebarDestination({
    required this.item,
    required this.expanded,
    required this.selected,
    required this.onTap,
  });

  final ResearchNavItem item;
  final bool expanded;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: expanded ? 10 : 8, vertical: 2),
      child: Tooltip(
        message: expanded ? '' : item.label,
        child: Material(
          color: selected ? scheme.secondaryContainer : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
          child: InkWell(
            key: Key('desktop-nav-${item.index}'),
            borderRadius: BorderRadius.circular(12),
            onTap: onTap,
            child: SizedBox(
              height: 44,
              child: Row(
                mainAxisAlignment: expanded ? MainAxisAlignment.start : MainAxisAlignment.center,
                children: <Widget>[
                  SizedBox(
                    width: expanded ? 44 : 58,
                    child: Icon(
                      item.icon,
                      color: selected ? scheme.onSecondaryContainer : scheme.onSurfaceVariant,
                    ),
                  ),
                  if (expanded)
                    Expanded(
                      child: Text(
                        item.label,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(fontWeight: selected ? FontWeight.w700 : FontWeight.w500),
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _StatusItem extends StatelessWidget {
  const _StatusItem(this.icon, this.label, {this.compact = false});
  final IconData icon;
  final String label;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 10),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(icon, size: 15),
          if (!compact) ...<Widget>[
            const SizedBox(width: 5),
            Text(label, style: const TextStyle(fontSize: 11)),
          ],
        ],
      ),
    );
  }
}
