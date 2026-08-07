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
        onThemeModeChanged: widget.onThemeModeChanged ?? (ThemeMode value) {},
      ),
    ];

    const railDestinations = <NavigationRailDestination>[
      NavigationRailDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: Text('บ้าน')),
      NavigationRailDestination(icon: Icon(Icons.chat_bubble_outline), selectedIcon: Icon(Icons.chat_bubble), label: Text('AI Chat')),
      NavigationRailDestination(icon: Icon(Icons.local_library_outlined), selectedIcon: Icon(Icons.local_library), label: Text('ห้องสมุด')),
      NavigationRailDestination(icon: Icon(Icons.hub_outlined), selectedIcon: Icon(Icons.hub), label: Text('แผนผัง')),
      NavigationRailDestination(icon: Icon(Icons.account_tree_outlined), selectedIcon: Icon(Icons.account_tree), label: Text('GitHub')),
      NavigationRailDestination(icon: Icon(Icons.monitor_heart_outlined), selectedIcon: Icon(Icons.monitor_heart), label: Text('ระบบ')),
      NavigationRailDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings), label: Text('ตั้งค่า')),
    ];

    const barDestinations = <NavigationDestination>[
      NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'บ้าน'),
      NavigationDestination(icon: Icon(Icons.chat_bubble_outline), selectedIcon: Icon(Icons.chat_bubble), label: 'AI Chat'),
      NavigationDestination(icon: Icon(Icons.local_library_outlined), selectedIcon: Icon(Icons.local_library), label: 'ห้องสมุด'),
      NavigationDestination(icon: Icon(Icons.hub_outlined), selectedIcon: Icon(Icons.hub), label: 'แผนผัง'),
      NavigationDestination(icon: Icon(Icons.account_tree_outlined), selectedIcon: Icon(Icons.account_tree), label: 'GitHub'),
      NavigationDestination(icon: Icon(Icons.monitor_heart_outlined), selectedIcon: Icon(Icons.monitor_heart), label: 'ระบบ'),
      NavigationDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings), label: 'ตั้งค่า'),
    ];

    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 760) {
          return Scaffold(
            body: Row(
              children: <Widget>[
                NavigationRail(
                  selectedIndex: _selectedIndex,
                  labelType: NavigationRailLabelType.all,
                  onDestinationSelected: (value) => setState(() => _selectedIndex = value),
                  destinations: railDestinations,
                ),
                const VerticalDivider(width: 1),
                Expanded(child: IndexedStack(index: _selectedIndex, children: pages)),
              ],
            ),
          );
        }

        return Scaffold(
          body: IndexedStack(index: _selectedIndex, children: pages),
          bottomNavigationBar: NavigationBar(
            selectedIndex: _selectedIndex,
            onDestinationSelected: (value) => setState(() => _selectedIndex = value),
            destinations: barDestinations,
          ),
        );
      },
    );
  }
}
