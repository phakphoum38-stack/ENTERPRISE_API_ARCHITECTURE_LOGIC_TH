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
  ResearchNavItem('Knowledge', 'Library', Icons.local_library_outlined, 3),
  ResearchNavItem('Knowledge', 'Knowledge Graph', Icons.hub_outlined, 4),
  ResearchNavItem('Connections', 'GitHub', Icons.account_tree_outlined, 5),
  ResearchNavItem('Connections', 'Google Workspace', Icons.apps_outlined, 6),
  ResearchNavItem('System', 'Local API & Service', Icons.dns_outlined, 7),
  ResearchNavItem('System', 'System Monitor', Icons.monitor_heart_outlined, 8),
  ResearchNavItem('System', 'Settings', Icons.settings_outlined, 9),
];

class ResearchSidebar extends StatelessWidget {
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
      duration: const Duration(milliseconds: 180),
      width: expanded ? 244 : 76,
      color: scheme.surface,
      child: Column(
        children: <Widget>[
          SizedBox(
            height: 72,
            child: expanded
                ? Padding(
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
                  )
                : Center(
                    child: IconButton(
                      key: const Key('toggle-desktop-sidebar'),
                      tooltip: 'ขยาย Sidebar',
                      onPressed: onToggle,
                      icon: const Icon(Icons.chevron_right),
                    ),
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
            title: Text(item.label),
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
      child: Row(
        children: <Widget>[
          Icon(Icons.circle, size: 8, color: scheme.primary),
          const SizedBox(width: 6),
          const Text('Research OS', style: TextStyle(fontSize: 12)),
          const Spacer(),
          const _StatusItem(Icons.smart_toy_outlined, 'Agents'),
          const _StatusItem(Icons.memory_outlined, 'Memory'),
          const _StatusItem(Icons.apps_outlined, 'Workspace'),
          const _StatusItem(Icons.dns_outlined, 'Local API'),
        ],
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
  const _StatusItem(this.icon, this.label);
  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(left: 16),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Icon(icon, size: 15),
          const SizedBox(width: 5),
          Text(label, style: const TextStyle(fontSize: 11)),
        ],
      ),
    );
  }
}
