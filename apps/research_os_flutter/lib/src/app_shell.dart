import 'package:flutter/material.dart';

import 'api/research_os_api_client.dart';
import 'features/agents/agent_center_page.dart';
import 'features/auth/google_login_page.dart';
import 'features/brain_skills/brain_skills_page.dart';
import 'features/chat/chat_workspace_page.dart';
import 'features/developer_access/developer_access_page.dart';
import 'features/friend/friend_connect_page.dart';
import 'features/github/github_dashboard_page.dart';
import 'features/google_workspace/google_workspace_page.dart';
import 'features/graph/knowledge_graph_page.dart';
import 'features/home/home_page.dart';
import 'features/library/library_page.dart';
import 'features/local_api/local_api_control_page.dart';
import 'features/monitor/system_monitor_page.dart';
import 'features/settings/settings_page.dart';
import 'ui/enterprise_navigation.dart';
import 'ui/research_os_sidebar_v2.dart';

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
  bool _sidebarExpanded = false;

  List<Widget> get _pages => <Widget>[
        HomePage(apiClient: widget.apiClient),
        ChatWorkspacePage(apiClient: widget.apiClient),
        AgentCenterPage(apiClient: widget.apiClient),
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
        DeveloperAccessPage(),
        BrainSkillsPage(apiClient: widget.apiClient),
        GoogleLoginPage(apiClient: widget.apiClient),
        FriendConnectPage(apiClient: widget.apiClient),
      ];

  void _select(int index) => setState(() => _selectedIndex = index);

  void _toggleSidebar() {
    setState(() => _sidebarExpanded = !_sidebarExpanded);
  }

  void _selectFromSidebar(int index) {
    setState(() {
      _selectedIndex = index;
      _sidebarExpanded = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final current = researchNavigationItems
        .firstWhere((item) => item.index == _selectedIndex);

    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 920) {
          return Scaffold(
            body: SafeArea(
              child: Row(
                children: <Widget>[
                  ResearchOSSidebarV2(
                    expanded: _sidebarExpanded,
                    selectedIndex: _selectedIndex,
                    onToggle: _toggleSidebar,
                    onSelected: _selectFromSidebar,
                  ),
                  Expanded(
                    child: Column(
                      key: const Key('desktop-content-pane'),
                      children: <Widget>[
                        Expanded(
                          child: IndexedStack(
                            index: _selectedIndex,
                            children: _pages,
                          ),
                        ),
                        const ResearchStatusBar(),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          );
        }

        return Scaffold(
          drawer: ResearchMobileDrawer(
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
                const ResearchBrandMark(compact: true),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(current.label, overflow: TextOverflow.ellipsis),
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
