import 'package:flutter/material.dart';

class ResearchNavItem {
  const ResearchNavItem(this.section, this.label, this.icon, this.index);

  final String section;
  final String label;
  final IconData icon;
  final int index;
}

class ResearchRecentChat {
  const ResearchRecentChat({required this.id, required this.title});

  final String id;
  final String title;
}

const researchNavigationItems = <ResearchNavItem>[
  ResearchNavItem('Workspace', 'Home', Icons.home_outlined, 0),
  ResearchNavItem('Workspace', 'AI Chat', Icons.edit_square, 1),
  ResearchNavItem('Workspace', 'Agent Center', Icons.smart_toy_outlined, 2),
  ResearchNavItem('Knowledge', 'Library', Icons.local_library_outlined, 3),
  ResearchNavItem('Knowledge', 'Knowledge Graph', Icons.hub_outlined, 4),
  ResearchNavItem('Connections', 'GitHub', Icons.account_tree_outlined, 5),
  ResearchNavItem('Connections', 'Google Workspace', Icons.apps_outlined, 6),
  ResearchNavItem('System', 'Local API & Service', Icons.dns_outlined, 7),
  ResearchNavItem('System', 'System Monitor', Icons.monitor_heart_outlined, 8),
  ResearchNavItem('System', 'Settings', Icons.settings_outlined, 9),
  ResearchNavItem('Access', 'Developer Access', Icons.admin_panel_settings_outlined, 10),
];

class ResearchSidebar extends StatelessWidget {
  const ResearchSidebar({
    required this.expanded,
    required this.selectedIndex,
    required this.recentChats,
    required this.onToggle,
    required this.onSelected,
    required this.onNewChat,
    required this.onRecentChatSelected,
    super.key,
  });

  final bool expanded;
  final int selectedIndex;
  final List<ResearchRecentChat> recentChats;
  final VoidCallback onToggle;
  final ValueChanged<int> onSelected;
  final Future<void> Function() onNewChat;
  final Future<void> Function(String id) onRecentChatSelected;

  List<Widget> _entries(BuildContext context) {
    final widgets = <Widget>[];
    String? section;
    for (final item in researchNavigationItems) {
      if (expanded &&
          section == 'Workspace' &&
          item.section != section &&
          recentChats.isNotEmpty) {
        widgets.add(
          _RecentChatsSection(
            chats: recentChats,
            onSelected: onRecentChatSelected,
          ),
        );
      }
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
      curve: Curves.easeOutCubic,
      width: expanded ? 300 : 72,
      color: scheme.surfaceContainerLow,
      child: Column(
        children: <Widget>[
          SizedBox(
            height: 64,
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: expanded ? 14 : 8),
              child: Row(
                children: <Widget>[
                  if (expanded) ...<Widget>[
                    const ResearchBrandMark(),
                    const SizedBox(width: 10),
                    const Expanded(
                      child: Text(
                        'Research OS',
                        key: Key('desktop-shell-title'),
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                  ],
                  IconButton(
                    key: const Key('toggle-desktop-sidebar'),
                    tooltip: expanded ? 'ย่อ Sidebar' : 'ขยาย Sidebar',
                    onPressed: onToggle,
                    icon: Icon(
                      expanded ? Icons.menu_open_rounded : Icons.menu_rounded,
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (expanded)
            Padding(
              padding: const EdgeInsets.fromLTRB(10, 0, 10, 6),
              child: _ChatPrimaryAction(
                selected: selectedIndex == 1,
                onTap: () {
                  onNewChat();
                },
              ),
            ),
          Expanded(
            child: ListView(
              key: const Key('desktop-navigation-list'),
              padding: EdgeInsets.fromLTRB(0, expanded ? 2 : 8, 0, 8),
              children: _entries(context),
            ),
          ),
          Padding(
            padding: EdgeInsets.fromLTRB(
              expanded ? 12 : 8,
              6,
              expanded ? 12 : 8,
              12,
            ),
            child: Column(
              children: <Widget>[
                Container(
                  width: double.infinity,
                  padding: EdgeInsets.symmetric(
                    horizontal: expanded ? 12 : 8,
                    vertical: 10,
                  ),
                  decoration: BoxDecoration(
                    color: scheme.surface,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: expanded
                      ? Row(
                          children: <Widget>[
                            Icon(
                              Icons.shield_outlined,
                              size: 18,
                              color: scheme.primary,
                            ),
                            const SizedBox(width: 9),
                            const Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: <Widget>[
                                  Text(
                                    'Local-first',
                                    style: TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                  Text(
                                    'Research OS workspace',
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    style: TextStyle(fontSize: 11),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        )
                      : Icon(
                          Icons.shield_outlined,
                          size: 18,
                          color: scheme.primary,
                        ),
                ),
                if (expanded) ...<Widget>[
                  const SizedBox(height: 8),
                  const _OwnerFooter(),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ChatPrimaryAction extends StatelessWidget {
  const _ChatPrimaryAction({required this.selected, required this.onTap});

  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Material(
      color: selected ? scheme.surfaceContainerHighest : Colors.transparent,
      borderRadius: BorderRadius.circular(10),
      child: InkWell(
        key: const Key('desktop-new-chat'),
        borderRadius: BorderRadius.circular(10),
        onTap: onTap,
        child: const SizedBox(
          height: 44,
          child: Padding(
            padding: EdgeInsets.symmetric(horizontal: 12),
            child: Row(
              children: <Widget>[
                Icon(Icons.edit_square, size: 21),
                SizedBox(width: 12),
                Text(
                  'แชตใหม่',
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _RecentChatsSection extends StatelessWidget {
  const _RecentChatsSection({required this.chats, required this.onSelected});

  final List<ResearchRecentChat> chats;
  final Future<void> Function(String id) onSelected;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        const _SectionLabel('เมื่อเร็ว ๆ นี้'),
        for (final chat in chats)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 1),
            child: Material(
              color: Colors.transparent,
              borderRadius: BorderRadius.circular(10),
              child: InkWell(
                key: Key('desktop-recent-chat-${chat.id}'),
                borderRadius: BorderRadius.circular(10),
                onTap: () {
                  onSelected(chat.id);
                },
                child: SizedBox(
                  height: 36,
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 12),
                    child: Row(
                      children: <Widget>[
                        const Icon(Icons.chat_bubble_outline, size: 16),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            chat.title,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontSize: 12.5),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }
}

class _OwnerFooter extends StatelessWidget {
  const _OwnerFooter();

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return SizedBox(
      height: 44,
      child: Row(
        children: <Widget>[
          CircleAvatar(
            radius: 15,
            backgroundColor: scheme.primaryContainer,
            child: Text(
              'R',
              style: TextStyle(
                color: scheme.onPrimaryContainer,
                fontWeight: FontWeight.w800,
              ),
            ),
          ),
          const SizedBox(width: 10),
          const Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  'Research OS Owner',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
                ),
                Text('Owner workspace', style: TextStyle(fontSize: 10)),
              ],
            ),
          ),
          const Icon(Icons.more_horiz, size: 18),
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
      child: const Row(
        children: <Widget>[
          Icon(Icons.circle, size: 8),
          SizedBox(width: 6),
          Text('Research OS', style: TextStyle(fontSize: 12)),
          Spacer(),
          _StatusItem(Icons.smart_toy_outlined, 'Agents'),
          _StatusItem(Icons.memory_outlined, 'Memory'),
          _StatusItem(Icons.apps_outlined, 'Workspace'),
          _StatusItem(Icons.dns_outlined, 'Local API'),
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
        label,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
              fontWeight: FontWeight.w600,
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
      padding: EdgeInsets.symmetric(horizontal: expanded ? 10 : 8, vertical: 1),
      child: Tooltip(
        message: expanded ? '' : item.label,
        child: Material(
          color: selected ? scheme.surfaceContainerHighest : Colors.transparent,
          borderRadius: BorderRadius.circular(10),
          child: InkWell(
            key: Key('desktop-nav-${item.index}'),
            borderRadius: BorderRadius.circular(10),
            onTap: onTap,
            child: SizedBox(
              height: 40,
              child: Row(
                mainAxisAlignment:
                    expanded ? MainAxisAlignment.start : MainAxisAlignment.center,
                children: <Widget>[
                  SizedBox(
                    width: expanded ? 42 : 54,
                    child: Icon(
                      item.icon,
                      size: 20,
                      color: selected ? scheme.onSurface : scheme.onSurfaceVariant,
                    ),
                  ),
                  if (expanded)
                    Expanded(
                      child: Text(
                        item.label,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight:
                              selected ? FontWeight.w700 : FontWeight.w500,
                        ),
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
