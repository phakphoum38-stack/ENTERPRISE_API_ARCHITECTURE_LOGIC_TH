import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../api/research_os_api_client.dart';
import '../../features/agents/agent_center_page.dart';
import '../../features/chat/chat_page.dart';
import '../../features/checkin/check_in_page.dart';
import '../../features/developer_access/developer_access_page.dart';
import '../../features/github/github_dashboard_page.dart';
import '../../features/google_workspace/google_workspace_page.dart';
import '../../features/graph/knowledge_graph_page.dart';
import '../../features/home/home_page.dart';
import '../../features/library/library_page.dart';
import '../../features/settings/settings_page.dart';
import 'backup_module_page.dart';
import 'control_center_chrome.dart';
import 'live_system_inspector.dart';
import 'module_adapter_pages.dart';
import 'registry_module_page.dart';
import 'research_os_module_catalog.dart';
import 'system_action_module_pages.dart';

class ResearchOSNewShell extends StatefulWidget {
  const ResearchOSNewShell({
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
  State<ResearchOSNewShell> createState() => _ResearchOSNewShellState();
}

enum _LegacyDestination { knowledgeGraph, settings, developerAccess, checkIn }

class _ResearchOSNewShellState extends State<ResearchOSNewShell> {
  static const _chatStorageKey = 'research_os_chat_sessions_v1';

  ResearchOSModuleId _selectedModule = ResearchOSModuleId.chat;
  _LegacyDestination? _legacyDestination;
  bool _sidebarExpanded = true;
  int _chatGeneration = 0;
  List<ResearchRecentConversation> _recentChats =
      const <ResearchRecentConversation>[];

  @override
  void initState() {
    super.initState();
    _refreshRecentChats();
  }

  ResearchOSModuleDefinition get _currentModule => researchOSNewGuiModules
      .firstWhere((module) => module.id == _selectedModule);

  String get _currentTitle {
    final legacy = _legacyDestination;
    if (legacy == null) return _currentModule.label;
    return switch (legacy) {
      _LegacyDestination.knowledgeGraph => 'Knowledge Graph',
      _LegacyDestination.settings => 'Settings',
      _LegacyDestination.developerAccess => 'Developer Access',
      _LegacyDestination.checkIn => 'Check-in',
    };
  }

  List<Map<String, dynamic>> _decodeSessions(String? raw) {
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

  DateTime _updatedAt(Map<String, dynamic> session) {
    final raw = session['updated_at'];
    if (raw is int) return DateTime.fromMillisecondsSinceEpoch(raw);
    return DateTime.tryParse((raw ?? '').toString()) ??
        DateTime.fromMillisecondsSinceEpoch(0);
  }

  List<ResearchRecentConversation> _summaries(
    List<Map<String, dynamic>> sessions,
  ) {
    final sorted = List<Map<String, dynamic>>.from(sessions)
      ..sort((a, b) => _updatedAt(b).compareTo(_updatedAt(a)));
    return sorted
        .where((session) => (session['id'] ?? '').toString().trim().isNotEmpty)
        .take(20)
        .map(
          (session) => ResearchRecentConversation(
            id: session['id'].toString(),
            title: (session['title'] ?? 'บทสนทนา').toString(),
          ),
        )
        .toList(growable: false);
  }

  Future<void> _refreshRecentChats() async {
    final prefs = await SharedPreferences.getInstance();
    final sessions = _decodeSessions(prefs.getString(_chatStorageKey));
    if (!mounted) return;
    setState(() => _recentChats = _summaries(sessions));
  }

  Future<void> _createNewChat() async {
    final prefs = await SharedPreferences.getInstance();
    final sessions = _decodeSessions(prefs.getString(_chatStorageKey));
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
      _selectedModule = ResearchOSModuleId.chat;
      _legacyDestination = null;
      _chatGeneration += 1;
      _recentChats = _summaries(sessions);
    });
  }

  Future<void> _openRecentChat(String id) async {
    final prefs = await SharedPreferences.getInstance();
    final sessions = _decodeSessions(prefs.getString(_chatStorageKey));
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
      _selectedModule = ResearchOSModuleId.chat;
      _legacyDestination = null;
      _chatGeneration += 1;
      _recentChats = _summaries(sessions);
    });
  }

  void _selectModule(ResearchOSModuleId id) {
    setState(() {
      _selectedModule = id;
      _legacyDestination = null;
    });
    if (id == ResearchOSModuleId.chat) _refreshRecentChats();
  }

  void _selectLegacy(_LegacyDestination destination) {
    setState(() => _legacyDestination = destination);
  }

  Widget _buildLegacyPage(_LegacyDestination destination) =>
      switch (destination) {
        _LegacyDestination.knowledgeGraph =>
          KnowledgeGraphPage(apiClient: widget.apiClient),
        _LegacyDestination.settings => SettingsPage(
            apiClient: widget.apiClient,
            themeMode: widget.themeMode,
            onThemeModeChanged:
                widget.onThemeModeChanged ?? (ThemeMode value) {},
            onApiBaseUrlChanged: widget.onApiBaseUrlChanged,
          ),
        _LegacyDestination.developerAccess => DeveloperAccessPage(),
        _LegacyDestination.checkIn => const CheckInPage(),
      };

  Widget _buildModulePage() => switch (_selectedModule) {
        ResearchOSModuleId.home => HomePage(apiClient: widget.apiClient),
        ResearchOSModuleId.chat => ChatPage(
            key: ValueKey<String>('new-gui-chat-$_chatGeneration'),
            apiClient: widget.apiClient,
          ),
        ResearchOSModuleId.agents =>
          AgentCenterPage(apiClient: widget.apiClient),
        ResearchOSModuleId.memory =>
          ResearchMemoryModulePage(apiClient: widget.apiClient),
        ResearchOSModuleId.skills => ResearchRegistryModulePage(
            apiClient: widget.apiClient,
            kind: ResearchRegistryKind.skills,
          ),
        ResearchOSModuleId.tools => ResearchRegistryModulePage(
            apiClient: widget.apiClient,
            kind: ResearchRegistryKind.tools,
          ),
        ResearchOSModuleId.factory =>
          AgentCenterPage(apiClient: widget.apiClient),
        ResearchOSModuleId.providers =>
          ResearchProvidersModulePage(apiClient: widget.apiClient),
        ResearchOSModuleId.files => LibraryPage(apiClient: widget.apiClient),
        ResearchOSModuleId.repositories || ResearchOSModuleId.github =>
          GitHubDashboardPage(apiClient: widget.apiClient),
        ResearchOSModuleId.drive =>
          GoogleWorkspacePage(apiClient: widget.apiClient),
        ResearchOSModuleId.runtime =>
          ResearchRuntimeHub(apiClient: widget.apiClient),
        ResearchOSModuleId.installer => const ResearchInstallerModulePage(),
        ResearchOSModuleId.backup => const ResearchBackupModulePage(),
        ResearchOSModuleId.restore => const ResearchRestoreModulePage(),
        ResearchOSModuleId.shell => const ResearchShellModulePage(),
      };

  Widget _buildCurrentPage() {
    final legacy = _legacyDestination;
    return legacy == null ? _buildModulePage() : _buildLegacyPage(legacy);
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final desktop = constraints.maxWidth >= 980;
        final wide = constraints.maxWidth >= 1320;
        if (!desktop) return _buildMobile(context);
        return _buildDesktop(wide: wide);
      },
    );
  }

  Widget _buildMobile(BuildContext context) {
    return Scaffold(
      key: const Key('new-gui-shell-mobile'),
      appBar: AppBar(
        title: Text(_currentTitle),
        actions: <Widget>[
          IconButton(
            tooltip: 'Settings',
            onPressed: () => _selectLegacy(_LegacyDestination.settings),
            icon: const Icon(Icons.settings_outlined),
          ),
        ],
      ),
      drawer: Drawer(
        child: SafeArea(
          child: ResearchControlCenterNavigation(
            expanded: true,
            selected: _legacyDestination == null ? _selectedModule : null,
            onSelected: (id) {
              Navigator.of(context).pop();
              _selectModule(id);
            },
            onToggle: null,
          ),
        ),
      ),
      body: _buildCurrentPage(),
    );
  }

  Widget _buildDesktop({required bool wide}) {
    return Scaffold(
      key: const Key('new-gui-shell'),
      backgroundColor: const Color(0xFF090E1A),
      body: SafeArea(
        child: Row(
          children: <Widget>[
            ResearchControlCenterNavigation(
              expanded: _sidebarExpanded,
              selected: _legacyDestination == null ? _selectedModule : null,
              onSelected: _selectModule,
              onToggle: () =>
                  setState(() => _sidebarExpanded = !_sidebarExpanded),
            ),
            const VerticalDivider(width: 1, thickness: 1),
            Expanded(
              child: Column(
                children: <Widget>[
                  ResearchControlTopBar(
                    apiClient: widget.apiClient,
                    title: _currentTitle,
                    onSettings: () =>
                        _selectLegacy(_LegacyDestination.settings),
                    onKnowledgeGraph: () =>
                        _selectLegacy(_LegacyDestination.knowledgeGraph),
                    onDeveloperAccess: () =>
                        _selectLegacy(_LegacyDestination.developerAccess),
                    onCheckIn: () =>
                        _selectLegacy(_LegacyDestination.checkIn),
                  ),
                  const Divider(height: 1),
                  Expanded(
                    child: Row(
                      children: <Widget>[
                        if (wide &&
                            _legacyDestination == null &&
                            _selectedModule == ResearchOSModuleId.chat)
                          ResearchConversationRail(
                            chats: _recentChats,
                            onNewChat: _createNewChat,
                            onSelected: _openRecentChat,
                          ),
                        Expanded(
                          child: ColoredBox(
                            key: const Key('new-gui-main-pane'),
                            color: const Color(0xFF090E1A),
                            child: _buildCurrentPage(),
                          ),
                        ),
                        if (wide)
                          ResearchLiveSystemInspector(
                            apiClient: widget.apiClient,
                          ),
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
}
