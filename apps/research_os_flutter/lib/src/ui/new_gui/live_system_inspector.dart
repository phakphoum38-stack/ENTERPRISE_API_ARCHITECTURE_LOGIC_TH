import 'package:flutter/material.dart';

import '../../api/research_os_api_client.dart';

class ResearchLiveSystemInspector extends StatefulWidget {
  const ResearchLiveSystemInspector({required this.apiClient, super.key});

  final ResearchOSApiClient apiClient;

  @override
  State<ResearchLiveSystemInspector> createState() =>
      _ResearchLiveSystemInspectorState();
}

class _ResearchLiveSystemInspectorState
    extends State<ResearchLiveSystemInspector> {
  late Future<_LiveSystemSnapshot> _future;

  @override
  void initState() {
    super.initState();
    _future = _LiveSystemSnapshot.load(widget.apiClient);
  }

  void _refresh() {
    setState(() => _future = _LiveSystemSnapshot.load(widget.apiClient));
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      key: const Key('new-gui-system-inspector'),
      width: 300,
      color: const Color(0xFF0B1220),
      padding: const EdgeInsets.fromLTRB(14, 14, 14, 12),
      child: FutureBuilder<_LiveSystemSnapshot>(
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
                    key: const Key('new-gui-inspector-refresh'),
                    tooltip: 'Refresh live status',
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
              _LiveCard(
                title: 'Local Service',
                value: data?.health ?? 'Checking…',
                icon: Icons.dns_outlined,
              ),
              const SizedBox(height: 9),
              _LiveCard(
                title: 'Provider',
                value: data?.provider ?? 'Checking…',
                icon: Icons.hub_outlined,
              ),
              const SizedBox(height: 9),
              _LiveCard(
                title: 'Active Agents',
                value: data?.agents ?? 'Checking…',
                icon: Icons.smart_toy_outlined,
              ),
              const SizedBox(height: 9),
              _LiveCard(
                title: 'Skills & Tools',
                value: data?.skillsTools ?? 'Checking…',
                icon: Icons.extension_outlined,
              ),
              const SizedBox(height: 9),
              _LiveCard(
                title: 'Memory',
                value: data?.memory ?? 'Checking…',
                icon: Icons.memory_outlined,
              ),
              const SizedBox(height: 18),
              const Text(
                'Unified Master',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 9),
              Container(
                key: const Key('new-gui-unified-master-card'),
                padding: const EdgeInsets.all(13),
                decoration: BoxDecoration(
                  color: const Color(0xFF11192B),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: const Color(0xFF26344F)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      data?.scaleAuthority ?? 'Checking runtime…',
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      data?.helperRuntime ??
                          '6^6 logical scale remains bounded by the adaptive runtime.',
                      style: const TextStyle(
                        color: Color(0xFF8EA4C5),
                        fontSize: 11,
                        height: 1.35,
                      ),
                    ),
                  ],
                ),
              ),
              if (snapshot.hasError) ...<Widget>[
                const SizedBox(height: 10),
                Text(
                  snapshot.error.toString(),
                  style: const TextStyle(
                    color: Color(0xFFFF9AA5),
                    fontSize: 10,
                  ),
                ),
              ],
            ],
          );
        },
      ),
    );
  }
}

class _LiveCard extends StatelessWidget {
  const _LiveCard({
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

class _LiveSystemSnapshot {
  const _LiveSystemSnapshot({
    required this.health,
    required this.provider,
    required this.agents,
    required this.skillsTools,
    required this.memory,
    required this.scaleAuthority,
    required this.helperRuntime,
  });

  final String health;
  final String provider;
  final String agents;
  final String skillsTools;
  final String memory;
  final String scaleAuthority;
  final String helperRuntime;

  static Future<_LiveSystemSnapshot> load(ResearchOSApiClient apiClient) async {
    var health = 'Unavailable';
    var provider = 'Unavailable';
    var agents = 'Unavailable';
    var skills = 'Unavailable';
    var tools = 'Unavailable';
    var memory = 'Unavailable';
    var scaleAuthority = 'Adaptive runtime';
    var helperRuntime = '6^6 logical scale / bounded execution';

    try {
      final value = await apiClient.getHealth();
      final status = (value['status'] ?? '').toString().trim();
      final version = (value['version'] ?? '').toString().trim();
      health = status.isEmpty
          ? 'Connected'
          : version.isEmpty
              ? status
              : '$status • $version';
    } on Object {
      health = 'Offline / error';
    }

    try {
      final value = await apiClient.getProviders();
      final active = (value['active'] ?? value['provider'] ?? '').toString().trim();
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

    try {
      final value = await apiClient.getSkills();
      final raw = value['skills'];
      final count = value['count'];
      skills = count != null
          ? '$count'
          : raw is List
              ? '${raw.length}'
              : 'Connected';
    } on Object {
      skills = 'error';
    }

    try {
      final value = await apiClient.getTools();
      final raw = value['tools'];
      final count = value['count'];
      tools = count != null
          ? '$count'
          : raw is List
              ? '${raw.length}'
              : 'Connected';
    } on Object {
      tools = 'error';
    }

    try {
      final value = await apiClient.getFriendStatus();
      final persistence = (value['memory_persistence'] ?? '').toString().trim();
      final scope = (value['memory_scope'] ?? '').toString().trim();
      memory = <String>[
        if (persistence.isNotEmpty) persistence,
        if (scope.isNotEmpty) scope,
      ].join(' • ');
      if (memory.isEmpty) memory = 'Connected';

      final authority = (value['scale_authority'] ?? '').toString().trim();
      if (authority.isNotEmpty) scaleAuthority = authority;

      final helper = value['helper_scheduler'];
      if (helper is Map) {
        final maxWorkers = helper['max_active_workers'];
        final activation = (helper['activation'] ?? '').toString().trim();
        helperRuntime = <String>[
          if (activation.isNotEmpty) activation,
          if (maxWorkers != null) 'max active $maxWorkers',
        ].join(' • ');
        if (helperRuntime.isEmpty) {
          helperRuntime = '6^6 logical scale / bounded execution';
        }
      }
    } on Object {
      memory = 'Runtime status unavailable';
    }

    return _LiveSystemSnapshot(
      health: health,
      provider: provider,
      agents: agents,
      skillsTools: '$skills skills • $tools tools',
      memory: memory,
      scaleAuthority: scaleAuthority,
      helperRuntime: helperRuntime,
    );
  }
}
