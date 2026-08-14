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
import '../../features/local_api/local_api_control_page.dart';
import '../../features/monitor/system_monitor_page.dart';
import '../../features/settings/settings_page.dart';
import 'research_os_module_catalog.dart';

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
  List<_RecentConversation> _recentChats = const <_RecentConversation>[];

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

  List<_RecentConversation> _summaries(List<Map<String, dynamic>> sessions) {
    final sorted = List<Map<String, dynamic>>.from(sessions)
      ..sort((a, b) => _updatedAt(b).compareTo(_updatedAt(a)));
    return sorted
        .where((session) => (session['id'] ?? '').toString().trim().isNotEmpty)
        .take(20)
        .map(
          (session) => _RecentConversation(
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

  Widget _buildCurrentPage() {
    final legacy = _legacyDestination;
    if (legacy != null) {
      return switch (legacy) {
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
    }

    return switch (_selectedModule) {
      ResearchOSModuleId.home => HomePage(apiClient: widget.apiClient),
      ResearchOSModuleId.chat => ChatPage(
          key: ValueKey<String>('new-gui-chat-$_chatGeneration'),
          apiClient: widget.apiClient,
        ),
      ResearchOSModuleId.agents => AgentCenterPage(apiClient: widget.apiClient),
      ResearchOSModuleId.memory => _MemoryModulePage(apiClient: widget.apiClient),
      ResearchOSModuleId.skills => _ModuleAdapterPage(module: _currentModule),
      ResearchOSModuleId.tools => _ModuleAdapterPage(module: _currentModule),
      ResearchOSModuleId.factory => _FactoryModulePage(apiClient: widget.apiClient),
      ResearchOSModuleId.providers =>
        _ProvidersModulePage(apiClient: widget.apiClient),
      ResearchOSModuleId.files => LibraryPage(apiClient: widget.apiClient),
      ResearchOSModuleId.repositories =>
        GitHubDashboardPage(apiClient: widget.apiClient),
      ResearchOSModuleId.github =>
        GitHubDashboardPage(apiClient: widget.apiClient),
      ResearchOSModuleId.drive =>
        GoogleWorkspacePage(apiClient: widget.apiClient),
      ResearchOSModuleId.runtime => _RuntimeHub(apiClient: widget.apiClient),
      ResearchOSModuleId.installer ||
      ResearchOSModuleId.backup ||
      ResearchOSModuleId.restore ||
      ResearchOSModuleId.shell => _ModuleAdapterPage(module: _currentModule),
    };
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final desktop = constraints.maxWidth >= 980;
        final wide = constraints.maxWidth >= 1320;
        if (!desktop) {
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
                child: _ModuleNavigation(
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

        return Scaffold(
          key: const Key('new-gui-shell'),
          backgroundColor: const Color(0xFF090E1A),
          body: SafeArea(
            child: Row(
              children: <Widget>[
                _ModuleNavigation(
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
                      _ControlTopBar(
                        apiClient: widget.apiClient,
                        title: _currentTitle,
                        onSettings: () =>
                            _selectLegacy(_LegacyDestination.settings),
                        onLegacySelected: _selectLegacy,
                      ),
                      const Divider(height: 1),
                      Expanded(
                        child: Row(
                          children: <Widget>[
                            if (wide &&
                                _legacyDestination == null &&
                                _selectedModule == ResearchOSModuleId.chat)
                              _ConversationRail(
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
                              _SystemInspector(apiClient: widget.apiClient),
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
      },
    );
  }
}

class _ModuleNavigation extends StatelessWidget {
  const _ModuleNavigation({
    required this.expanded,
    required this.selected,
    required this.onSelected,
    required this.onToggle,
  });

  final bool expanded;
  final ResearchOSModuleId? selected;
  final ValueChanged<ResearchOSModuleId> onSelected;
  final VoidCallback? onToggle;

  String _sectionLabel(ResearchOSModuleSection section) => switch (section) {
        ResearchOSModuleSection.main => 'MAIN',
        ResearchOSModuleSection.workspace => 'WORKSPACE',
        ResearchOSModuleSection.system => 'SYSTEM',
      };

  @override
  Widget build(BuildContext context) {
    final grouped = <ResearchOSModuleSection, List<ResearchOSModuleDefinition>>{};
    for (final module in researchOSNewGuiModules) {
      grouped.putIfAbsent(module.section, () => <ResearchOSModuleDefinition>[])
        ..add(module);
    }

    return AnimatedContainer(
      key: const Key('new-gui-sidebar'),
      duration: const Duration(milliseconds: 180),
      width: expanded ? 224 : 76,
      color: const Color(0xFF0D1424),
      child: Column(
        children: <Widget>[
          SizedBox(
            height: 68,
            child: Row(
              children: <Widget>[
                const SizedBox(width: 14),
                Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(12),
                    gradient: const LinearGradient(
                      colors: <Color>[Color(0xFF5B7CFF), Color(0xFF45D4E8)],
                    ),
                  ),
                  child: const Icon(Icons.hub_rounded, color: Colors.white),
                ),
                if (expanded) ...<Widget>[
                  const SizedBox(width: 10),
                  const Expanded(
                    child: Text(
                      'Research OS',
                      key: Key('new-gui-brand-title'),
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w800,
                        fontSize: 16,
                      ),
                    ),
                  ),
                ],
                if (onToggle != null)
                  IconButton(
                    key: const Key('new-gui-toggle-sidebar'),
                    onPressed: onToggle,
                    icon: Icon(
                      expanded ? Icons.menu_open_rounded : Icons.menu_rounded,
                      color: Colors.white70,
                    ),
                  ),
              ],
            ),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(8, 8, 8, 12),
              children: <Widget>[
                for (final section in ResearchOSModuleSection.values) ...<Widget>[
                  if (expanded)
                    Padding(
                      padding: const EdgeInsets.fromLTRB(12, 14, 12, 6),
                      child: Text(
                        _sectionLabel(section),
                        style: const TextStyle(
                          color: Color(0xFF7E8DA8),
                          fontSize: 10,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 1.1,
                        ),
                      ),
                    ),
                  for (final module in grouped[section] ?? const <ResearchOSModuleDefinition>[])
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 2),
                      child: Material(
                        color: selected == module.id
                            ? const Color(0xFF172238)
                            : Colors.transparent,
                        borderRadius: BorderRadius.circular(12),
                        child: InkWell(
                          key: Key('new-gui-nav-${module.id.name}'),
                          borderRadius: BorderRadius.circular(12),
                          onTap: () => onSelected(module.id),
                          child: SizedBox(
                            height: 42,
                            child: Row(
                              children: <Widget>[
                                SizedBox(
                                  width: 48,
                                  child: Icon(
                                    module.icon,
                                    color: selected == module.id
                                        ? const Color(0xFF7EA2FF)
                                        : const Color(0xFFA8B5CA),
                                    size: 21,
                                  ),
                                ),
                                if (expanded)
                                  Expanded(
                                    child: Text(
                                      module.label,
                                      overflow: TextOverflow.ellipsis,
                                      style: TextStyle(
                                        color: selected == module.id
                                            ? Colors.white
                                            : const Color(0xFFC2CCDA),
                                        fontWeight: selected == module.id
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
                ],
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Container(
              padding: EdgeInsets.all(expanded ? 12 : 8),
              decoration: BoxDecoration(
                color: const Color(0xFF11192B),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFF26344F)),
              ),
              child: expanded
                  ? const Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Text(
                          '6^6 ORCHESTRATOR',
                          style: TextStyle(
                            color: Color(0xFF8EA4C5),
                            fontSize: 10,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        SizedBox(height: 6),
                        Row(
                          children: <Widget>[
                            Icon(Icons.circle, size: 9, color: Color(0xFF3DDC97)),
                            SizedBox(width: 7),
                            Text(
                              'Adaptive / bounded',
                              style: TextStyle(color: Colors.white70, fontSize: 12),
                            ),
                          ],
                        ),
                      ],
                    )
                  : const Icon(Icons.hub_outlined, color: Color(0xFF7EA2FF)),
            ),
          ),
        ],
      ),
    );
  }
}

class _ControlTopBar extends StatelessWidget {
  const _ControlTopBar({
    required this.apiClient,
    required this.title,
    required this.onSettings,
    required this.onLegacySelected,
  });

  final ResearchOSApiClient apiClient;
  final String title;
  final VoidCallback onSettings;
  final ValueChanged<_LegacyDestination> onLegacySelected;

  @override
  Widget build(BuildContext context) {
    return Container(
      key: const Key('new-gui-top-bar'),
      height: 68,
      color: const Color(0xFF0D1424),
      padding: const EdgeInsets.symmetric(horizontal: 18),
      child: Row(
        children: <Widget>[
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 17,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  apiClient.baseUrl,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: Color(0xFF8291AA), fontSize: 11),
                ),
              ],
            ),
          ),
          _HealthPill(apiClient: apiClient),
          const SizedBox(width: 10),
          PopupMenuButton<_LegacyDestination>(
            tooltip: 'Additional modules',
            color: const Color(0xFF172238),
            onSelected: onLegacySelected,
            itemBuilder: (context) => const <PopupMenuEntry<_LegacyDestination>>[
              PopupMenuItem(
                value: _LegacyDestination.knowledgeGraph,
                child: Text('Knowledge Graph'),
              ),
              PopupMenuItem(
                value: _LegacyDestination.developerAccess,
                child: Text('Developer Access'),
              ),
              PopupMenuItem(
                value: _LegacyDestination.checkIn,
                child: Text('Check-in'),
              ),
            ],
            icon: const Icon(Icons.more_horiz_rounded, color: Colors.white70),
          ),
          IconButton(
            key: const Key('new-gui-settings'),
            tooltip: 'Settings',
            onPressed: onSettings,
            icon: const Icon(Icons.settings_outlined, color: Colors.white70),
          ),
        ],
      ),
    );
  }
}

class _HealthPill extends StatefulWidget {
  const _HealthPill({required this.apiClient});

  final ResearchOSApiClient apiClient;

  @override
  State<_HealthPill> createState() => _HealthPillState();
}

class _HealthPillState extends State<_HealthPill> {
  late Future<Map<String, dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = widget.apiClient.getHealth();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Map<String, dynamic>>(
      future: _future,
      builder: (context, snapshot) {
        final healthy = snapshot.hasData &&
            ((snapshot.data?['status'] ?? '').toString().toLowerCase() == 'ok' ||
                snapshot.data?['healthy'] == true);
        final waiting = snapshot.connectionState == ConnectionState.waiting;
        return Container(
          key: const Key('new-gui-health-pill'),
          padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 7),
          decoration: BoxDecoration(
            color: const Color(0xFF11192B),
            borderRadius: BorderRadius.circular(999),
            border: Border.all(color: const Color(0xFF26344F)),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              Icon(
                Icons.circle,
                size: 9,
                color: waiting
                    ? const Color(0xFFF7C65C)
                    : healthy
                        ? const Color(0xFF3DDC97)
                        : const Color(0xFFFF6B7A),
              ),
              const SizedBox(width: 7),
              Text(
                waiting ? 'Checking' : healthy ? 'Healthy' : 'Needs attention',
                style: const TextStyle(color: Colors.white70, fontSize: 11),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _ConversationRail extends StatelessWidget {
  const _ConversationRail({
    required this.chats,
    required this.onNewChat,
    required this.onSelected,
  });

  final List<_RecentConversation> chats;
  final Future<void> Function() onNewChat;
  final Future<void> Function(String id) onSelected;

  @override
  Widget build(BuildContext context) {
    return Container(
      key: const Key('new-gui-conversation-rail'),
      width: 248,
      color: const Color(0xFF0B1220),
      padding: const EdgeInsets.fromLTRB(12, 14, 12, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          FilledButton.icon(
            key: const Key('new-gui-new-chat'),
            onPressed: onNewChat,
            icon: const Icon(Icons.add_rounded, size: 18),
            label: const Text('New Chat'),
          ),
          const SizedBox(height: 14),
          const Text(
            'CONVERSATIONS',
            style: TextStyle(
              color: Color(0xFF7587A4),
              fontSize: 10,
              fontWeight: FontWeight.w800,
              letterSpacing: 1,
            ),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: chats.isEmpty
                ? const Center(
                    child: Text(
                      'ยังไม่มีบทสนทนา',
                      style: TextStyle(color: Color(0xFF7587A4), fontSize: 12),
                    ),
                  )
                : ListView.builder(
                    itemCount: chats.length,
                    itemBuilder: (context, index) {
                      final chat = chats[index];
                      return ListTile(
                        key: Key('new-gui-chat-${chat.id}'),
                        dense: true,
                        contentPadding: const EdgeInsets.symmetric(horizontal: 8),
                        leading: const Icon(
                          Icons.chat_bubble_outline_rounded,
                          size: 17,
                          color: Color(0xFF8EA4C5),
                        ),
                        title: Text(
                          chat.title,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(color: Color(0xFFC9D4E4), fontSize: 12),
                        ),
                        onTap: () => onSelected(chat.id),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}

class _SystemInspector extends StatefulWidget {
  const _SystemInspector({required this.apiClient});

  final ResearchOSApiClient apiClient;

  @override
  State<_SystemInspector> createState() => _SystemInspectorState();
}

class _SystemInspectorState extends State<_SystemInspector> {
  late Future<_SystemSnapshot> _future;

  @override
  void initState() {
    super.initState();
    _future = _SystemSnapshot.load(widget.apiClient);
  }

  void _refresh() {
    setState(() => _future = _SystemSnapshot.load(widget.apiClient));
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      key: const Key('new-gui-system-inspector'),
      width: 286,
      color: const Color(0xFF0B1220),
      padding: const EdgeInsets.fromLTRB(14, 14, 14, 12),
      child: FutureBuilder<_SystemSnapshot>(
        future: _future,
        builder: (context, snapshot) {
          final data = snapshot.data;
          return ListView(
            children: <Widget>[
              Row(
                children: <Widget>[
                  const Expanded(
                    child: Text(
                      'System Status',
                      style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800),
                    ),
                  ),
                  IconButton(
                    tooltip: 'Refresh',
                    onPressed: _refresh,
                    icon: const Icon(Icons.refresh_rounded, color: Colors.white60, size: 19),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              _InspectorCard(
                title: 'Local Service',
                value: data?.healthLabel ?? 'Checking…',
                icon: Icons.dns_outlined,
              ),
              const SizedBox(height: 9),
              _InspectorCard(
                title: 'Provider',
                value: data?.providerLabel ?? 'Checking…',
                icon: Icons.hub_outlined,
              ),
              const SizedBox(height: 9),
              _InspectorCard(
                title: 'Agents',
                value: data?.agentLabel ?? 'Checking…',
                icon: Icons.smart_toy_outlined,
              ),
              const SizedBox(height: 18),
              const Text(
                'Adaptive Runtime',
                style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 9),
              Container(
                padding: const EdgeInsets.all(13),
                decoration: BoxDecoration(
                  color: const Color(0xFF11192B),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: const Color(0xFF26344F)),
                ),
                child: const Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text('6^6 logical scale', style: TextStyle(color: Color(0xFF8EA4C5), fontSize: 11)),
                    SizedBox(height: 5),
                    Text('Bounded by AMR', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
                    SizedBox(height: 6),
                    Text('Modules activate on demand; explicit owner modules are not silently dropped.', style: TextStyle(color: Color(0xFF8EA4C5), fontSize: 11, height: 1.35)),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _InspectorCard extends StatelessWidget {
  const _InspectorCard({required this.title, required this.value, required this.icon});

  final String title;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF11192B),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF26344F)),
      ),
      child: Row(
        children: <Widget>[
          Icon(icon, color: const Color(0xFF7EA2FF), size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(title, style: const TextStyle(color: Color(0xFF8EA4C5), fontSize: 10)),
                const SizedBox(height: 3),
                Text(value, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w700)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SystemSnapshot {
  const _SystemSnapshot({required this.healthLabel, required this.providerLabel, required this.agentLabel});

  final String healthLabel;
  final String providerLabel;
  final String agentLabel;

  static Future<_SystemSnapshot> load(ResearchOSApiClient apiClient) async {
    var health = 'Unavailable';
    var provider = 'Unavailable';
    var agents = 'Unavailable';

    try {
      final value = await apiClient.getHealth();
      final status = (value['status'] ?? (value['healthy'] == true ? 'healthy' : '')).toString();
      health = status.isEmpty ? 'Connected' : status;
    } on Object {
      health = 'Offline / error';
    }

    try {
      final value = await apiClient.getProviders();
      final active = (value['active'] ?? value['provider'] ?? '').toString();
      provider = active.isEmpty ? 'Connected' : active;
    } on Object {
      provider = 'Offline / error';
    }

    try {
      final value = await apiClient.getAgents();
      final raw = value['agents'];
      agents = raw is List ? '${raw.length} registered' : 'Connected';
    } on Object {
      agents = 'Offline / error';
    }

    return _SystemSnapshot(healthLabel: health, providerLabel: provider, agentLabel: agents);
  }
}

class _MemoryModulePage extends StatefulWidget {
  const _MemoryModulePage({required this.apiClient});

  final ResearchOSApiClient apiClient;

  @override
  State<_MemoryModulePage> createState() => _MemoryModulePageState();
}

class _MemoryModulePageState extends State<_MemoryModulePage> {
  final TextEditingController _controller = TextEditingController();
  Map<String, dynamic>? _result;
  String? _error;
  bool _working = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _search() async {
    final query = _controller.text.trim();
    if (query.isEmpty || _working) return;
    setState(() {
      _working = true;
      _error = null;
    });
    try {
      final result = await widget.apiClient.searchMemory(query);
      if (mounted) setState(() => _result = result);
    } on Object catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return _ModuleSurface(
      title: 'Memory',
      subtitle: 'Search the existing memory/evidence runtime without replacing it.',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          TextField(
            controller: _controller,
            decoration: const InputDecoration(labelText: 'Search memory'),
            onSubmitted: (_) => _search(),
          ),
          const SizedBox(height: 10),
          Align(
            alignment: Alignment.centerLeft,
            child: FilledButton.icon(
              onPressed: _working ? null : _search,
              icon: _working
                  ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.search_rounded),
              label: const Text('Search'),
            ),
          ),
          if (_error != null) ...<Widget>[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: Color(0xFFFF6B7A))),
          ],
          if (_result != null) ...<Widget>[
            const SizedBox(height: 14),
            SelectableText(
              const JsonEncoder.withIndent('  ').convert(_result),
              style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
            ),
          ],
        ],
      ),
    );
  }
}

class _ProvidersModulePage extends StatefulWidget {
  const _ProvidersModulePage({required this.apiClient});

  final ResearchOSApiClient apiClient;

  @override
  State<_ProvidersModulePage> createState() => _ProvidersModulePageState();
}

class _ProvidersModulePageState extends State<_ProvidersModulePage> {
  late Future<Map<String, dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = widget.apiClient.getProviders();
  }

  @override
  Widget build(BuildContext context) {
    return _ModuleSurface(
      title: 'Providers',
      subtitle: 'Live provider data from /v1/providers.',
      child: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) return Text(snapshot.error.toString());
          return SelectableText(
            const JsonEncoder.withIndent('  ').convert(snapshot.data ?? const <String, dynamic>{}),
            style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
          );
        },
      ),
    );
  }
}

class _FactoryModulePage extends StatefulWidget {
  const _FactoryModulePage({required this.apiClient});

  final ResearchOSApiClient apiClient;

  @override
  State<_FactoryModulePage> createState() => _FactoryModulePageState();
}

class _FactoryModulePageState extends State<_FactoryModulePage> {
  late Future<Map<String, dynamic>> _future;

  @override
  void initState() {
    super.initState();
    _future = widget.apiClient.getOrchestrations(limit: 20);
  }

  @override
  Widget build(BuildContext context) {
    return _ModuleSurface(
      title: 'Factory',
      subtitle: 'Existing orchestration runtime exposed as a control-center module.',
      child: FutureBuilder<Map<String, dynamic>>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) return Text(snapshot.error.toString());
          return SelectableText(
            const JsonEncoder.withIndent('  ').convert(snapshot.data ?? const <String, dynamic>{}),
            style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
          );
        },
      ),
    );
  }
}

class _RuntimeHub extends StatelessWidget {
  const _RuntimeHub({required this.apiClient});

  final ResearchOSApiClient apiClient;

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Column(
        children: <Widget>[
          const Material(
            child: TabBar(
              tabs: <Widget>[
                Tab(text: 'Local API & Service'),
                Tab(text: 'System Monitor'),
              ],
            ),
          ),
          Expanded(
            child: TabBarView(
              children: <Widget>[
                const LocalApiControlPage(),
                SystemMonitorPage(apiClient: apiClient),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ModuleAdapterPage extends StatelessWidget {
  const _ModuleAdapterPage({required this.module});

  final ResearchOSModuleDefinition module;

  @override
  Widget build(BuildContext context) {
    return _ModuleSurface(
      title: module.label,
      subtitle: module.availability == 'planned'
          ? 'Dedicated surface is intentionally not faked. The integration evidence must be established before mutable controls are enabled.'
          : 'The capability exists; this new GUI surface is being wired to the existing runtime adapter.',
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: const Color(0xFF11192B),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFF26344F)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text('Status: ${module.availability}', style: const TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            Text('Source: ${module.backendSource ?? 'not established'}'),
          ],
        ),
      ),
    );
  }
}

class _ModuleSurface extends StatelessWidget {
  const _ModuleSurface({required this.title, required this.subtitle, required this.child});

  final String title;
  final String subtitle;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF090E1A),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: <Widget>[
            Text(title, style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 4),
            Text(subtitle, style: const TextStyle(color: Color(0xFF8EA4C5))),
            const SizedBox(height: 18),
            child,
          ],
        ),
      ),
    );
  }
}

class _RecentConversation {
  const _RecentConversation({required this.id, required this.title});

  final String id;
  final String title;
}
