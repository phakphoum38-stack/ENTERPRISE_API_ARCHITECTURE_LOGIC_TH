import 'package:flutter/material.dart';

class ResearchNavItem {
  const ResearchNavItem(this.section, this.label, this.icon, this.index);

  final String section;
  final String label;
  final IconData icon;
  final int index;
}

const researchNavigationItems = <ResearchNavItem>[
  ResearchNavItem('Workspace', 'Home', Icons.dashboard_outlined, 0),
  ResearchNavItem('Workspace', 'AI Chat', Icons.chat_bubble_outline, 1),
  ResearchNavItem('Workspace', 'Agent Center', Icons.smart_toy_outlined, 2),
  ResearchNavItem('AI', 'Brain Skills', Icons.psychology_alt_outlined, 11),
  ResearchNavItem('Knowledge', 'Library', Icons.local_library_outlined, 3),
  ResearchNavItem('Knowledge', 'Knowledge Graph', Icons.hub_outlined, 4),
  ResearchNavItem('Connections', 'GitHub', Icons.account_tree_outlined, 5),
  ResearchNavItem('Connections', 'Google Workspace', Icons.apps_outlined, 6),
  ResearchNavItem('System', 'Local API & Service', Icons.dns_outlined, 7),
  ResearchNavItem('System', 'System Monitor', Icons.monitor_heart_outlined, 8),
  ResearchNavItem('System', 'Settings', Icons.settings_outlined, 9),
  ResearchNavItem('Access', 'Developer Access', Icons.admin_panel_settings_outlined, 10),
  ResearchNavItem('Account', 'Google Sign-In', Icons.account_circle_outlined, 12),
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
          Expanded(child: ListView(children: _entries(context))),
        ],
      ),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  const _SectionLabel(this.label);
  final String label;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.fromLTRB(18, 12, 18, 5),
        child: Text(
          label.toUpperCase(),
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
                fontWeight: FontWeight.w800,
                letterSpacing: .8,
              ),
        ),
      );
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
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      child: Material(
        color: selected ? scheme.secondaryContainer : Colors.transparent,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: SizedBox(
            height: 44,
            child: Row(
              children: <Widget>[
                SizedBox(
                  width: expanded ? 44 : 60,
                  child: Icon(item.icon, color: selected ? scheme.onSecondaryContainer : scheme.onSurfaceVariant),
                ),
                if (expanded)
                  Expanded(
                    child: Text(
                      item.label,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(fontWeight: selected ? FontWeight.w700 : FontWeight.w500),
                    ),
                  ),
              ],
            ),
          ),
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
      width: compact ? 30 : 38,
      height: compact ? 30 : 38,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: <Color>[scheme.primaryContainer, scheme.secondaryContainer]),
        borderRadius: BorderRadius.circular(compact ? 9 : 12),
      ),
      child: Text('R', style: TextStyle(color: scheme.onPrimaryContainer, fontWeight: FontWeight.w900)),
    );
  }
}

class ResearchStatusBar extends StatelessWidget {
  const ResearchStatusBar({super.key});
  @override
  Widget build(BuildContext context) => const SizedBox(height: 0);
}

class ResearchMobileDrawer extends StatelessWidget {
  const ResearchMobileDrawer({required this.selectedIndex, required this.onSelected, super.key});
  final int selectedIndex;
  final ValueChanged<int> onSelected;
  @override
  Widget build(BuildContext context) => Drawer(
        child: ListView(children: <Widget>[
          const DrawerHeader(child: Text('Research OS')),
          for (final item in researchNavigationItems)
            ListTile(
              selected: selectedIndex == item.index,
              leading: Icon(item.icon),
              title: Text(item.label),
              onTap: () => onSelected(item.index),
            ),
        ]),
      );
}
