import 'package:flutter/material.dart';

import 'api/research_os_api_client.dart';
import 'features/agents/agent_center_page.dart';
import 'features/chat/chat_page.dart';
import 'features/github/github_dashboard_page.dart';
import 'features/google_workspace/google_workspace_page.dart';
import 'features/graph/knowledge_graph_page.dart';
import 'features/home/home_page.dart';
import 'features/library/library_page.dart';
import 'features/local_api/local_api_control_page.dart';
import 'features/monitor/system_monitor_page.dart';
import 'features/settings/settings_page.dart';

class ResearchOSAppShell extends StatefulWidget {
  const ResearchOSAppShell({
    required this.apiClient,
    this.themeMode = ThemeMode.system,
    this.onThemeModeChanged,
    this.onApiBaseUrlChanged,
    super.key,
  });

  final ResearchOSApiClient apiClient;
  final ThemeMode themeMode;
  final ValueChanged<ThemeMode>? onThemeModeChanged;
  final Future<void> Function(String value)? onApiBaseUrlChanged;

  @override
  State<ResearchOSAppShell> createState() => _ResearchOSAppShellState();
}

class _ResearchOSAppShellState extends State<ResearchOSAppShell> {
  int _selectedIndex = 0;
  bool _sidebarExpanded = true;

  static const _items = <_NavItem>[
    _NavItem('Workspace', 'Home', Icons.dashboard_outlined, 0),
    _NavItem('Workspace', 'AI Chat', Icons.chat_bubble_outline, 1),
    _NavItem('Workspace', 'Agent Center', Icons.smart_toy_outlined, 2),
    _NavItem('Knowledge', 'Library', Icons.local_library_outlined, 3),
    _NavItem('Knowledge', 'Knowledge Graph', Icons.hub_outlined, 4),
    _NavItem('Connections', 'GitHub', Icons.account_tree_outlined, 5),
    _NavItem('Connections', 'Google Workspace', Icons.apps_outlined, 6),
    _NavItem('System', 'Local API & Service', Icons.dns_outlined, 7),
    _NavItem('System', 'System Monitor', Icons.monitor_heart_outlined, 8),
    _NavItem('System', 'Settings', Icons.settings_outlined, 9),
  ];

  List<Widget> get _pages => <Widget>[
        HomePage(apiClient: widget.apiClient),
        ChatPage(apiClient: widget.apiClient),
        const AgentCenterPage(),
        LibraryPage(apiClient: widget.apiClient),
        KnowledgeGraphPage(apiClient: widget.apiClient),
        GitHubDashboardPage(apiClient: widget.apiClient),
        GoogleWorkspacePage(apiClient: widget.apiClient),
        const LocalApiControlPage(),
        SystemMonitorPage(apiClient: widget.apiClient),
        SettingsPage(
          apiClient: widget.apiClient,
          themeMode: widget.themeMode,
          onThemeModeChanged:
              widget.onThemeModeChanged ?? (ThemeMode value) {},
          onApiBaseUrlChanged: widget.onApiBaseUrlChanged,
        ),
      ];

  void _select(int index) => setState(() => _selectedIndex = index);

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 920) {
          return Scaffold(
            body: SafeArea(
              child: Row(
                children: <Widget>[
                  _EnterpriseSidebar(
                    expanded: _sidebarExpanded,
                    selectedIndex: _selectedIndex,
                    onToggle: () =>
                        setState(() => _sidebarExpanded = !_sidebarExpanded),
                    onSelected: _select,
                  ),
                  VerticalDivider(
                    width: 1,
                    thickness: 1,
                    color: Theme.of(context).dividerColor,
                  ),
                  Expanded(
                    child: Column(
                      children: <Widget>[
                        Expanded(
                          child: IndexedStack(
                            index: _selectedIndex,
                            children: _pages,
                          ),
                        ),
                        const _DesktopStatusBar(),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          );
        }

        return Scaffold(
          drawer: _MobileDrawer(
            selectedIndex: _selectedIndex,
            onSelected: (index) {
              Navigator.of(context).pop();
              _select(index);
            },
          ),
          appBar: AppBar(
            titleSpacing: 0,
            title: Row(
              children: <Widget>[
                const _BrandMark(compact: true),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    _items.firstWhere((item) => item.index == _selectedIndex).label,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            actions: <Widget>[
              IconButton(
                tooltip: 'System Monitor',
                onPressed: () => _select(8),
                icon: const Icon(Icons.monitor_heart_outlined),
              ),
            ],
          ),
          body: IndexedStack(index: _selectedIndex, children: _pages),
        );
      },
    );
  }
}

class _EnterpriseSidebar extends StatelessWidget {
  const _EnterpriseSidebar({
    required this.expanded,
    required this.selectedIndex,
    required this.onToggle,
    required this.onSelected,
  });

  final bool expanded;
  final int selectedIndex;
  final VoidCallback onToggle;
  final ValueChanged<int> onSelected;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final width = expanded ? 244.0 : 76.0;
    String? lastSection;

    return AnimatedContainer(
      key: const Key('enterprise-sidebar'),
      duration: const Duration(milliseconds: 180),
      width: width,
      color: scheme.surface,
      child: Column(
        children: <Widget>[
          SizedBox(
            height: 72,
            child: Padding(
              padding: EdgeInsets.symmetric(horizontal: expanded ? 16 : 12),
              child: Row(
                children: <Widget>[
                  const _BrandMark(),
                  if (expanded) ...<Widget>[
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
                          SizedBox(height: 2),
                          Text(
                            'Enterprise Workspace',
                            style: TextStyle(fontSize: 11),
                          ),
                        ],
                      ),
                    ),
                  ],
                  IconButton(
                    key: const Key('toggle-desktop-sidebar'),
                    tooltip: expanded ? 'ย่อ Sidebar' : 'ขยาย Sidebar',
                    onPressed: onToggle,
                    icon: Icon(expanded ? Icons.chevron_left : Icons.chevron_right),
                  ),
                ],
              ),
            ),
          ),
          Divider(height: 1, color: Theme.of(context).dividerColor),
          Expanded(
            child: ListView(
              key: const Key('desktop-navigation-list'),
              padding: const EdgeInsets.symmetric(vertical: 10),
              children: <Widget>[
                for (final item in _ResearchOSAppShellState._items) ...<Widget>[
                  if (expanded && lastSection != item.section)
                    Builder(
                      builder: (context) {
                        lastSection = item.section;
                        return Padding(
                          padding: const EdgeInsets.fromLTRB(18, 14, 18, 6),
                          child: Text(
                            item.section.toUpperCase(),
                            style: Theme.of(context).textTheme.labelSmall?.copyWith(
                                  color: scheme.onSurfaceVariant,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: .7,
                                ),
                          ),
                        );
                      },
                    ),
                  Padding(
                    padding: EdgeInsets.symmetric(
                      horizontal: expanded ? 10 : 8,
                      vertical: 2,
                    ),
                    child: Tooltip(
                      message: expanded ? '' : item.label,
                      child: Material(
                        color: selectedIndex == item.index
                            ? scheme.secondaryContainer
                            : Colors.transparent,
                        borderRadius: BorderRadius.circular(12),
                        child: InkWell(
                          borderRadius: BorderRadius.circular(12),
                          onTap: () => onSelected(item.index),
                          child: SizedBox(
                            height: 44,
                            child: Row(
                              mainAxisAlignment: expanded
                                  ? MainAxisAlignment.start
                                  : MainAxisAlignment.center,
                              children: <Widget>[
                                SizedBox(
                                  width: expanded ? 44 : 58,
                                  child: Icon(
                                    item.icon,
                                    color: selectedIndex == item.index
                                        ? scheme.onSecondaryContainer
                                        : scheme.onSurfaceVariant,
                                  ),
                                ),
                                if (expanded)
                                  Expanded(
                                    child: Text(
                                      item.label,
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: TextStyle(
                                        fontWeight: selectedIndex == item.index
                                            ? FontWeight.w700
                                            : FontWeight.w500,
                                      ),
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
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Container(
              height: 40,
              decoration: BoxDecoration(
                color: scheme.surfaceContainerHighest,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: <Widget>[
                  Icon(Icons.shield_outlined, size: 16, color: scheme.primary),
                  if (expanded) ...<Widget>[
                    const SizedBox(width: 8),
                    const Text('Local-first & secure', style: TextStyle(fontSize: 12)),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MobileDrawer extends StatelessWidget {
  const _MobileDrawer({required this.selectedIndex, required this.onSelected});

  final int selectedIndex;
  final ValueChanged<int> onSelected;

  @override
  Widget build(BuildContext context) {
    String? lastSection;
    return Drawer(
      child: SafeArea(
        child: Column(
          children: <Widget>[
            const Padding(
              padding: EdgeInsets.all(20),
              child: Row(
                children: <Widget>[
                  _BrandMark(),
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
                children: <Widget>[
                  for (final item in _ResearchOSAppShellState._items) ...<Widget>[
                    if (lastSection != item.section)
                      Builder(
                        builder: (context) {
                          lastSection = item.section;
                          return Padding(
                            padding: const EdgeInsets.fromLTRB(20, 18, 20, 6),
                            child: Text(
                              item.section.toUpperCase(),
                              style: Theme.of(context).textTheme.labelSmall,
                            ),
                          );
                        },
                      ),
                    ListTile(
                      selected: selectedIndex == item.index,
                      leading: Icon(item.icon),
                      title: Text(item.label),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      onTap: () => onSelected(item.index),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _BrandMark extends StatelessWidget {
  const _BrandMark({this.compact = false});

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

class _DesktopStatusBar extends StatelessWidget {
  const _DesktopStatusBar();

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

class _NavItem {
  const _NavItem(this.section, this.label, this.icon, this.index);

  final String section;
  final String label;
  final IconData icon;
  final int index;
}
