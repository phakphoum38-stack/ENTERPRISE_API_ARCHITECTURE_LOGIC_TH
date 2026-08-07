import 'package:flutter/material.dart';

import 'api/research_os_api_client.dart';
import 'features/chat/chat_page.dart';
import 'features/github/github_dashboard_page.dart';
import 'features/graph/knowledge_graph_page.dart';
import 'features/home/home_page.dart';
import 'features/library/library_page.dart';
import 'features/monitor/system_monitor_page.dart';
import 'features/settings/settings_page.dart';

class ResearchOSAppShell extends StatefulWidget {
  const ResearchOSAppShell({
    required this.apiClient,
    this.themeMode = ThemeMode.system,
    this.onThemeModeChanged,
    super.key,
  });

  final ResearchOSApiClient apiClient;
  final ThemeMode themeMode;
  final ValueChanged<ThemeMode>? onThemeModeChanged;

  @override
  State<ResearchOSAppShell> createState() => _ResearchOSAppShellState();
}

class _ResearchOSAppShellState extends State<ResearchOSAppShell> {
  int _selectedIndex = 0;
  bool _railExtended = true;

  static const _workspaceTitles = <String>[
    'Home Dashboard',
    'AI Workspace',
    'Knowledge Library',
    'Knowledge Graph',
    'GitHub Control Center',
    'System Monitor',
    'Settings & Providers',
  ];

  @override
  void dispose() {
    widget.apiClient.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final pages = <Widget>[
      HomePage(apiClient: widget.apiClient),
      ChatPage(apiClient: widget.apiClient),
      LibraryPage(apiClient: widget.apiClient),
      KnowledgeGraphPage(apiClient: widget.apiClient),
      GitHubDashboardPage(apiClient: widget.apiClient),
      SystemMonitorPage(apiClient: widget.apiClient),
      SettingsPage(
        apiClient: widget.apiClient,
        themeMode: widget.themeMode,
        onThemeModeChanged:
            widget.onThemeModeChanged ?? (ThemeMode value) {},
      ),
    ];

    const railDestinations = <NavigationRailDestination>[
      NavigationRailDestination(
        icon: Icon(Icons.home_outlined),
        selectedIcon: Icon(Icons.home),
        label: Text('บ้าน'),
      ),
      NavigationRailDestination(
        icon: Icon(Icons.chat_bubble_outline),
        selectedIcon: Icon(Icons.chat_bubble),
        label: Text('AI Chat'),
      ),
      NavigationRailDestination(
        icon: Icon(Icons.local_library_outlined),
        selectedIcon: Icon(Icons.local_library),
        label: Text('ห้องสมุด'),
      ),
      NavigationRailDestination(
        icon: Icon(Icons.hub_outlined),
        selectedIcon: Icon(Icons.hub),
        label: Text('แผนผัง'),
      ),
      NavigationRailDestination(
        icon: Icon(Icons.account_tree_outlined),
        selectedIcon: Icon(Icons.account_tree),
        label: Text('GitHub'),
      ),
      NavigationRailDestination(
        icon: Icon(Icons.monitor_heart_outlined),
        selectedIcon: Icon(Icons.monitor_heart),
        label: Text('ระบบ'),
      ),
      NavigationRailDestination(
        icon: Icon(Icons.settings_outlined),
        selectedIcon: Icon(Icons.settings),
        label: Text('ตั้งค่า'),
      ),
    ];

    const barDestinations = <NavigationDestination>[
      NavigationDestination(
        icon: Icon(Icons.home_outlined),
        selectedIcon: Icon(Icons.home),
        label: 'บ้าน',
      ),
      NavigationDestination(
        icon: Icon(Icons.chat_bubble_outline),
        selectedIcon: Icon(Icons.chat_bubble),
        label: 'AI Chat',
      ),
      NavigationDestination(
        icon: Icon(Icons.local_library_outlined),
        selectedIcon: Icon(Icons.local_library),
        label: 'ห้องสมุด',
      ),
      NavigationDestination(
        icon: Icon(Icons.hub_outlined),
        selectedIcon: Icon(Icons.hub),
        label: 'แผนผัง',
      ),
      NavigationDestination(
        icon: Icon(Icons.account_tree_outlined),
        selectedIcon: Icon(Icons.account_tree),
        label: 'GitHub',
      ),
      NavigationDestination(
        icon: Icon(Icons.monitor_heart_outlined),
        selectedIcon: Icon(Icons.monitor_heart),
        label: 'ระบบ',
      ),
      NavigationDestination(
        icon: Icon(Icons.settings_outlined),
        selectedIcon: Icon(Icons.settings),
        label: 'ตั้งค่า',
      ),
    ];

    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 900) {
          return Scaffold(
            body: SafeArea(
              child: Column(
                children: <Widget>[
                  _DesktopTopBar(
                    title: _workspaceTitles[_selectedIndex],
                    railExtended: _railExtended,
                    onToggleRail: () {
                      setState(() => _railExtended = !_railExtended);
                    },
                  ),
                  const Divider(height: 1),
                  Expanded(
                    child: Row(
                      children: <Widget>[
                        NavigationRail(
                          key: const Key('desktop-navigation-rail'),
                          extended: _railExtended,
                          selectedIndex: _selectedIndex,
                          labelType: _railExtended
                              ? NavigationRailLabelType.none
                              : NavigationRailLabelType.all,
                          leading: const Padding(
                            padding: EdgeInsets.only(bottom: 8),
                            child: Icon(Icons.auto_awesome, size: 28),
                          ),
                          onDestinationSelected: (value) {
                            setState(() => _selectedIndex = value);
                          },
                          destinations: railDestinations,
                        ),
                        const VerticalDivider(width: 1),
                        Expanded(
                          child: Column(
                            children: <Widget>[
                              Expanded(
                                child: IndexedStack(
                                  index: _selectedIndex,
                                  children: pages,
                                ),
                              ),
                              const _DesktopStatusBar(),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          );
        }

        return Scaffold(
          appBar: AppBar(
            title: Text(_workspaceTitles[_selectedIndex]),
            actions: <Widget>[
              IconButton(
                tooltip: 'System Monitor',
                onPressed: () => setState(() => _selectedIndex = 5),
                icon: const Icon(Icons.monitor_heart_outlined),
              ),
            ],
          ),
          body: IndexedStack(index: _selectedIndex, children: pages),
          bottomNavigationBar: NavigationBar(
            selectedIndex: _selectedIndex,
            onDestinationSelected: (value) {
              setState(() => _selectedIndex = value);
            },
            destinations: barDestinations,
          ),
        );
      },
    );
  }
}

class _DesktopTopBar extends StatelessWidget {
  const _DesktopTopBar({
    required this.title,
    required this.railExtended,
    required this.onToggleRail,
  });

  final String title;
  final bool railExtended;
  final VoidCallback onToggleRail;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 56,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12),
        child: Row(
          children: <Widget>[
            IconButton(
              key: const Key('toggle-desktop-sidebar'),
              tooltip: railExtended ? 'ย่อ Sidebar' : 'ขยาย Sidebar',
              onPressed: onToggleRail,
              icon: Icon(
                railExtended ? Icons.menu_open : Icons.menu,
              ),
            ),
            const SizedBox(width: 8),
            const Icon(Icons.hub_outlined),
            const SizedBox(width: 10),
            const Text(
              'Research OS Desktop',
              key: Key('desktop-shell-title'),
              style: TextStyle(fontWeight: FontWeight.w700),
            ),
            const SizedBox(width: 16),
            Container(width: 1, height: 24, color: Theme.of(context).dividerColor),
            const SizedBox(width: 16),
            Expanded(
              child: Text(
                title,
                key: const Key('desktop-workspace-title'),
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.titleMedium,
              ),
            ),
            const Tooltip(
              message: 'Backend secrets stay on the Research OS API',
              child: Icon(Icons.shield_outlined),
            ),
          ],
        ),
      ),
    );
  }
}

class _DesktopStatusBar extends StatelessWidget {
  const _DesktopStatusBar();

  @override
  Widget build(BuildContext context) {
    return Container(
      key: const Key('desktop-status-bar'),
      height: 28,
      padding: const EdgeInsets.symmetric(horizontal: 12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        border: Border(top: BorderSide(color: Theme.of(context).dividerColor)),
      ),
      child: const Row(
        children: <Widget>[
          Icon(Icons.circle, size: 9),
          SizedBox(width: 6),
          Text('Research OS Workspace'),
          Spacer(),
          Icon(Icons.memory, size: 16),
          SizedBox(width: 4),
          Text('Memory'),
          SizedBox(width: 14),
          Icon(Icons.cloud_outlined, size: 16),
          SizedBox(width: 4),
          Text('API'),
        ],
      ),
    );
  }
}
