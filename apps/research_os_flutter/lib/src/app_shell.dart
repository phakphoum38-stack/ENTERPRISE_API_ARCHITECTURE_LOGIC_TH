import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

import 'api/research_os_api_client.dart';
import 'features/agents/agent_center_page.dart';
import 'features/chat/chat_page.dart';
import 'features/checkin/check_in_page.dart';
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

class _ResearchOSAppShellState extends State<ResearchOSAppShell>
    with WidgetsBindingObserver {
  static const _chatStorageKey = 'research_os_chat_sessions_v1';

  int _selectedIndex = 0;
  int _chatGeneration = 0;
  bool _sidebarExpanded = true;
  bool _identityWorking = false;
  Map<String, dynamic> _identityStatus = const <String, dynamic>{};
  String? _identityError;
  List<ResearchRecentChat> _recentChats = const <ResearchRecentChat>[];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _refreshRecentChats();
    _refreshIdentity(silent: true);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _refreshIdentity(silent: true);
    }
  }

  Map<String, dynamic> get _identityAccount {
    final raw = _identityStatus['account'];
    return raw is Map
        ? Map<String, dynamic>.from(raw)
        : const <String, dynamic>{};
  }

  bool get _identityConnected => _identityStatus['connected'] == true;
  bool get _identityConfigured => _identityStatus['oauth_configured'] == true;
  String? get _accountName {
    final value = _identityAccount['name']?.toString().trim();
    return value == null || value.isEmpty ? null : value;
  }

  String? get _accountEmail {
    final value = _identityAccount['email']?.toString().trim();
    return value == null || value.isEmpty ? null : value;
  }

  String get _accountInitial {
    final source = _accountName ?? _accountEmail ?? 'R';
    return source.characters.first.toUpperCase();
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
        const CheckInPage(),
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
        .take(20)
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

  Future<void> _refreshIdentity({bool silent = false}) async {
    try {
      final status = await widget.apiClient.getGoogleIdentityStatus();
      if (!mounted) return;
      setState(() {
        _identityStatus = status;
        _identityError = null;
      });
    } on Object catch (error) {
      if (!mounted || silent) return;
      setState(() => _identityError = error.toString());
    }
  }

  Future<void> _startGoogleSignIn() async {
    if (_identityWorking) return;
    setState(() {
      _identityWorking = true;
      _identityError = null;
    });
    try {
      final response = await widget.apiClient.startGoogleIdentitySignIn();
      final rawUrl = response['authorization_url']?.toString() ?? '';
      final uri = Uri.tryParse(rawUrl);
      if (uri == null || !uri.hasScheme) {
        throw const ResearchOSApiException(
          'Research OS API did not return a valid Google sign-in URL.',
        );
      }
      final launched = await launchUrl(uri, mode: LaunchMode.externalApplication);
      if (!launched) {
        throw const ResearchOSApiException('ไม่สามารถเปิดหน้าลงชื่อเข้าใช้ Google ได้');
      }
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'เปิด Google แล้ว เมื่อลงชื่อเสร็จให้กลับเข้า Research OS ระบบจะตรวจบัญชีให้อัตโนมัติ',
          ),
        ),
      );
    } on Object catch (error) {
      if (mounted) setState(() => _identityError = error.toString());
    } finally {
      if (mounted) setState(() => _identityWorking = false);
    }
  }

  Future<void> _signOutGoogle() async {
    if (_identityWorking) return;
    setState(() {
      _identityWorking = true;
      _identityError = null;
    });
    try {
      await widget.apiClient.signOutGoogleIdentity();
      await _refreshIdentity();
    } on Object catch (error) {
      if (mounted) setState(() => _identityError = error.toString());
    } finally {
      if (mounted) setState(() => _identityWorking = false);
    }
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

  Future<void> _showChatSearch() async {
    final result = await showSearch<String?>(
      context: context,
      delegate: _ResearchChatSearchDelegate(_recentChats),
    );
    if (result != null) await _openRecentChat(result);
  }

  Future<void> _showAccountSheet() async {
    await _refreshIdentity(silent: true);
    if (!mounted) return;
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: Colors.transparent,
      builder: (sheetContext) => _ResearchAccountSheet(
        connected: _identityConnected,
        configured: _identityConfigured,
        working: _identityWorking,
        name: _accountName,
        email: _accountEmail,
        error: _identityError,
        onSignIn: () async {
          Navigator.of(sheetContext).pop();
          await _startGoogleSignIn();
        },
        onSignOut: () async {
          Navigator.of(sheetContext).pop();
          await _signOutGoogle();
        },
        onRefresh: () async {
          Navigator.of(sheetContext).pop();
          await _refreshIdentity();
          if (mounted) await _showAccountSheet();
        },
        onNavigate: (index) {
          Navigator.of(sheetContext).pop();
          _select(index);
        },
      ),
    );
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
                    accountConnected: _identityConnected,
                    accountName: _accountName,
                    accountEmail: _accountEmail,
                    onToggle: () =>
                        setState(() => _sidebarExpanded = !_sidebarExpanded),
                    onSelected: _select,
                    onNewChat: _createNewChat,
                    onRecentChatSelected: _openRecentChat,
                    onSearch: _showChatSearch,
                    onAccountTap: _showAccountSheet,
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
            recentChats: _recentChats,
            accountConnected: _identityConnected,
            accountName: _accountName,
            accountEmail: _accountEmail,
            onSelected: (index) {
              Navigator.of(context).pop();
              _select(index);
            },
            onNewChat: _createNewChat,
            onRecentChatSelected: _openRecentChat,
            onSearch: _showChatSearch,
            onAccountTap: _showAccountSheet,
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
                key: const Key('mobile-account-button'),
                tooltip: _identityConnected ? _accountEmail ?? 'บัญชี' : 'ลงชื่อเข้าใช้',
                onPressed: _showAccountSheet,
                icon: CircleAvatar(
                  radius: 15,
                  child: Text(
                    _accountInitial,
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800),
                  ),
                ),
              ),
              const SizedBox(width: 6),
            ],
          ),
          body: IndexedStack(index: _selectedIndex, children: _pages),
        );
      },
    );
  }
}

class _ResearchAccountSheet extends StatelessWidget {
  const _ResearchAccountSheet({
    required this.connected,
    required this.configured,
    required this.working,
    required this.name,
    required this.email,
    required this.error,
    required this.onSignIn,
    required this.onSignOut,
    required this.onRefresh,
    required this.onNavigate,
  });

  final bool connected;
  final bool configured;
  final bool working;
  final String? name;
  final String? email;
  final String? error;
  final Future<void> Function() onSignIn;
  final Future<void> Function() onSignOut;
  final Future<void> Function() onRefresh;
  final ValueChanged<int> onNavigate;

  String get _displayName {
    if (name?.trim().isNotEmpty ?? false) return name!.trim();
    if (email?.trim().isNotEmpty ?? false) return email!.trim().split('@').first;
    return 'Research OS';
  }

  String get _initial => _displayName.characters.first.toUpperCase();

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final height = MediaQuery.sizeOf(context).height * 0.9;
    return Container(
      key: const Key('research-account-sheet'),
      height: height,
      decoration: BoxDecoration(
        color: scheme.surfaceContainerLow,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(34)),
      ),
      child: Stack(
        children: <Widget>[
          ListView(
            padding: const EdgeInsets.fromLTRB(28, 74, 28, 42),
            children: <Widget>[
              Center(
                child: CircleAvatar(
                  radius: 48,
                  backgroundColor: scheme.primaryContainer,
                  child: Text(
                    _initial,
                    style: TextStyle(
                      fontSize: 34,
                      color: scheme.onPrimaryContainer,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 18),
              Text(
                _displayName,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.w800,
                    ),
              ),
              if (connected && email != null) ...<Widget>[
                const SizedBox(height: 5),
                Text(
                  email!,
                  key: const Key('account-email'),
                  textAlign: TextAlign.center,
                  style: TextStyle(color: scheme.onSurfaceVariant),
                ),
              ],
              const SizedBox(height: 30),
              Text(
                'Customize Research OS',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: scheme.onSurfaceVariant,
                      fontWeight: FontWeight.w700,
                    ),
              ),
              const SizedBox(height: 10),
              _AccountGroup(
                children: <Widget>[
                  _AccountRow(
                    icon: Icons.tune_rounded,
                    label: 'Personalization',
                    onTap: () => onNavigate(9),
                  ),
                  _AccountRow(
                    icon: Icons.menu_book_outlined,
                    label: 'Memory',
                    onTap: () => onNavigate(3),
                  ),
                  _AccountRow(
                    icon: Icons.extension_outlined,
                    label: 'Plugins & Connections',
                    onTap: () => onNavigate(6),
                  ),
                ],
              ),
              const SizedBox(height: 26),
              Text(
                'Account',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: scheme.onSurfaceVariant,
                      fontWeight: FontWeight.w700,
                    ),
              ),
              const SizedBox(height: 10),
              _AccountGroup(
                children: <Widget>[
                  _AccountRow(
                    icon: Icons.mail_outline_rounded,
                    label: 'Email',
                    trailing: connected ? email ?? 'Google account' : 'ยังไม่ได้ลงชื่อ',
                  ),
                  _AccountRow(
                    icon: Icons.palette_outlined,
                    label: 'Theme',
                    onTap: () => onNavigate(9),
                  ),
                  _AccountRow(
                    icon: Icons.shield_outlined,
                    label: 'Local-first storage',
                    onTap: () => onNavigate(8),
                  ),
                ],
              ),
              if (error != null) ...<Widget>[
                const SizedBox(height: 16),
                Text(
                  error!,
                  textAlign: TextAlign.center,
                  style: TextStyle(color: scheme.error),
                ),
              ],
              const SizedBox(height: 22),
              if (!connected)
                FilledButton.icon(
                  key: const Key('google-sign-in-button'),
                  onPressed: working || !configured ? null : onSignIn,
                  icon: const Icon(Icons.login_rounded),
                  label: const Text('Continue with Google / Gmail'),
                )
              else
                OutlinedButton.icon(
                  key: const Key('google-sign-out-button'),
                  onPressed: working ? null : onSignOut,
                  icon: const Icon(Icons.logout_rounded),
                  label: const Text('Sign out'),
                ),
              const SizedBox(height: 8),
              TextButton.icon(
                onPressed: working ? null : onRefresh,
                icon: const Icon(Icons.refresh_rounded),
                label: const Text('ตรวจสถานะบัญชี'),
              ),
              if (!connected && !configured)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(
                    'Google OAuth ยังไม่ได้ตั้งค่าบน Research OS API',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: scheme.onSurfaceVariant),
                  ),
                ),
            ],
          ),
          Positioned(
            top: 18,
            right: 18,
            child: IconButton.filledTonal(
              tooltip: 'ปิด',
              onPressed: () => Navigator.of(context).pop(),
              icon: const Icon(Icons.close_rounded),
            ),
          ),
        ],
      ),
    );
  }
}

class _AccountGroup extends StatelessWidget {
  const _AccountGroup({required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.zero,
      clipBehavior: Clip.antiAlias,
      child: Column(
        children: <Widget>[
          for (var index = 0; index < children.length; index++) ...<Widget>[
            children[index],
            if (index != children.length - 1)
              const Divider(height: 1, indent: 58),
          ],
        ],
      ),
    );
  }
}

class _AccountRow extends StatelessWidget {
  const _AccountRow({
    required this.icon,
    required this.label,
    this.trailing,
    this.onTap,
  });

  final IconData icon;
  final String label;
  final String? trailing;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon),
      title: Text(label),
      trailing: trailing != null
          ? ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 190),
              child: Text(
                trailing!,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(color: Theme.of(context).colorScheme.onSurfaceVariant),
              ),
            )
          : onTap != null
              ? const Icon(Icons.chevron_right_rounded)
              : null,
      onTap: onTap,
    );
  }
}

class _ResearchChatSearchDelegate extends SearchDelegate<String?> {
  _ResearchChatSearchDelegate(this.chats);

  final List<ResearchRecentChat> chats;

  @override
  String get searchFieldLabel => 'ค้นหาบทสนทนา';

  @override
  List<Widget>? buildActions(BuildContext context) => <Widget>[
        if (query.isNotEmpty)
          IconButton(
            tooltip: 'ล้าง',
            onPressed: () => query = '',
            icon: const Icon(Icons.close_rounded),
          ),
      ];

  @override
  Widget? buildLeading(BuildContext context) => IconButton(
        tooltip: 'กลับ',
        onPressed: () => close(context, null),
        icon: const Icon(Icons.arrow_back_rounded),
      );

  @override
  Widget buildResults(BuildContext context) => _results(context);

  @override
  Widget buildSuggestions(BuildContext context) => _results(context);

  Widget _results(BuildContext context) {
    final needle = query.trim().toLowerCase();
    final matches = chats
        .where((chat) => needle.isEmpty || chat.title.toLowerCase().contains(needle))
        .toList(growable: false);
    if (matches.isEmpty) {
      return const Center(child: Text('ไม่พบบทสนทนา'));
    }
    return ListView.builder(
      itemCount: matches.length,
      itemBuilder: (context, index) {
        final chat = matches[index];
        return ListTile(
          leading: const Icon(Icons.chat_bubble_outline),
          title: Text(chat.title),
          onTap: () => close(context, chat.id),
        );
      },
    );
  }
}
