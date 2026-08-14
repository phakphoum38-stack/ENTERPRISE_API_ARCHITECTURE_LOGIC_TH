import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';
import 'research_os_module_catalog.dart';

class ResearchRecentConversation {
  const ResearchRecentConversation({required this.id, required this.title});

  final String id;
  final String title;
}

class ResearchControlCenterNavigation extends StatelessWidget {
  const ResearchControlCenterNavigation({
    required this.expanded,
    required this.selected,
    required this.onSelected,
    required this.onToggle,
    super.key,
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
      final entries = grouped.putIfAbsent(
        module.section,
        () => <ResearchOSModuleDefinition>[],
      );
      entries.add(module);
    }

    return AnimatedContainer(
      key: const Key('new-gui-sidebar'),
      duration: const Duration(milliseconds: 180),
      width: expanded ? 236 : 76,
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
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
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
              key: const Key('new-gui-navigation-list'),
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
                  for (final module
                      in grouped[section] ?? const <ResearchOSModuleDefinition>[])
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
              width: double.infinity,
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
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            color: Color(0xFF8EA4C5),
                            fontSize: 10,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        SizedBox(height: 6),
                        Row(
                          children: <Widget>[
                            Icon(
                              Icons.circle,
                              size: 9,
                              color: Color(0xFF3DDC97),
                            ),
                            SizedBox(width: 7),
                            Expanded(
                              child: Text(
                                'AMR bounded',
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                  color: Colors.white70,
                                  fontSize: 12,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                    )
                  : const Icon(
                      Icons.hub_outlined,
                      color: Color(0xFF7EA2FF),
                    ),
            ),
          ),
        ],
      ),
    );
  }
}

class ResearchControlTopBar extends StatelessWidget {
  const ResearchControlTopBar({
    required this.apiClient,
    required this.title,
    required this.onSettings,
    required this.onKnowledgeGraph,
    required this.onDeveloperAccess,
    required this.onCheckIn,
    super.key,
  });

  final ResearchOSApiClient apiClient;
  final String title;
  final VoidCallback onSettings;
  final VoidCallback onKnowledgeGraph;
  final VoidCallback onDeveloperAccess;
  final VoidCallback onCheckIn;

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
                  style: const TextStyle(
                    color: Color(0xFF8291AA),
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ),
          ResearchHealthPill(apiClient: apiClient),
          const SizedBox(width: 10),
          PopupMenuButton<String>(
            tooltip: 'Additional modules',
            color: const Color(0xFF172238),
            onSelected: (value) {
              switch (value) {
                case 'knowledge':
                  onKnowledgeGraph();
                case 'developer':
                  onDeveloperAccess();
                case 'checkin':
                  onCheckIn();
              }
            },
            itemBuilder: (context) => const <PopupMenuEntry<String>>[
              PopupMenuItem(value: 'knowledge', child: Text('Knowledge Graph')),
              PopupMenuItem(value: 'developer', child: Text('Developer Access')),
              PopupMenuItem(value: 'checkin', child: Text('Check-in')),
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

class ResearchHealthPill extends StatefulWidget {
  const ResearchHealthPill({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<ResearchHealthPill> createState() => _ResearchHealthPillState();
}

class _ResearchHealthPillState extends State<ResearchHealthPill> {
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

class ResearchConversationRail extends StatelessWidget {
  const ResearchConversationRail({
    required this.chats,
    required this.onNewChat,
    required this.onSelected,
    super.key,
  });

  final List<ResearchRecentConversation> chats;
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
                      style: TextStyle(
                        color: Color(0xFF7587A4),
                        fontSize: 12,
                      ),
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
                          style: const TextStyle(
                            color: Color(0xFFC9D4E4),
                            fontSize: 12,
                          ),
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

class ResearchSystemInspector extends StatefulWidget {
  const ResearchSystemInspector({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<ResearchSystemInspector> createState() => _ResearchSystemInspectorState();
}

class _ResearchSystemInspectorState extends State<ResearchSystemInspector> {
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
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                  IconButton(
                    tooltip: 'Refresh',
                    onPressed: _refresh,
                    icon: const Icon(
                      Icons.refresh_rounded,
                      color: Colors.white60,
                      size: 19,
                    ),
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
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w800,
                ),
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
                    Text(
                      '6^6 logical scale',
                      style: TextStyle(color: Color(0xFF8EA4C5), fontSize: 11),
                    ),
                    SizedBox(height: 5),
                    Text(
                      'Bounded by AMR',
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    SizedBox(height: 6),
                    Text(
                      'Modules activate on demand; explicit owner modules are not silently dropped.',
                      style: TextStyle(
                        color: Color(0xFF8EA4C5),
                        fontSize: 11,
                        height: 1.35,
                      ),
                    ),
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
  const _InspectorCard({
    required this.title,
    required this.value,
    required this.icon,
  });

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
                Text(
                  title,
                  style: const TextStyle(
                    color: Color(0xFF8EA4C5),
                    fontSize: 10,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  value,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SystemSnapshot {
  const _SystemSnapshot({
    required this.healthLabel,
    required this.providerLabel,
    required this.agentLabel,
  });

  final String healthLabel;
  final String providerLabel;
  final String agentLabel;

  static Future<_SystemSnapshot> load(ResearchOSApiClient apiClient) async {
    var health = 'Unavailable';
    var provider = 'Unavailable';
    var agents = 'Unavailable';

    try {
      final value = await apiClient.getHealth();
      final status = (value['status'] ??
              (value['healthy'] == true ? 'healthy' : ''))
          .toString();
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

    return _SystemSnapshot(
      healthLabel: health,
      providerLabel: provider,
      agentLabel: agents,
    );
  }
}
