import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api/research_os_api_client.dart';
import 'features/agents/agent_center_page.dart';
import 'features/chat/chat_page.dart';
import 'features/developer_access/developer_access_page.dart';
import 'features/github/github_dashboard_page.dart';
import 'features/google_workspace/google_workspace_page.dart';
import 'features/graph/knowledge_graph_page.dart';
import 'features/home/home_page.dart';
import 'features/library/library_page.dart';
import 'features/local_api/local_api_control_page.dart';
import 'features/monitor/system_monitor_page.dart';
import 'features/settings/settings_page.dart';
import 'ui/enterprise_navigation.dart';

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
  static const _chatStorageKey = 'research_os_chat_sessions_v1';

  int _selectedIndex = 0;
  int _chatGeneration = 0;
  bool _sidebarExpanded = true;
  List<ResearchRecentChat> _recentChats = const <ResearchRecentChat>[];

  @override
  void initState() {
    super.initState();
    _refreshRecentChats();
  }

  List<Widget> get _pages => <Widget>[
        HomePage(apiClient: widget.apiClient),
        ChatPage(
          key: ValueKey<String>('research-chat-$_chatGeneration'),
          apiClient: widget.apiClient,
        ),
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
      ];

  List<Map<String, dynamic>> _decodeStoredSessions(String? raw) {
    if (raw == null || raw.trim().isEmpty) return <Map<String, dynamic>>[];
    try {
      final decoded = jsonDecode(raw);
      if (decoded is! List) return <Map<String, dynamic>>[];
      return decoded
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList();
    } on Object {
      return <Map<String, dynamic>>[];
    }
  }

  DateTime _sessionUpdatedAt(Map<String, dynamic> session) {
    final value = session['updated_at'];
    if (value is int) {
      return DateTime.fromMillisecondsSinceEpoch(value);
    }
    return DateTime.tryParse((value ?? '').toString()) ??
        DateTime.fromMillisecondsSinceEpoch(0);
  }

  List<ResearchRecentChat> _summaries(List<Map<String, dynamic>> sessions) {
    final sorted = List<Map<String, dynamic>>.from(sessions)
      ..sort((a, b) => _sessionUpdatedAt(b).compareTo(_sessionUpdatedAt(a)));
    return sorted
        .where((session) => (session['id'] ?? '').toString().isNotEmpty)
        .take(12)
        .map(
          (session) => ResearchRecentChat(
            id: session['id'].toString(),
            title: (session['title'] ?? 'บทสนทนา').toString(),
          ),
        )
        .toList(growable: false);
  }

  Future<void> _refreshRecentChats() async {
    final prefs = await SharedPreferences.getInstance();
    final sessions = _decodeStoredSessions(prefs.getString(_chatStorageKey));
    if (!mounted) return;
    setState(() => _recentChats = _summaries(sessions));
  }

  void _select(int index) {
    setState(() => _selectedIndex = index);
    if (index == 1) _refreshRecentChats();
  }

  Future<void> _createNewChat() async {
    final prefs = await SharedPreferences.getInstance();
    final sessions = _decodeStoredSessions(prefs.getString(_chatStorageKey));
    final now = DateTime.now();
    sessions.insert(0, <String, dynamic>{
      'id': 'chat-${now.microsecondsSinceEpoch.toRadixString(36)}',
      'title': 'บทสนทนาใหม่',
      'updated_at': now.toIso8601String(),
      'messages': <Map<String, dynamic>>[],
    });
    await prefs.setString(_chatStorageKey, jsonEncode(sessions));
    if (!mounted) return;
    setState(() {
      _selectedIndex = 1;
      _chatGeneration += 1;
      _recentChats = _summaries(sessions);
    });
  }

  Future<void> _openRecentChat(String id) async {
    final prefs = await SharedPreferences.getInstance();
    final sessions = _decodeStoredSessions(prefs.getString(_chatStorageKey));
    final now = DateTime.now();
    var found = false;
    for (final session in sessions) {
      if ((session['id'] ?? '').toString() == id) {
        session['updated_at'] = now.toIso8601String();
        found = true;
        break;
      }
    }
    if (!found) return;
    await prefs.setString(_chatStorageKey, jsonEncode(sessions));
    if (!mounted) return;
    setState(() {
      _selectedIndex = 1;
      _chatGeneration += 1;
      _recentChats = _summaries(sessions);
    });
  }

  @override
  Widget build(BuildContext context) {
    final current = researchNavigationItems
        .firstWhere((item) => item.index == _selectedIndex);

    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 920) {
          final scheme = Theme.of(context).colorScheme;
          return Scaffold(
            backgroundColor: scheme.surface,
            body: SafeArea(
              child: Row(
                children: <Widget>[
                  ResearchSidebar(
                    expanded: _sidebarExpanded,
                    selectedIndex: _selectedIndex,
                    recentChats: _recentChats,
                    onToggle: () =>
                        setState(() => _sidebarExpanded = !_sidebarExpanded),
                    onSelected: _select,
                    onNewChat: _createNewChat,
                    onRecentChatSelected: _openRecentChat,
                  ),
                  VerticalDivider(
                    width: 1,
                    thickness: 1,
                    color: Theme.of(context).dividerColor.withValues(alpha: .55),
                  ),
                  Expanded(
                    child: ColoredBox(
                      key: const Key('desktop-main-pane'),
                      color: scheme.surface,
                      child: IndexedStack(
                        index: _selectedIndex,
                        children: _pages,
                      ),
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
